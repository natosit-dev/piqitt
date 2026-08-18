from __future__ import annotations

from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Tuple
import re


PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"


@dataclass
class SamOutcome:
    status: str
    source_value: Any = None
    target_value: Any = None
    meaning: str = ""
    evidence: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        out = asdict(self)
        if out.get("evidence") is None:
            out.pop("evidence", None)
        return out


def normalize_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text if text else None


def normalize_numeric(value: Any) -> Optional[str]:
    if value is None or str(value).strip() == "":
        return None
    try:
        dec = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    normalized = format(dec.normalize(), "f")
    if "." in normalized:
        normalized = normalized.rstrip("0").rstrip(".")
    return normalized or "0"


def normalize_code_system(system: Any) -> Optional[str]:
    if system is None:
        return None
    raw = str(system).strip()
    if not raw:
        return None
    upper = raw.upper()
    if upper.startswith("URN:HL7V2:"):
        return normalize_code_system(upper.split(":", 2)[-1])
    aliases = {
        "LN": "LOINC",
        "LOINC": "LOINC",
        "HTTP://LOINC.ORG": "LOINC",
        "URN:OID:2.16.840.1.113883.6.1": "LOINC",
        "CPT": "CPT",
        "URN:HL7V2:CPT": "CPT",
        "HL7": "HL7",
        "URN:HL7V2:HL7": "HL7",
        "SCT": "SNOMED_CT",
        "SNOMED": "SNOMED_CT",
        "SNOMEDCT": "SNOMED_CT",
        "HTTP://SNOMED.INFO/SCT": "SNOMED_CT",
    }
    return aliases.get(upper, upper)


def normalize_timestamp(value: Any) -> Optional[str]:
    """Canonicalize common HL7 TS and ISO-ish timestamps without inventing semantics.

    Zone-less values remain zone-less. Explicit source offsets remain explicit so
    SaSI can detect a converter that silently drops timezone information.
    """
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.split("^", 1)[0].strip()

    hl7 = re.fullmatch(
        r"(\d{4})(\d{2})(\d{2})(?:(\d{2})(?:(\d{2})(?:(\d{2})(?:\.\d+)?)?)?)?([+-]\d{4})?",
        text,
    )
    if hl7:
        y, m, d, hh, mm, ss, offset = hl7.groups()
        base = f"{y}-{m}-{d}"
        if hh is None:
            return base
        value_out = f"{base}T{hh}:{mm or '00'}:{ss or '00'}"
        if offset:
            value_out += f"{offset[:3]}:{offset[3:]}"
        return value_out

    iso = text.replace(" ", "T")
    if iso.endswith(("Z", "z")):
        zone = "Z"
        iso = iso[:-1]
    else:
        zone_match = re.search(r"([+-]\d{2}:?\d{2})$", iso)
        zone = zone_match.group(1) if zone_match else ""
        if zone_match:
            iso = iso[: zone_match.start()]
            if len(zone) == 5 and ":" not in zone:
                zone = zone[:3] + ":" + zone[3:]

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", iso):
        return iso + zone
    m = re.match(r"^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?", iso)
    if m:
        date, hh, mm, ss = m.groups()
        return f"{date}T{hh}:{mm}:{ss or '00'}{zone}"
    return normalize_text(text)


def normalize_unit(unit: Any) -> Optional[str]:
    text = normalize_text(unit)
    return text.casefold() if text else None


def normalize_code(code: Any) -> Optional[str]:
    text = normalize_text(code)
    return text.upper() if text else None


