"""Native PIQI reference-artifact bridge.

This module is deliberately separate from the original YAML-driven MVP evaluator.
It loads PIQI Alliance SAM metadata and Evaluation Rubrics without translating
those files into PIQITT's old profile schema.

The only PIQITT-owned configuration is the FHIR -> PIQI model binding file.
That boundary is intentional:

    FHIR Bundle -> PIQITT binding adapter -> PAT_CLINICAL_V1 entity
                -> official Evaluation Rubric -> official SAM metadata

The evaluator below is a bridge, not a claim of full PIQI conformance. SAMs for
which PIQITT does not yet have faithful execution semantics return UNSUPPORTED
instead of silently passing, failing, or being replaced with a home-grown test.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
import argparse
import json


PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"
UNSUPPORTED = "UNSUPPORTED"
UNBOUND = "UNBOUND"


@dataclass(frozen=True)
class ReferenceSAM:
    mnemonic: str
    name: str
    input_type: Optional[str]
    dimension: Optional[str]
    prerequisite: Optional[str]
    conditional: Optional[str]
    execution_type: Optional[str]
    parameters: Tuple[Dict[str, Any], ...]


@dataclass(frozen=True)
class ReferenceCriterion:
    sequence: int
    entity: str
    sam: str
    conditional_sam: Optional[str]
    effect: str
    weight: float
    critical: bool
    sam_parameters: Tuple[Dict[str, Any], ...]
    conditional_parameters: Tuple[Dict[str, Any], ...]
    sam_name: Optional[str]
    failure_name: Optional[str]


@dataclass(frozen=True)
class EntityBinding:
    entity: str
    resource: str
    paths: Tuple[str, ...]
    selector: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------


def load_reference_sams(path: str | Path) -> Dict[str, ReferenceSAM]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out: Dict[str, ReferenceSAM] = {}
    for item in data.get("SAMLibrary", []):
        sam = ReferenceSAM(
            mnemonic=item["mnemonic"],
            name=item.get("name") or item["mnemonic"],
            input_type=item.get("inputType"),
            dimension=item.get("HDQTDimensionMnemonic"),
            prerequisite=item.get("prerequisiteSAMMnemonic"),
            conditional=item.get("conditionalSAMMnemonic"),
            execution_type=item.get("executionTypeMnemonic"),
            parameters=tuple(item.get("parameters") or []),
        )
        out[sam.mnemonic] = sam
    return out


def load_reference_rubric(path: str | Path) -> Tuple[Dict[str, Any], List[ReferenceCriterion]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    criteria: List[ReferenceCriterion] = []
    for item in data.get("criteria", []):
        criteria.append(
            ReferenceCriterion(
                sequence=int(item.get("sequence", 0)),
                entity=item["entity"],
                sam=item["samMnemonic"],
                conditional_sam=item.get("conditionalSam"),
                effect=item.get("scoringEffect", "Scoring"),
                weight=float(item.get("scoringWeight", 1)),
                critical=bool(item.get("criticalityIndicator", False)),
                sam_parameters=tuple(item.get("samParameters") or []),
                conditional_parameters=tuple(item.get("conditionalSamParameters") or []),
                sam_name=item.get("samNameOverride"),
                failure_name=item.get("failureNameOverride"),
            )
        )
    return data, criteria


def load_bindings(path: str | Path) -> Tuple[Dict[str, Any], Dict[str, EntityBinding]]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out: Dict[str, EntityBinding] = {}
    for item in data.get("bindings", []):
        binding = EntityBinding(
            entity=item["entity"],
            resource=item["resource"],
            paths=tuple(item.get("paths") or []),
            selector=item.get("selector"),
        )
        out[binding.entity] = binding
    return data, out


# ---------------------------------------------------------------------------
# Dependency / coverage inspection
# ---------------------------------------------------------------------------


def sam_dependency_closure(
    sams: Dict[str, ReferenceSAM],
    roots: Iterable[str],
) -> Set[str]:
    """Return prerequisite + conditional closure for the requested SAM roots."""
    seen: Set[str] = set()
    stack = [r for r in roots if r]
    while stack:
        mnemonic = stack.pop()
        if mnemonic in seen:
            continue
        seen.add(mnemonic)
        sam = sams.get(mnemonic)
        if not sam:
            continue
        if sam.prerequisite:
            stack.append(sam.prerequisite)
        if sam.conditional:
            stack.append(sam.conditional)
    return seen


# SAMs we currently execute with local, deterministic semantics.
# Anything else is surfaced as UNSUPPORTED instead of being approximated.
LOCAL_IMPLEMENTATIONS: Set[str] = {
    "ATTR_ISPOPULATED",
    "ATTR_ISDATE",
    "ATTR_ISPASTDATE",
    "ATTR_ISNUMERIC",
    "ATTR_ISCODED",
    "ATTRIBUTE_INDICATOR_IS_TRUE",
    "CONCEPT_HASDISPLAY",
    "CONCEPT_HASCODE",
    "CONCEPT_HASCODESYSTEM",
    "CONCEPT_ISCOMPLETE",
    "OBSERVATIONVALUE_ISQUALITATIVE",
}


def sam_is_locally_executable(
    mnemonic: str,
    sams: Dict[str, ReferenceSAM],
    _seen: Optional[Set[str]] = None,
) -> bool:
    """True only when the SAM and its metadata dependencies are implemented."""
    if mnemonic not in LOCAL_IMPLEMENTATIONS:
        return False
    sam = sams.get(mnemonic)
    if not sam:
        return False
    seen = set(_seen or set())
    if mnemonic in seen:
        return True
    seen.add(mnemonic)
    for dep in (sam.prerequisite, sam.conditional):
        if dep and not sam_is_locally_executable(dep, sams, seen):
            return False
    return True


# ---------------------------------------------------------------------------
# FHIR extraction adapter
# ---------------------------------------------------------------------------


def _deep_get(obj: Any, path: str) -> List[Any]:
    """Small JSONPath-ish extractor; `*` expands arrays at that path segment."""
    if not path:
        return []
    current: List[Any] = [obj]
    for part in path.split("."):
        star = part.endswith("*")
        key = part[:-1] if star else part
        nxt: List[Any] = []
        for node in current:
            if isinstance(node, dict) and key in node:
                val = node[key]
                if star and isinstance(val, list):
                    nxt.extend(val)
                else:
                    nxt.append(val)
            elif isinstance(node, list):
                for item in node:
                    if isinstance(item, dict) and key in item:
                        val = item[key]
                        if star and isinstance(val, list):
                            nxt.extend(val)
                        else:
                            nxt.append(val)
        current = nxt
    return current


def _choice_values(resource: Dict[str, Any], stem: str) -> List[Any]:
    """Extract FHIR choice values such as value[x]."""
    prefix = stem[:-3] if stem.endswith("[x]") else stem
    return [value for key, value in resource.items() if key.startswith(prefix) and key != prefix]


def extract_binding_values(resource: Dict[str, Any], binding: EntityBinding) -> List[Any]:
    values: List[Any] = []
    for path in binding.paths:
        if path.endswith("[x]"):
            values.extend(_choice_values(resource, path))
        else:
            values.extend(_deep_get(resource, path))
    return values


def resource_matches_selector(resource: Dict[str, Any], selector: Optional[Dict[str, Any]]) -> bool:
    if not selector:
        return True
    values = _deep_get(resource, selector.get("path", ""))
    allowed = {str(v).lower() for v in (selector.get("equalsAny") or [])}
    return any(str(v).lower() in allowed for v in values)


# ---------------------------------------------------------------------------
# Primitive SAM execution
# ---------------------------------------------------------------------------


def _populated(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict)):
        return bool(value)
    return True


def _parse_fhir_date(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        if len(text) == 10:
            d = date.fromisoformat(text)
            return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _codings(value: Any) -> List[Dict[str, Any]]:
    if not isinstance(value, dict):
        return []
    if isinstance(value.get("coding"), list):
        return [c for c in value["coding"] if isinstance(c, dict)]
    if any(k in value for k in ("code", "system", "display")):
        return [value]
    return []


def _run_local_primitive(mnemonic: str, value: Any, params: Dict[str, Any], now: datetime) -> str:
    if mnemonic == "ATTR_ISPOPULATED":
        return PASS if _populated(value) else FAIL

    if mnemonic == "ATTR_ISDATE":
        if not _populated(value):
            return SKIP
        return PASS if _parse_fhir_date(value) is not None else FAIL

    if mnemonic == "ATTR_ISPASTDATE":
        if not _populated(value):
            return SKIP
        dt = _parse_fhir_date(value)
        if dt is None:
            return FAIL
        return PASS if dt <= now else FAIL

    if mnemonic == "ATTR_ISNUMERIC":
        if not _populated(value):
            return SKIP
        try:
            float(value)
            return PASS
        except (TypeError, ValueError):
            return FAIL

    if mnemonic == "ATTR_ISCODED":
        if not _populated(value):
            return SKIP
        return PASS if _codings(value) else FAIL

    if mnemonic == "ATTRIBUTE_INDICATOR_IS_TRUE":
        if value is None:
            return SKIP
        return PASS if value is True else FAIL

    if mnemonic == "CONCEPT_HASDISPLAY":
        codings = _codings(value)
        if not codings:
            return FAIL
        return PASS if any(_populated(c.get("display")) for c in codings) else FAIL

    if mnemonic == "CONCEPT_HASCODE":
        codings = _codings(value)
        if not codings:
            return FAIL
        return PASS if any(_populated(c.get("code")) for c in codings) else FAIL

    if mnemonic == "CONCEPT_HASCODESYSTEM":
        codings = _codings(value)
        if not codings:
            return FAIL
        return PASS if any(_populated(c.get("system")) for c in codings) else FAIL

    if mnemonic == "CONCEPT_ISCOMPLETE":
        codings = _codings(value)
        if not codings:
            return FAIL
        return PASS if any(
            _populated(c.get("code")) and _populated(c.get("system")) and _populated(c.get("display"))
            for c in codings
        ) else FAIL

    if mnemonic == "OBSERVATIONVALUE_ISQUALITATIVE":
        if not _populated(value):
            return SKIP
        # PIQI's exact accepted attribute list is model-aware. For the bridge we
        # only claim support for obvious qualitative FHIR representations.
        if isinstance(value, str):
            return PASS
        if isinstance(value, dict) and ("coding" in value or "text" in value):
            return PASS
        return FAIL

    return UNSUPPORTED


def run_sam(
    mnemonic: str,
    value: Any,
    params: Dict[str, Any],
    sams: Dict[str, ReferenceSAM],
    now: datetime,
    _stack: Optional[Set[str]] = None,
) -> str:
    sam = sams.get(mnemonic)
    if not sam or mnemonic not in LOCAL_IMPLEMENTATIONS:
        return UNSUPPORTED

    stack = set(_stack or set())
    if mnemonic in stack:
        return UNSUPPORTED
    stack.add(mnemonic)

    if sam.conditional:
        status = run_sam(sam.conditional, value, {}, sams, now, stack)
        if status == UNSUPPORTED:
            return UNSUPPORTED
        if status != PASS:
            return SKIP

    if sam.prerequisite:
        status = run_sam(sam.prerequisite, value, {}, sams, now, stack)
        if status == UNSUPPORTED:
            return UNSUPPORTED
        if status != PASS:
            return status

    return _run_local_primitive(mnemonic, value, params, now)


def criterion_params(items: Tuple[Dict[str, Any], ...]) -> Dict[str, Any]:
    return {
        str(item.get("samParameterMnemonic")): item.get("parameterValue")
        for item in items
        if item.get("samParameterMnemonic")
    }


# ---------------------------------------------------------------------------
# Bridge evaluator
# ---------------------------------------------------------------------------


class PIQIReferenceBridge:
    def __init__(
        self,
        sam_library_path: str | Path,
        rubric_path: str | Path,
        bindings_path: str | Path,
        now: Optional[datetime] = None,
    ) -> None:
        self.sams = load_reference_sams(sam_library_path)
        self.rubric_meta, self.criteria = load_reference_rubric(rubric_path)
        self.binding_meta, self.bindings = load_bindings(bindings_path)
        self.now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

        rubric_model = (self.rubric_meta.get("model") or {}).get("mnemonic")
        binding_model = self.binding_meta.get("modelMnemonic")
        if rubric_model and binding_model and rubric_model != binding_model:
            raise ValueError(f"Rubric model {rubric_model} does not match binding model {binding_model}")

    def coverage(self) -> Dict[str, Any]:
        direct_sams = {c.sam for c in self.criteria}
        conditional_sams = {c.conditional_sam for c in self.criteria if c.conditional_sam}
        closure = sam_dependency_closure(self.sams, direct_sams | conditional_sams)
        missing_sams = sorted(m for m in closure if m not in self.sams)

        bound = [c for c in self.criteria if c.entity in self.bindings]
        unbound = [c for c in self.criteria if c.entity not in self.bindings]
        executable = [
            c for c in bound
            if sam_is_locally_executable(c.sam, self.sams)
            and (not c.conditional_sam or sam_is_locally_executable(c.conditional_sam, self.sams))
        ]

        return {
            "rubric": self.rubric_meta.get("mnemonic"),
            "rubricName": self.rubric_meta.get("name"),
            "model": (self.rubric_meta.get("model") or {}).get("mnemonic"),
            "criteria": len(self.criteria),
            "boundCriteria": len(bound),
            "unboundCriteria": len(unbound),
            "locallyExecutableCriteria": len(executable),
            "samDependencyClosure": sorted(closure),
            "missingSamDefinitions": missing_sams,
            "unboundEntities": sorted({c.entity for c in unbound}),
            "unsupportedSams": sorted({
                c.sam for c in bound if not sam_is_locally_executable(c.sam, self.sams)
            }),
        }

    def evaluate_bundle(self, bundle: Dict[str, Any]) -> Dict[str, Any]:
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for entry in bundle.get("entry") or []:
            resource = entry.get("resource") or {}
            by_type.setdefault(resource.get("resourceType", "Unknown"), []).append(resource)

        results: List[Dict[str, Any]] = []
        numerator = 0.0
        denominator = 0.0
        weighted_num = 0.0
        weighted_den = 0.0
        critical_fails = 0

        for criterion in self.criteria:
            binding = self.bindings.get(criterion.entity)
            if not binding:
                results.append(self._result_row(criterion, UNBOUND, None, None, "No FHIR binding"))
                continue

            resources = [
                r for r in by_type.get(binding.resource, [])
                if resource_matches_selector(r, binding.selector)
            ]
            if not resources:
                results.append(self._result_row(criterion, SKIP, None, None, "No matching resource"))
                continue

            for resource in resources:
                values = extract_binding_values(resource, binding) or [None]
                for value in values:
                    if criterion.conditional_sam:
                        cond = run_sam(
                            criterion.conditional_sam,
                            value,
                            criterion_params(criterion.conditional_parameters),
                            self.sams,
                            self.now,
                        )
                        if cond == UNSUPPORTED:
                            results.append(self._result_row(criterion, UNSUPPORTED, resource, value, "Conditional SAM unsupported"))
                            continue
                        if cond != PASS:
                            results.append(self._result_row(criterion, SKIP, resource, value, "Criterion condition not met"))
                            continue

                    status = run_sam(
                        criterion.sam,
                        value,
                        criterion_params(criterion.sam_parameters),
                        self.sams,
                        self.now,
                    )
                    results.append(self._result_row(criterion, status, resource, value, None))

                    if criterion.effect != "Scoring" or status not in {PASS, FAIL}:
                        continue
                    denominator += 1
                    weighted_den += criterion.weight
                    if status == PASS:
                        numerator += 1
                        weighted_num += criterion.weight
                    elif criterion.critical:
                        critical_fails += 1

        return {
            "rubric": self.rubric_meta.get("mnemonic"),
            "rubricName": self.rubric_meta.get("name"),
            "model": (self.rubric_meta.get("model") or {}).get("mnemonic"),
            "bridgeStatus": "experimental",
            "piqiIndex": round(100 * numerator / denominator, 2) if denominator else None,
            "piqiWeightedIndex": round(100 * weighted_num / weighted_den, 2) if weighted_den else None,
            "numerator": int(numerator),
            "denominator": int(denominator),
            "weightedNumerator": weighted_num,
            "weightedDenominator": weighted_den,
            "criticalFailureCount": critical_fails,
            "coverage": self.coverage(),
            "details": results,
        }

    def _result_row(
        self,
        criterion: ReferenceCriterion,
        status: str,
        resource: Optional[Dict[str, Any]],
        value: Any,
        note: Optional[str],
    ) -> Dict[str, Any]:
        sam = self.sams.get(criterion.sam)
        return {
            "sequence": criterion.sequence,
            "entity": criterion.entity,
            "sam": criterion.sam,
            "samName": criterion.sam_name or (sam.name if sam else None),
            "failureName": criterion.failure_name,
            "status": status,
            "effect": criterion.effect,
            "weight": criterion.weight,
            "critical": criterion.critical,
            "dimension": sam.dimension if sam else None,
            "resourceType": resource.get("resourceType") if resource else None,
            "resourceId": resource.get("id") if resource else None,
            "value": value,
            "note": note,
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _default_paths() -> Tuple[Path, Path, Path]:
    root = Path(__file__).resolve().parent.parent
    ref = root / "reference" / "piqi"
    return (
        ref / "SAMs_USCDI_V2_V3.json",
        ref / "USCDI_V2.json",
        ref / "fhir_bindings_v0.json",
    )


def main() -> None:
    default_sams, default_rubric, default_bindings = _default_paths()
    parser = argparse.ArgumentParser(description="Inspect or run PIQI official-reference bridge")
    parser.add_argument("--sams", default=str(default_sams))
    parser.add_argument("--rubric", default=str(default_rubric))
    parser.add_argument("--bindings", default=str(default_bindings))
    parser.add_argument("--bundle", help="FHIR Bundle JSON; omit to print coverage only")
    args = parser.parse_args()

    bridge = PIQIReferenceBridge(args.sams, args.rubric, args.bindings)
    if not args.bundle:
        print(json.dumps(bridge.coverage(), indent=2))
        return

    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    print(json.dumps(bridge.evaluate_bundle(bundle), indent=2, default=str))


if __name__ == "__main__":
    main()
