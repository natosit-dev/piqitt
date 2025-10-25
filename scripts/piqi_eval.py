# piqi_eval.py
"""
PIQI Evaluator (MVP)
- Loads a YAML SAM library and one or more Evaluation Profiles
- Applies SAMs to FHIR Bundles (Patient-centric) and computes scores
- Returns message-level results + drill-downs you can aggregate per patient or facility

Scoring model (unweighted default):
- For each configured assessment step we increment denominator by 1.
- If the SAM returns PASS -> numerator += 1
- If the SAM returns SKIP/INDETERMINATE -> denominator += 0 (excluded)
- PIQI Index = 100 * numerator/denominator  (safe-divide)

Entity & mapping:
- We evaluate FHIR resources present in your bundle (Patient, Observation, Claim, etc.)
- Profiles declare which resource paths and attributes to test.

Extend by:
- Adding SAM functions below
- Adding more profile steps in YAML
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable, Tuple, Set
import json
import math
import re
import yaml
from pathlib import Path
import os

# ----------------------------
# Types
# ----------------------------

Result = Dict[str, Any]

@dataclass
class SamSpec:
    mnemonic: str
    dimension: str               # e.g., "Availability.Unpopulated"
    entity_type: str             # "SimpleAttribute" | "CodableConcept" | "ObservationValue" | "RangeValue"
    prereq: Optional[str] = None # optional prerequisite SAM mnemonic
    exec_type: str = "Primitive_Logic"  # future: Regex, REST, Stored_Procedure
    params_schema: Optional[Dict[str, Any]] = None

@dataclass
class StepSpec:
    id: str
    resource: str               # e.g., "Patient" | "Observation"
    path: str                   # JSONPath-like (limited) e.g., "birthDate" or "code.coding"
    sam: str                    # SAM mnemonic
    params: Dict[str, Any]      # parameters passed to SAM
    effect: str = "Scoring"     # "Scoring" | "Informational"
    weight: float = 1.0
    critical: bool = False
    condition: Optional[Dict[str, Any]] = None  # optional conditional SAM (mnemonic + params)


# ----------------------------
# Utilities
# ----------------------------

def _deep_get(obj: Any, path: str) -> List[Any]:
    """
    Minimal JSONPath-ish getter supporting:
      - dot navigation: "code.coding"
      - list expansion with "*": "code.coding*.system"
      - root is the resource dict
    Returns a list of matches (so we can fan out on arrays).
    """
    if not path or obj is None:
        return []
    parts = path.split(".")
    current = [obj]
    for p in parts:
        nxt = []
        star = p.endswith("*")
        key = p[:-1] if star else p
        for node in current:
            if isinstance(node, dict) and key in node:
                val = node[key]
                if star and isinstance(val, list):
                    nxt.extend(val)
                else:
                    nxt.append(val)
            elif isinstance(node, list):
                # apply key to each list member
                for it in node:
                    if isinstance(it, dict) and key in it:
                        val = it[key]
                        if star and isinstance(val, list):
                            nxt.extend(val)
                        else:
                            nxt.append(val)
        current = nxt
    return current

def _safe_float(s: Any) -> Optional[float]:
    try:
        return float(s)
    except Exception:
        return None

def _loinc_like(system: str) -> bool:
    if not system:
        return False
    s = system.strip().lower()
    return s in {"loinc", "http://loinc.org", "urn:oid:2.16.840.1.113883.6.1", "ln"}

def _value_preview(value: Any, max_len: int = 120) -> Optional[str]:
    """
    Produce a concise human-readable preview for common FHIR shapes:
    - primitives -> str(value)
    - Coding -> "code|system (display)"
    - CodeableConcept -> first coding as above, else text
    - Quantity -> "value unit"
    - Range -> "low - high"
    - Observation.value[x] dicts (Quantity, String, CodeableConcept, DateTime)
    - Lists -> first 1-3 item previews joined by "; "
    Truncates to max_len.
    """
    def trunc(s: str) -> str:
        s = s.strip()
        return s if len(s) <= max_len else (s[: max_len - 3] + "...")

    if value is None:
        return None

    # Primitive
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return trunc(value)

    # Quantity-like
    if isinstance(value, dict) and "value" in value and ("unit" in value or "code" in value or "system" in value):
        v = value.get("value")
        u = value.get("unit") or value.get("code") or ""
        return trunc(f"{v} {u}".strip())

    # Coding
    if isinstance(value, dict) and {"code", "system"} & set(value.keys()):
        code = (value.get("code") or "").strip()
        system = (value.get("system") or "").strip()
        display = (value.get("display") or "").strip()
        base = f"{code}|{system}" if code or system else display
        return trunc(f"{base} ({display})" if display and base != display else base)

    # CodeableConcept
    if isinstance(value, dict) and "coding" in value:
        codings = value.get("coding") or []
        if codings and isinstance(codings[0], dict):
            return _value_preview(codings[0], max_len=max_len)
        text = value.get("text")
        return trunc(text) if text else None

    # Range / referenceRange variants
    if isinstance(value, dict) and ({"low", "high"} & set(value.keys()) or {"lowValue", "highValue"} & set(value.keys())):
        low = value.get("low") or value.get("lowValue")
        high = value.get("high") or value.get("highValue")
        # Quantity sub-objects
        def qv(q):
            if isinstance(q, dict):
                if "value" in q:
                    u = q.get("unit") or ""
                    return f"{q.get('value')} {u}".strip()
                return str(q)
            return str(q)
        if low is not None or high is not None:
            return trunc(f"{qv(low)} - {qv(high)}")

    # Observation.value[x] dicts (if passed directly)
    if isinstance(value, dict):
        # Try common keys in value[x]
        for k in ("valueString", "valueDateTime"):
            if k in value:
                return trunc(str(value[k]))
        if "valueQuantity" in value:
            return _value_preview(value["valueQuantity"], max_len=max_len)
        if "valueCodeableConcept" in value:
            return _value_preview(value["valueCodeableConcept"], max_len=max_len)

    # Lists: preview a few items
    if isinstance(value, list):
        parts = []
        for item in value[:3]:
            p = _value_preview(item, max_len=max_len // 3)
            if p:
                parts.append(p)
        return trunc("; ".join(parts)) if parts else None

    # Fallback
    try:
        import json
        s = json.dumps(value, ensure_ascii=False)
        return trunc(s)
    except Exception:
        return None
# --- Plausibility config loader ---
def load_plausibility_yaml(path: str | None = None) -> dict:
    """Load plausibility dictionary with keys {by_loinc, by_class}."""
    from pathlib import Path
    import yaml
    def_ref = _default_ref_dir()
    p = Path(path) if path else (def_ref / "plausibility.yaml")
    if not p.exists():
        return {"by_loinc": {}, "by_class": {}}
    data = yaml.safe_load(p.read_text()) or {}
    return {"by_loinc": data.get("by_loinc", {}), "by_class": data.get("by_class", {})}

def _obs_first_loinc(obs: dict) -> tuple[str | None, str | None]:
    """Return (loinc_code, display) from Observation.code.coding if present."""
    code = (obs.get("code") or {}).get("coding") or []
    for c in code:
        sys = (c.get("system") or "").lower()
        if "loinc" in sys or "2.16.840.1.113883.6.1" in sys:
            return c.get("code"), c.get("display")
    return None, None


def _obs_loinc_class_hint(obs: dict) -> str | None:
    # Stub for future use (e.g., if you stash LOINC class in an extension)
    return None

# ----------------------------
# SAM Implementations (MVP set)
# ----------------------------

class SAM:
    """Namespace for SAM functions. Return: 'PASS' | 'FAIL' | 'SKIP'."""
    @staticmethod
    def Attr_IsPopulated(value: Any, **kwargs) -> str:
        if value is None:
            return "FAIL"
        if isinstance(value, str) and value.strip() == "":
            return "FAIL"
        if isinstance(value, list) and len(value) == 0:
            return "FAIL"
        return "PASS"

    @staticmethod
    def Attr_IsNumeric(value: Any, **kwargs) -> str:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return "SKIP"
        return "PASS" if _safe_float(value) is not None else "FAIL"

    @staticmethod
    def Attr_IsDate(value: Any, **kwargs) -> str:
        # naive: YYYY-MM-DD
        if value is None or value == "":
            return "SKIP"
        return "PASS" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)) else "FAIL"

    @staticmethod
    def Concept_HasCode(value: Any, **kwargs) -> str:
        """
        value is expected to be a coding dict or a codableConcept dict.
        Supports both:
          - coding dict: {"system": "...", "code": "...", "display": "..."}
          - codable concept: {"coding":[...], "text":"..."}
        """
        if value is None:
            return "FAIL"
        if isinstance(value, dict) and "coding" in value:
            codings = value.get("coding") or []
            ok = any((c.get("code") or "").strip() for c in codings if isinstance(c, dict))
            return "PASS" if ok else "FAIL"
        if isinstance(value, dict):
            return "PASS" if (value.get("code") or "").strip() else "FAIL"
        return "SKIP"

    @staticmethod
    def Concept_IsValidMember(value: Any, value_sets: Dict[str, Set[str]] = None, **kwargs) -> str:
        """
        Validates that (system,code) is present in the provided value_set keyed by a system mnemonic.
        params:
           system: "LOINC" | "CPT" (maps to sets you loaded)
        Accepts either coding dicts or codableConcepts; passes if ANY coding matches.
        """
        if value_sets is None:
            value_sets = {}
        system_param = (kwargs.get("system") or "").upper()
        allowed = value_sets.get(system_param, set())

        def is_valid(coding: Dict[str, Any]) -> bool:
            code = (coding.get("code") or "").strip().upper()
            system = (coding.get("system") or "").strip()
            if system_param == "LOINC" and not _loinc_like(system):
                return False
            return code in allowed if code else False

        # codable concept
        if isinstance(value, dict) and "coding" in value:
            return "PASS" if any(is_valid(c) for c in (value.get("coding") or [])) else "FAIL"
        # coding dict
        if isinstance(value, dict):
            return "PASS" if is_valid(value) else "FAIL"
        return "SKIP"

    @staticmethod
    def ObservationValue_IsNumeric(value: Any, **kwargs) -> str:
        """Checks Observation.value[x] is numeric (for quantity/number use-cases)."""
        if value is None:
            return "SKIP"
        # support quantity dict: {"value": 3.1}
        if isinstance(value, dict) and "value" in value:
            return "PASS" if _safe_float(value["value"]) is not None else "FAIL"
        # raw string/number
        return "PASS" if _safe_float(value) is not None else "FAIL"

    @staticmethod
    def RangeValue_IsComplete(value: Any, **kwargs) -> str:
        """ReferenceRange dict: expects low/high present."""
        if not isinstance(value, dict):
            return "SKIP"
        low = value.get("low") or value.get("lowValue")
        high = value.get("high") or value.get("highValue")
        return "PASS" if (low is not None and high is not None) else "FAIL"

    @staticmethod
    def LabResult_ValueIsPlausible(obs: Dict[str, Any], **kwargs) -> str:
        """
        Minimal plausibility stub:
        - If Observation.code is LOINC numeric-type-ish AND valueQuantity is present -> value must be numeric
        - Real version would consult LOINC scale/type + unit ranges. Here we only sanity-check numeric.
        """
        code = obs.get("code") or {}
        codings = code.get("coding") or []
        loinc = any(_loinc_like(c.get("system", "")) for c in codings)
        if not loinc:
            return "SKIP"
        vq = obs.get("valueQuantity")
        if vq is None:
            # many LOINC are qualitative; don't fail hard here — mark as SKIP
            return "SKIP"
        return "PASS" if _safe_float(vq.get("value")) is not None else "FAIL"
    
    @staticmethod
    def Observation_UnitAllowed(obs: Dict[str, Any], **kwargs) -> str:
        """Check Observation.valueQuantity.unit is allowed for this LOINC (or class fallback)."""
        cfg = kwargs.get("plausibility_cfg") or {}
        vq = obs.get("valueQuantity")
        if not isinstance(vq, dict):
            return "SKIP"
        unit = (vq.get("unit") or "").strip()
        if not unit:
            return "FAIL"  # unit is required when checking
        loinc, _ = _obs_first_loinc(obs)
        by_loinc = (cfg.get("by_loinc") or {})
        by_class = (cfg.get("by_class") or {})
        if loinc and loinc in by_loinc:
            allowed = set(by_loinc[loinc].get("units") or [])
            return "PASS" if unit in allowed else "FAIL"
        loinc_class = _obs_loinc_class_hint(obs)
        if loinc_class and loinc_class in by_class:
            allowed = set(by_class[loinc_class].get("units") or [])
            return "PASS" if unit in allowed else "FAIL"
        return "SKIP"

    @staticmethod
    def Observation_ValueWithinRange(obs: Dict[str, Any], **kwargs) -> str:
        """Check Observation.valueQuantity.value is within plausibility bounds for LOINC (or class)."""
        cfg = kwargs.get("plausibility_cfg") or {}
        vq = obs.get("valueQuantity")
        if not isinstance(vq, dict) or "value" not in vq:
            return "SKIP"
        val = _safe_float(vq.get("value"))
        if val is None:
            return "FAIL"
        loinc, _ = _obs_first_loinc(obs)
        by_loinc = (cfg.get("by_loinc") or {})
        by_class = (cfg.get("by_class") or {})

        def in_range(rec: dict) -> bool:
            mn = rec.get("min"); mx = rec.get("max")
            try:
                if mn is not None and val < float(mn): return False
                if mx is not None and val > float(mx): return False
                return True
            except Exception:
                return False

        if loinc and loinc in by_loinc:
            return "PASS" if in_range(by_loinc[loinc]) else "FAIL"
        loinc_class = _obs_loinc_class_hint(obs)
        if loinc_class and loinc_class in by_class:
            return "PASS" if in_range(by_class[loinc_class]) else "FAIL"
        return "SKIP"



# ----------------------------
# Evaluator
# ----------------------------

class PIQIEvaluator:
    def __init__(
        self,
        sam_library_path: str,
        profile_paths: List[str],
        loinc_codes: Optional[Set[str]] = None,
        cpt_codes: Optional[Set[str]] = None,
        plausibility_cfg: Optional[Dict[str, Any]] = None,
    ):
        """
        loinc_codes: set of uppercased LOINC codes
        cpt_codes:   set of uppercased CPT codes
        """
        self.sam_defs: Dict[str, SamSpec] = self._load_sam_library(sam_library_path)
        self.plausibility_cfg = plausibility_cfg or {}
        self.profiles: Dict[str, List[StepSpec]] = self._load_profiles(profile_paths)
        self.value_sets: Dict[str, Set[str]] = {
            "LOINC": (loinc_codes or set()),
            "CPT": (cpt_codes or set()),
        }
        self.sam_dispatch: Dict[str, Callable[..., str]] = {
            "Attr_IsPopulated": SAM.Attr_IsPopulated,
            "Attr_IsNumeric": SAM.Attr_IsNumeric,
            "Attr_IsDate": SAM.Attr_IsDate,
            "Concept_HasCode": SAM.Concept_HasCode,
            "Concept_IsValidMember": lambda value, **p: SAM.Concept_IsValidMember(value, value_sets=self.value_sets, **p),
            "ObservationValue_IsNumeric": SAM.ObservationValue_IsNumeric,
            "RangeValue_IsComplete": SAM.RangeValue_IsComplete,
            "LabResult_ValueIsPlausible": SAM.LabResult_ValueIsPlausible,
            "Observation_UnitAllowed":  lambda value, **p: SAM.Observation_UnitAllowed(value, **p),
            "Observation_ValueWithinRange": lambda value, **p: SAM.Observation_ValueWithinRange(value, **p),
        
        }

    # ---------- loading ----------

    def _load_sam_library(self, path: str) -> Dict[str, SamSpec]:
        data = yaml.safe_load(Path(path).read_text())
        out: Dict[str, SamSpec] = {}
        for item in data.get("sams", []):
            out[item["mnemonic"]] = SamSpec(
                mnemonic=item["mnemonic"],
                dimension=item["dimension"],
                entity_type=item["entity_type"],
                prereq=item.get("prerequisite"),
                exec_type=item.get("exec_type", "Primitive_Logic"),
                params_schema=item.get("params_schema"),
            )
        return out

    def _load_profiles(self, paths: List[str]) -> Dict[str, List[StepSpec]]:
        profs: Dict[str, List[StepSpec]] = {}
        for p in paths:
            y = yaml.safe_load(Path(p).read_text())
            name = y["profile"]["name"]
            steps: List[StepSpec] = []
            for s in y["profile"]["steps"]:
                steps.append(
                    StepSpec(
                        id=s["id"],
                        resource=s["resource"],
                        path=s["path"],
                        sam=s["sam"],
                        params=s.get("params", {}),
                        effect=s.get("effect", "Scoring"),
                        weight=float(s.get("weight", 1.0)),
                        critical=bool(s.get("critical", False)),
                        condition=s.get("condition"),
                    )
                )
            profs[name] = steps
        return profs

    # ---------- evaluation ----------

    def evaluate_bundle(self, bundle: Dict[str, Any], profile_name: str) -> Result:
        steps = self.profiles.get(profile_name) or []
        entries = bundle.get("entry") or []
        by_type: Dict[str, List[Dict[str, Any]]] = {}
        for e in entries:
            r = e.get("resource") or {}
            by_type.setdefault(r.get("resourceType", "Unknown"), []).append(r)

        message_header = (by_type.get("MessageHeader") or [{}])[0]
        sending = (message_header.get("source") or {}).get("name")
        msg_id = message_header.get("id")

        numerator = 0.0
        denominator = 0.0
        weighted_num = 0.0
        weighted_den = 0.0
        critical_fails = 0
        details: List[Dict[str, Any]] = []

        for step in steps:
            resources = by_type.get(step.resource, [])
            if not resources:
                # No such resources in the bundle; treat each step as SKIP
                continue

            for res in resources:
                # Condition (optional)
                if step.condition:
                    cond_sam = step.condition.get("sam")
                    cond_params = step.condition.get("params", {})
                    cond_val = self._extract_value(res, step.path)
                    cond_status = self._run_sam(cond_sam, cond_val, res=res, params=cond_params)
                    if cond_status != "PASS":
                        continue  # do not score this step

                # Expand the path; for arrays, fan out
                values = self._extract_value(res, step.path)
                if not values:
                    values = [None]  # so Attr_IsPopulated can FAIL

                # Prerequisite handling on EACH value
                for v in values:
                    # Run prerequisite if declared
                    if (pr := self.sam_defs.get(step.sam).prereq) is not None:
                        prereq_status = self._run_sam(pr, v, res=res, params=step.params)
                        if prereq_status == "SKIP":
                            # excluded from scoring (no denominator bump)
                            continue
                        if prereq_status == "FAIL":
                            denominator += 1
                            weighted_den += step.weight
                            if step.effect == "Scoring":
                                # fail on prereq
                                details.append(self._mk_detail(step, res, v, pr, "FAIL"))
                                if step.critical:
                                    critical_fails += 1
                            continue  # don't run the assigned SAM

                    # Run assigned SAM
                    status = self._run_sam(step.sam, v, res=res, params=step.params)

                    if status == "SKIP":
                        details.append(self._mk_detail(step, res, v, step.sam, "SKIP"))
                        continue  # not scorable

                    denominator += 1
                    weighted_den += step.weight
                    if status == "PASS":
                        numerator += 1
                        weighted_num += step.weight
                    if step.effect == "Scoring":
                        details.append(self._mk_detail(step, res, v, step.sam, status))
                        if step.critical and status == "FAIL":
                            critical_fails += 1

        idx = 100.0 * numerator / denominator if denominator else None
        w_idx = 100.0 * weighted_num / weighted_den if weighted_den else None

        return {
            "messageId": msg_id,
            "sendingFacility": sending,
            "piqiIndex": round(idx, 2) if idx is not None else None,
            "piqiWeightedIndex": round(w_idx, 2) if w_idx is not None else None,
            "numerator": int(numerator),
            "denominator": int(denominator),
            "weightedNumerator": weighted_num,
            "weightedDenominator": weighted_den,
            "criticalFailureCount": critical_fails,
            "details": details,  # include the full SAM evaluations
        }


    def _mk_detail(self, step: StepSpec, res: Dict[str, Any], value: Any, sam: str, status: str) -> Dict[str, Any]:
        sam_def = self.sam_defs.get(sam, SamSpec(sam, "", ""))
        return {
            "stepId": step.id,
            "resourceType": res.get("resourceType"),
            "resourceId": res.get("id"),
            "path": step.path,
            "sam": sam,
            "status": status,  # PASS | FAIL | SKIP
            "dimension": sam_def.dimension,
            "mnemonic": sam_def.mnemonic,
            "entity_type": sam_def.entity_type,
            "prerequisite": sam_def.prereq,
            "params_schema": sam_def.params_schema,
            "severity": "critical" if step.critical else "standard",
            "values": value,
            "valuePreview": _value_preview(value),
        }


    def _extract_value(self, resource: Dict[str, Any], path: str) -> List[Any]:
        # Special-cases for common patterns
        # Example: Observation result value
        if resource.get("resourceType") == "Observation" and path == "value[x]":
            out = []
            for k in ["valueQuantity", "valueString", "valueCodeableConcept", "valueDateTime"]:
                if k in resource:
                    out.append(resource[k])
            return out or [None]
        return _deep_get(resource, path)

    def _run_sam(self, mnemonic: str, value: Any, res: Dict[str, Any], params: Dict[str, Any]) -> str:
        fn = self.sam_dispatch.get(mnemonic)
        if not fn:
            return "SKIP"
        if mnemonic in {"Observation_UnitAllowed", "Observation_ValueWithinRange"}:
            params = dict(params or {})
            params.setdefault("plausibility_cfg", self.plausibility_cfg)
            return fn(res, **params)  # these SAMs expect the full Observation
        return fn(value if "LabResult_ValueIsPlausible" not in mnemonic else res, **params)


# ----------------------------
# Helpers to load terminologies
# ----------------------------

def _default_ref_dir() -> Path:
    """
    Resolve the /ref directory from typical project layout:
    - /scripts/piqi_eval.py (this file)
    - /profiles/...
    - /ref/loinc.csv, /ref/cpt.csv

    Order of precedence:
    1) PIQI_REF_DIR env var (absolute or relative)
    2) ../ref relative to this file (…/scripts/ -> …/ref)
    3) ./ref relative to current working directory
    """
    env_dir = os.getenv("PIQI_REF_DIR")
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    here = Path(__file__).resolve()
    candidate = (here.parent.parent / "ref")  # ../ref from /scripts
    return candidate if candidate.exists() else Path.cwd() / "ref"


def load_loinc_codes_from_csv(path: str | None = None) -> set[str]:
    """
    Load LOINC codes. If 'path' is None, default to <ref_dir>/loinc.csv.
    Accepts CSV or TSV; tries to auto-detect delimiter and column name.
    """
    import csv
    if path is None:
        path = _default_ref_dir() / "loinc.csv"
    path = Path(path)
    codes: set[str] = set()
    with path.open(newline="", encoding="utf-8", errors="ignore") as f:
        sample = f.read(4096)
        f.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
        except Exception:
            dialect = csv.excel
        reader = csv.DictReader(f, dialect=dialect)
        # Common header candidates in LOINC distributions
        candidates = [c for c in (reader.fieldnames or []) if c and c.lower() in {"loinc_num", "loinc", "code"}]
        col = candidates[0] if candidates else (reader.fieldnames or [""])[0]
        for row in reader:
            code = (row.get(col) or "").strip().upper()
            if code:
                codes.add(code)
    return codes


def load_cpt_codes_from_csv(path: str | None = None) -> set[str]:
    """
    Load CPT codes. If 'path' is None, default to <ref_dir>/cpt.csv.
    Accepts CSV; tries common column names.
    """
    import csv
    if path is None:
        path = _default_ref_dir() / "cpt.csv"
    path = Path(path)
    codes: set[str] = set()
    with path.open(newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        candidates = [c for c in (reader.fieldnames or []) if c and c.lower() in {"code", "cpt", "cpt code", "cpt_code"}]
        col = candidates[0] if candidates else (reader.fieldnames or [""])[0]
        for row in reader:
            code = (row.get(col) or "").strip().upper()
            if code:
                codes.add(code)
    return codes