def _canonical_coding(coding: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    return (
        normalize_code(coding.get("code")),
        normalize_code_system(coding.get("system")),
        normalize_text(coding.get("display")),
    )


def _source_obx_value(obs: Dict[str, Any]) -> Tuple[str, Any]:
    value_type = (obs.get("valueType") or "").upper()
    raw = obs.get("value")
    if value_type == "NM":
        return "numeric", normalize_numeric(raw)
    if value_type in {"DT", "TS"}:
        return "datetime", normalize_timestamp(raw)
    if value_type in {"CE", "CWE", "CNE"}:
        coding = obs.get("valueCoding") or {}
        return "coding", _canonical_coding(coding)
    return "text", normalize_text(raw)


def _target_observation_value(obs: Dict[str, Any]) -> Tuple[str, Any]:
    if "valueQuantity" in obs:
        return "numeric", normalize_numeric((obs.get("valueQuantity") or {}).get("value"))
    if "valueDateTime" in obs:
        return "datetime", normalize_timestamp(obs.get("valueDateTime"))
    if "valueCodeableConcept" in obs:
        codings = (obs.get("valueCodeableConcept") or {}).get("coding") or []
        coding = codings[0] if codings else {}
        return "coding", _canonical_coding(coding)
    if "valueString" in obs:
        return "text", normalize_text(obs.get("valueString"))
    return "missing", None


def message_type_supported(source: Dict[str, Any], target: Dict[str, Any], **params: Any) -> SamOutcome:
    msg_type = (source.get("messageType") or "UNKNOWN").upper()
    prefixes = [str(x).upper() for x in (params.get("supported_prefixes") or ["ADT^", "ORU^", "DFT^"])]
    ok = any(msg_type.startswith(prefix) for prefix in prefixes)
    return SamOutcome(
        PASS if ok else FAIL,
        source_value=msg_type,
        target_value="supported" if ok else "fallback/unsupported",
        meaning="PIQITT has an explicit converter for this message family." if ok else "PIQITT does not have an explicit converter for this message family.",
        evidence={"supportedPrefixes": prefixes},
    )


def patient_preserved(source: Dict[str, Any], target: Dict[str, Any], **params: Any) -> SamOutcome:
    src = source.get("patient")
    if not src:
        return SamOutcome(SKIP, meaning="Source message has no PID patient to preserve.")
    targets = target.get("patients") or []
    if not targets:
        return SamOutcome(FAIL, source_value=src, target_value=None, meaning="PID patient disappeared during transformation.")

    src_ids = {normalize_text(x.get("value")) for x in src.get("identifiers", []) if normalize_text(x.get("value"))}
    tgt_ids = {
        normalize_text(i.get("value"))
        for p in targets
        for i in (p.get("identifier") or [])
        if normalize_text(i.get("value"))
    }
    if src_ids and not (src_ids & tgt_ids):
        return SamOutcome(
            FAIL,
            source_value=sorted(src_ids),
            target_value=sorted(tgt_ids),
            meaning="A Patient exists, but the source patient identifier was not preserved.",
        )
    return SamOutcome(
        PASS,
        source_value=sorted(src_ids) if src_ids else "PID present",
        target_value=sorted(tgt_ids) if tgt_ids else f"{len(targets)} Patient resource(s)",
        meaning="Source patient identity is represented in the FHIR Bundle.",
    )


def encounter_preserved(source: Dict[str, Any], target: Dict[str, Any], **params: Any) -> SamOutcome:
    src = source.get("encounter")
    if not src:
        return SamOutcome(SKIP, meaning="Source message has no PV1 encounter to preserve.")
    encounters = target.get("encounters") or []
    if not encounters:
        return SamOutcome(FAIL, source_value=src, target_value=None, meaning="PV1 encounter disappeared during transformation.")
    src_class = normalize_code(src.get("class"))
    tgt_class = normalize_code(((encounters[0].get("class") or {}).get("code")))
    status = PASS if (not src_class or src_class == tgt_class) else FAIL
    return SamOutcome(
        status,
        source_value=src_class,
        target_value=tgt_class,
        meaning="Encounter class and presence were preserved." if status == PASS else "Encounter exists, but its class changed during transformation.",
    )


def obx_cardinality_preserved(source: Dict[str, Any], target: Dict[str, Any], **params: Any) -> SamOutcome:
    src_count = len(source.get("observations") or [])
    if src_count == 0:
        return SamOutcome(SKIP, source_value=0, meaning="No source OBX segments to compare.")
    tgt_count = len(target.get("observations") or [])
    return SamOutcome(
        PASS if src_count == tgt_count else FAIL,
        source_value=src_count,
        target_value=tgt_count,
        meaning="OBX cardinality was preserved." if src_count == tgt_count else "The number of FHIR Observations differs from the number of source OBX segments.",
    )


def ft1_cardinality_preserved(source: Dict[str, Any], target: Dict[str, Any], **params: Any) -> SamOutcome:
    src_count = len(source.get("transactions") or [])
    if src_count == 0:
        return SamOutcome(SKIP, source_value=0, meaning="No source FT1 segments to compare.")
    tgt_count = len(target.get("claims") or [])
    return SamOutcome(
        PASS if src_count == tgt_count else FAIL,
        source_value=src_count,
        target_value=tgt_count,
        meaning="FT1-to-Claim cardinality was preserved." if src_count == tgt_count else "The number of FHIR Claims differs from the number of source FT1 segments.",
    )


def code_preserved(source: Dict[str, Any], target: Dict[str, Any], **params: Any) -> SamOutcome:
    src_obs = source.get("observations") or []
    if not src_obs:
        return SamOutcome(SKIP, meaning="No source OBX codes to compare.")
    tgt_obs = target.get("observations") or []
    mismatches: List[Dict[str, Any]] = []
    for idx, src in enumerate(src_obs):
        if idx >= len(tgt_obs):
            mismatches.append({"index": idx, "source": src.get("code"), "target": None})
            continue
        src_code = _canonical_coding(src.get("code") or {})
        codings = ((tgt_obs[idx].get("code") or {}).get("coding") or [])
        tgt_code = _canonical_coding(codings[0] if codings else {})
        if src_code[:2] != tgt_code[:2]:
            mismatches.append({"index": idx, "source": src_code, "target": tgt_code})
    status = PASS if not mismatches and len(src_obs) <= len(tgt_obs) else FAIL
    return SamOutcome(
        status,
        source_value=len(src_obs),
        target_value=len(tgt_obs),
        meaning="OBX code/system semantics were preserved." if status == PASS else "One or more OBX code/system pairs changed or disappeared.",
        evidence={"mismatches": mismatches[:25], "mismatchCount": len(mismatches)},
    )


def value_preserved(source: Dict[str, Any], target: Dict[str, Any], **params: Any) -> SamOutcome:
    src_obs = source.get("observations") or []
    if not src_obs:
        return SamOutcome(SKIP, meaning="No source OBX values to compare.")
    tgt_obs = target.get("observations") or []
    mismatches: List[Dict[str, Any]] = []
    compared = 0
    for idx, src in enumerate(src_obs):
        if idx >= len(tgt_obs):
            mismatches.append({"index": idx, "source": _source_obx_value(src), "target": None})
            continue
        s_kind, s_val = _source_obx_value(src)
        t_kind, t_val = _target_observation_value(tgt_obs[idx])
        if s_val is None and t_val is None:
            continue
        compared += 1
        if s_kind != t_kind or s_val != t_val:
            mismatches.append({"index": idx, "source": [s_kind, s_val], "target": [t_kind, t_val]})
    if compared == 0 and not mismatches:
        return SamOutcome(SKIP, meaning="No comparable OBX values were present.")
    status = PASS if not mismatches else FAIL
    return SamOutcome(
        status,
        source_value=compared,
        target_value=compared - len(mismatches),
        meaning="Comparable OBX values were preserved." if status == PASS else "One or more OBX values changed, changed type, or disappeared.",
        evidence={"mismatches": mismatches[:25], "mismatchCount": len(mismatches)},
    )


def unit_preserved(source: Dict[str, Any], target: Dict[str, Any], **params: Any) -> SamOutcome:
    src_obs = source.get("observations") or []
    tgt_obs = target.get("observations") or []
    compared = 0
    mismatches: List[Dict[str, Any]] = []
    for idx, src in enumerate(src_obs):
        src_unit = normalize_unit(src.get("unit"))
        if src_unit is None:
            continue
        compared += 1
        tgt_unit = None
        if idx < len(tgt_obs):
            tgt_unit = normalize_unit(((tgt_obs[idx].get("valueQuantity") or {}).get("unit")))
        if src_unit != tgt_unit:
            mismatches.append({"index": idx, "source": src_unit, "target": tgt_unit})
    if compared == 0:
        return SamOutcome(SKIP, meaning="No source OBX units to compare.")
    status = PASS if not mismatches else FAIL
    return SamOutcome(
        status,
        source_value=compared,
        target_value=compared - len(mismatches),
        meaning="OBX measurement units were preserved." if status == PASS else "One or more OBX measurement units changed or disappeared.",
        evidence={"mismatches": mismatches[:25], "mismatchCount": len(mismatches)},
    )


def effective_time_preserved(source: Dict[str, Any], target: Dict[str, Any], **params: Any) -> SamOutcome:
    src_obs = source.get("observations") or []
    tgt_obs = target.get("observations") or []
    compared = 0
    mismatches: List[Dict[str, Any]] = []
    for idx, src in enumerate(src_obs):
        src_time = normalize_timestamp(src.get("effectiveTime"))
        if src_time is None:
            continue
        compared += 1
        tgt_time = normalize_timestamp(tgt_obs[idx].get("effectiveDateTime")) if idx < len(tgt_obs) else None
        if src_time != tgt_time:
            mismatches.append({"index": idx, "source": src_time, "target": tgt_time})
    if compared == 0:
        return SamOutcome(SKIP, meaning="No source OBX effective times to compare.")
    status = PASS if not mismatches else FAIL
    return SamOutcome(
        status,
        source_value=compared,
        target_value=compared - len(mismatches),
        meaning="OBX effective times were preserved after canonicalization." if status == PASS else "One or more OBX effective times changed or disappeared.",
        evidence={"mismatches": mismatches[:25], "mismatchCount": len(mismatches)},
    )


def references_resolve(source: Dict[str, Any], target: Dict[str, Any], **params: Any) -> SamOutcome:
    refs = target.get("references") or []
    if not refs:
        return SamOutcome(SKIP, meaning="No local FHIR references to resolve.")
    resources = set(target.get("resourceKeys") or [])
    local_refs = [r for r in refs if isinstance(r, str) and "/" in r and not r.startswith(("http://", "https://", "urn:"))]
    if not local_refs:
        return SamOutcome(SKIP, meaning="No relative FHIR references to resolve.")
    unresolved = sorted({r for r in local_refs if r not in resources})
    return SamOutcome(
        PASS if not unresolved else FAIL,
        source_value=len(local_refs),
        target_value=len(local_refs) - len(unresolved),
        meaning="All relative FHIR references resolve inside the Bundle." if not unresolved else "One or more relative FHIR references do not resolve inside the Bundle.",
        evidence={"unresolved": unresolved[:50], "unresolvedCount": len(unresolved)},
    )


SAM_DISPATCH = {
    "XFORM_MessageTypeSupported": message_type_supported,
    "XFORM_PatientPreserved": patient_preserved,
    "XFORM_EncounterPreserved": encounter_preserved,
    "XFORM_OBXCardinalityPreserved": obx_cardinality_preserved,
    "XFORM_FT1CardinalityPreserved": ft1_cardinality_preserved,
    "XFORM_CodePreserved": code_preserved,
    "XFORM_ValuePreserved": value_preserved,
    "XFORM_UnitPreserved": unit_preserved,
    "XFORM_EffectiveTimePreserved": effective_time_preserved,
    "XFORM_ReferencesResolve": references_resolve,
}
