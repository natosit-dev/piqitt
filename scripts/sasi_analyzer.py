from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import yaml

try:
    from scripts import fhir_convert_backend as fhir
    from scripts.sasi_sams import SAM_DISPATCH, SKIP, normalize_code_system, normalize_text
except ImportError:
    import fhir_convert_backend as fhir  # type: ignore
    from sasi_sams import SAM_DISPATCH, SKIP, normalize_code_system, normalize_text  # type: ignore


@dataclass
class SasiStep:
    id: str
    sam: str
    source_path: Optional[str] = None
    target_path: Optional[str] = None
    params: Optional[Dict[str, Any]] = None


def _coding_from_ce(value: str) -> Dict[str, Any]:
    return {
        "code": fhir.comp(value, 1),
        "display": fhir.comp(value, 2),
        "system": fhir.comp(value, 3),
    }


def _source_unit(units: str) -> Optional[str]:
    if not units:
        return None
    if "^" in units:
        return fhir.comp(units, 2) or fhir.comp(units, 1) or None
    return units


def build_source_inventory(raw_hl7: str) -> Dict[str, Any]:
    """Describe the source message using the parser PIQITT already trusts."""
    parsed = fhir.parse_hl7(raw_hl7)
    msg_type = fhir.detect_message_type(parsed)
    segment_counts = Counter(seg for seg, _ in parsed.get("_order", []))

    patient = None
    if parsed.get("PID"):
        fields = parsed["PID"][0]["_fields"]
        pid3 = fhir.get_field(fields, 3)
        patient = {
            "identifiers": [
                {
                    "value": fhir.comp(rep, 1),
                    "assigner": fhir.comp(rep, 4),
                }
                for rep in fhir.reps(pid3)
                if fhir.comp(rep, 1)
            ],
            "family": fhir.comp(fhir.get_field(fields, 5), 1),
            "given": fhir.comp(fhir.get_field(fields, 5), 2),
            "birthDate": fhir.get_field(fields, 7),
            "sex": fhir.get_field(fields, 8),
        }

    encounter = None
    if parsed.get("PV1"):
        fields = parsed["PV1"][0]["_fields"]
        location = fhir.get_field(fields, 3)
        encounter = {
            "class": fhir.get_field(fields, 2),
            "location": {
                "pointOfCare": fhir.comp(location, 1),
                "room": fhir.comp(location, 2),
                "bed": fhir.comp(location, 3),
                "facility": fhir.comp(location, 4),
            },
        }

    observations: List[Dict[str, Any]] = []
    for entry in parsed.get("OBX", []):
        fields = entry["_fields"]
        value_type = fhir.get_field(fields, 2).upper()
        raw_value = fhir.get_field(fields, 5)
        rec: Dict[str, Any] = {
            "setId": fhir.get_field(fields, 1),
            "valueType": value_type,
            "code": _coding_from_ce(fhir.get_field(fields, 3)),
            "value": raw_value,
            "unit": _source_unit(fhir.get_field(fields, 6)),
            "effectiveTime": fhir.get_field(fields, 14),
        }
        if value_type in {"CE", "CWE", "CNE"}:
            rec["valueCoding"] = _coding_from_ce(raw_value)
        observations.append(rec)

    transactions: List[Dict[str, Any]] = []
    for entry in parsed.get("FT1", []):
        fields = entry["_fields"]
        transactions.append(
            {
                "date": fhir.get_field(fields, 4),
                "code": fhir.get_field(fields, 6),
                "description": fhir.get_field(fields, 7),
                "amount": fhir.get_field(fields, 10),
            }
        )

    orders = []
    for entry in parsed.get("OBR", []):
        fields = entry["_fields"]
        orders.append(
            {
                "placer": fhir.get_field(fields, 2),
                "filler": fhir.get_field(fields, 3),
                "service": _coding_from_ce(fhir.get_field(fields, 4)),
            }
        )

    return {
        "messageType": msg_type,
        "segmentCounts": dict(segment_counts),
        "patient": patient,
        "encounter": encounter,
        "observations": observations,
        "transactions": transactions,
        "orders": orders,
    }


def _walk_references(node: Any) -> Iterable[str]:
    if isinstance(node, dict):
        ref = node.get("reference")
        if isinstance(ref, str) and ref:
            yield ref
        for value in node.values():
            yield from _walk_references(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_references(value)


def build_target_inventory(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Describe the FHIR representation PIQITT produced."""
    resources = [
        (entry or {}).get("resource") or {}
        for entry in (bundle.get("entry") or [])
        if isinstance(entry, dict)
    ]
    by_type: Dict[str, List[Dict[str, Any]]] = {}
    keys: List[str] = []
    for resource in resources:
        rtype = resource.get("resourceType") or "Unknown"
        by_type.setdefault(rtype, []).append(resource)
        if resource.get("resourceType") and resource.get("id"):
            keys.append(f"{resource['resourceType']}/{resource['id']}")

    return {
        "resourceCounts": {key: len(value) for key, value in by_type.items()},
        "patients": by_type.get("Patient", []),
        "encounters": by_type.get("Encounter", []),
        "observations": by_type.get("Observation", []),
        "claims": by_type.get("Claim", []),
        "diagnosticReports": by_type.get("DiagnosticReport", []),
        "messageHeaders": by_type.get("MessageHeader", []),
        "references": list(_walk_references(bundle)),
        "resourceKeys": keys,
    }


def _coded_observation_distribution_source(source: Dict[str, Any]) -> Dict[str, int]:
    counter: Counter[str] = Counter()
    for obs in source.get("observations") or []:
        code = obs.get("code") or {}
        key = f"{normalize_code_system(code.get('system')) or '(none)'}|{normalize_text(code.get('code')) or '(blank)'}"
        counter[key] += 1
    return dict(counter)


def _coded_observation_distribution_target(target: Dict[str, Any]) -> Dict[str, int]:
    counter: Counter[str] = Counter()
    for obs in target.get("observations") or []:
        codings = ((obs.get("code") or {}).get("coding") or [])
        coding = codings[0] if codings else {}
        key = f"{normalize_code_system(coding.get('system')) or '(none)'}|{normalize_text(coding.get('code')) or '(blank)'}"
        counter[key] += 1
    return dict(counter)


def _coded_value_distribution_source(source: Dict[str, Any]) -> Dict[str, int]:
    counter: Counter[str] = Counter()
    for obs in source.get("observations") or []:
        value_type = (obs.get("valueType") or "").upper()
        if value_type not in {"CE", "CWE", "CNE"}:
            continue
        obs_code = obs.get("code") or {}
        val = obs.get("valueCoding") or {}
        key = "|".join([
            normalize_code_system(obs_code.get("system")) or "(none)",
            normalize_text(obs_code.get("code")) or "(blank)",
            normalize_code_system(val.get("system")) or "(none)",
            normalize_text(val.get("code")) or "(blank)",
        ])
        counter[key] += 1
    return dict(counter)


def _coded_value_distribution_target(target: Dict[str, Any]) -> Dict[str, int]:
    counter: Counter[str] = Counter()
    for obs in target.get("observations") or []:
        values = ((obs.get("valueCodeableConcept") or {}).get("coding") or [])
        if not values:
            continue
        codes = ((obs.get("code") or {}).get("coding") or [])
        obs_code = codes[0] if codes else {}
        val = values[0]
        key = "|".join([
            normalize_code_system(obs_code.get("system")) or "(none)",
            normalize_text(obs_code.get("code")) or "(blank)",
            normalize_code_system(val.get("system")) or "(none)",
            normalize_text(val.get("code")) or "(blank)",
        ])
        counter[key] += 1
    return dict(counter)


def build_statistics(source: Dict[str, Any], target: Dict[str, Any]) -> Dict[str, Any]:
    """Small per-message statistical payload that can be aggregated later."""
    src_patient = source.get("patient") or {}
    target_patients = target.get("patients") or []
    tgt_gender = target_patients[0].get("gender") if target_patients else None
    return {
        "source": {
            "messageType": source.get("messageType"),
            "patientSex": src_patient.get("sex"),
            "observationCodes": _coded_observation_distribution_source(source),
            "codedObservationValues": _coded_value_distribution_source(source),
            "segmentCounts": source.get("segmentCounts") or {},
        },
        "target": {
            "patientGender": tgt_gender,
            "observationCodes": _coded_observation_distribution_target(target),
            "codedObservationValues": _coded_value_distribution_target(target),
            "resourceCounts": target.get("resourceCounts") or {},
        },
    }


class SaSIAnalyzer:
    """Structural and Statistical Integrity analyzer for one HL7 -> FHIR transformation."""

    def __init__(self, sam_library_path: str, profile_path: str):
        self.sam_defs = self._load_sam_library(sam_library_path)
        self.profile_name, self.steps = self._load_profile(profile_path)

    @staticmethod
    def _load_sam_library(path: str) -> Dict[str, Dict[str, Any]]:
        doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return {item["mnemonic"]: item for item in doc.get("sams", [])}

    @staticmethod
    def _load_profile(path: str) -> tuple[str, List[SasiStep]]:
        doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        profile = doc.get("profile") or {}
        steps = [
            SasiStep(
                id=step["id"],
                sam=step["sam"],
                source_path=step.get("source_path"),
                target_path=step.get("target_path"),
                params=step.get("params") or {},
            )
            for step in profile.get("steps", [])
        ]
        return profile.get("name", "SaSI"), steps

    def evaluate(
        self,
        raw_hl7: str,
        bundle: Dict[str, Any],
        message_type: Optional[str] = None,
        source_file: Optional[str] = None,
        source_index: Optional[int] = None,
        include_inventories: bool = False,
    ) -> Dict[str, Any]:
        source = build_source_inventory(raw_hl7)
        target = build_target_inventory(bundle)
        if message_type:
            source["messageType"] = message_type

        details: List[Dict[str, Any]] = []
        passes = fails = skips = 0

        for step in self.steps:
            sam_def = self.sam_defs.get(step.sam) or {}
            fn = SAM_DISPATCH.get(step.sam)
            if fn is None:
                status = SKIP
                outcome_dict = {
                    "status": SKIP,
                    "meaning": f"No SaSI implementation is registered for {step.sam}.",
                }
            else:
                outcome_dict = fn(source, target, **(step.params or {})).to_dict()
                status = outcome_dict["status"]

            if status == "PASS":
                passes += 1
            elif status == "FAIL":
                fails += 1
            else:
                skips += 1

            detail = {
                "stepId": step.id,
                "sam": step.sam,
                "dimension": sam_def.get("dimension"),
                "status": status,
                "sourcePath": step.source_path,
                "targetPath": step.target_path,
                "description": sam_def.get("description"),
                "sourceValue": outcome_dict.get("source_value"),
                "targetValue": outcome_dict.get("target_value"),
                "meaning": outcome_dict.get("meaning"),
            }
            if outcome_dict.get("evidence") is not None:
                detail["evidence"] = outcome_dict["evidence"]
            details.append(detail)

        result: Dict[str, Any] = {
            "profile": self.profile_name,
            "messageType": source.get("messageType"),
            "sourceFile": source_file,
            "sourceIndex": source_index,
            "evaluations": len(self.steps),
            "passes": passes,
            "fails": fails,
            "skips": skips,
            "details": details,
            "statistics": build_statistics(source, target),
        }
        if include_inventories:
            result["sourceInventory"] = source
            result["targetInventory"] = target
        return result
