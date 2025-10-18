import json
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# -----------------
# HL7 text helpers
# -----------------

def _norm(s: str) -> str:
    """Normalize newlines so we can split reliably."""
    return s.replace("\r\n", "\n").replace("\r", "\n")

def split_segments(hl7: str) -> List[str]:
    """Split an HL7 message into non-empty segment lines."""
    return [ln for ln in _norm(hl7).split("\n") if ln.strip()]

def parse_segment(line: str) -> tuple[str, list[str]]:
    """Return (SEG, fields[]) for a segment line."""
    parts = line.split("|")
    seg = parts[0].strip()
    fields = parts[1:]
    return seg, fields

def get_field(fields: List[str], idx_1_based: int) -> str:
    """
    Generic field accessor for non-MSH segments.
    HL7 fields are documented as 1-based; our list is 0-based.
    """
    i = idx_1_based - 1
    if i < 0 or i >= len(fields):
        return ""
    return fields[i]

# MSH indexing is special:
# After splitting on '|', fields[0] == MSH-2 (encoding chars), not MSH-1.
# To fetch true MSH-N, use N-2 on the list.
def get_msh_field(msh_fields: List[str], msh_idx: int) -> str:
    adj = msh_idx - 2
    if adj < 0 or adj >= len(msh_fields):
        return ""
    return msh_fields[adj]

def comp(field: str, i: int) -> str:
    """Extract component i (1-based) from a ^-delimited HL7 field."""
    comps = field.split("^") if field else []
    j = i - 1
    return comps[j] if 0 <= j < len(comps) else ""

def reps(field: str) -> List[str]:
    """Split a repeating HL7 field on ~."""
    return field.split("~") if field else []

def split_messages(hl7_text: str) -> List[str]:
    """
    Split a text blob that may contain multiple HL7 messages.
    We detect message starts by lines beginning with 'MSH|'.
    """
    lines = split_segments(hl7_text)
    starts = [i for i, ln in enumerate(lines) if ln.startswith("MSH|")]
    messages: List[str] = []
    for idx, start in enumerate(starts):
        end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
        block = "\n".join(lines[start:end]).strip()
        if block:
            messages.append(block)
    return messages

def parse_hl7(hl7_text: str) -> Dict[str, Any]:
    """
    Parse a single HL7 message into a dict of segment arrays and ordered list.
    out["SEG"] = [{"_fields": [...]}, ...]
    out["_order"] = [(SEG, fields), ...]
    """
    segments = split_segments(hl7_text)
    out: Dict[str, Any] = {"MSH": [], "PID": [], "PV1": [], "OBR": [], "OBX": [], "FT1": []}
    ordered: List[Tuple[str, List[str]]] = []
    for line in segments:
        seg, fields = parse_segment(line)
        ordered.append((seg, fields))
        entry = {"_fields": fields}
        if seg in out:
            out[seg].append(entry)
        else:
            out[seg] = [entry]
    out["_order"] = ordered
    return out

# ----------------
# FHIR primitives
# ----------------

def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid4()}"

def to_gender(sex: str) -> str:
    sx = (sex or "").strip().upper()
    return {"M": "male", "F": "female", "O": "other", "U": "unknown"}.get(sx, "unknown")

def to_iso_date(d: str) -> Optional[str]:
    """Return YYYY-MM-DD from YYYYMMDD or ISO-like input."""
    if not d:
        return None
    d = d.strip()
    if len(d) == 8 and d.isdigit():
        return f"{d[0:4]}-{d[4:6]}-{d[6:8]}"
    try:
        return datetime.fromisoformat(d).date().isoformat()
    except Exception:
        return None

def codeable_concept_from_ce(ce_field: str) -> Dict[str, Any]:
    """
    Map a CE field 'code^text^system' to a FHIR CodeableConcept.
    If system indicates LOINC (LN/LOINC), use http://loinc.org.
    Otherwise retain/mark HL7v2 system.
    """
    code = comp(ce_field, 1)
    text = comp(ce_field, 2)
    system = comp(ce_field, 3)
    coding = []
    if code:
        if system and system.upper() in ("LN", "LOINC"):
            system_uri = "http://loinc.org"
        elif system:
            system_uri = f"urn:hl7v2:{system}"
        else:
            system_uri = "urn:hl7v2"
        coding.append({"system": system_uri, "code": code, "display": text or None})
    cc: Dict[str, Any] = {"coding": coding} if coding else {}
    if text and not coding:
        cc["text"] = text
    return cc

# ----------------------
# Resource constructors
# ----------------------

def build_message_header(msh_fields: List[str]) -> Dict[str, Any]:
    """
    Build MessageHeader using MSH fields via MSH-safe indexing.
    - MSH-9 -> event
    - MSH-3,4,5,6 -> source/destination
    """
    ev = get_msh_field(msh_fields, 9)
    ev_code = comp(ev, 1)
    ev_trigger = comp(ev, 2)

    sending_app = get_msh_field(msh_fields, 3)
    sending_fac = get_msh_field(msh_fields, 4)
    receiving_app = get_msh_field(msh_fields, 5)
    receiving_fac = get_msh_field(msh_fields, 6)

    return {
        "resourceType": "MessageHeader",
        "id": new_id("msg"),
        "eventCoding": {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0003",
            "code": f"{ev_code}^{ev_trigger}" if ev_trigger else ev_code
        },
        "source": {"name": f"{sending_app}|{sending_fac}".strip("|") or "Unknown"},
        "destination": [{"name": f"{receiving_app}|{receiving_fac}".strip("|") or "Unknown"}],
        "timestamp": datetime.utcnow().isoformat(timespec="seconds") + "Z"
    }

def build_patient_from_pid(pid_fields: List[str]) -> Dict[str, Any]:
    # PID-3: identifiers (repeating)
    pid3 = get_field(pid_fields, 3)
    identifiers = []
    for rep in reps(pid3):
        id_val = comp(rep, 1)
        id_assigner = comp(rep, 4)
        if id_val:
            identifiers.append({
                "system": f"urn:oid:{id_assigner}" if id_assigner else "urn:mrn",
                "value": id_val
            })

    # PID-5: name family^given
    name = get_field(pid_fields, 5)
    family = comp(name, 1)
    given = comp(name, 2)

    # DOB + Sex
    birth_date = to_iso_date(get_field(pid_fields, 7))
    gender = to_gender(get_field(pid_fields, 8))

    # Address (street^other^city^state^zip)
    addr = get_field(pid_fields, 11)
    street = comp(addr, 1)
    city = comp(addr, 3)
    state = comp(addr, 4)
    postal = comp(addr, 5)

    patient: Dict[str, Any] = {
        "resourceType": "Patient",
        "id": new_id("pat"),
        "name": [{"family": family, "given": [given] if given else []}],
        "gender": gender,
        "birthDate": birth_date
    }
    if identifiers:
        patient["identifier"] = identifiers
    if any([street, city, state, postal]):
        patient["address"] = [{
            "line": [street] if street else [],
            "city": city or None,
            "state": state or None,
            "postalCode": postal or None
        }]
    return patient

def build_encounter_from_pv1(pv1_fields: List[str], patient_ref: str) -> Dict[str, Any]:
    # PV1-2: class, PV1-3: location (point-of-care^room^bed^facility)
    cls = get_field(pv1_fields, 2)
    loc = get_field(pv1_fields, 3)
    pof = comp(loc, 1)
    room = comp(loc, 2)
    bed = comp(loc, 3)
    facility = comp(loc, 4)

    encounter: Dict[str, Any] = {
        "resourceType": "Encounter",
        "id": new_id("enc"),
        "status": "finished",
        "class": {"code": cls or "UNK"},
        "subject": {"reference": patient_ref},
    }
    if any([pof, room, bed, facility]):
        encounter["extension"] = [{
            "url": "http://example.org/fhir/StructureDefinition/hl7v2-location",
            "extension": [
                {"url": "pointOfCare", "valueString": pof},
                {"url": "room", "valueString": room},
                {"url": "bed", "valueString": bed},
                {"url": "facility", "valueString": facility}
            ]
        }]
    return encounter

def build_observation_from_obx(obx_fields: List[str], patient_ref: Optional[str], encounter_ref: Optional[str]) -> Dict[str, Any]:
    """
    Map one OBX to an Observation. Supports common value types:
    - TX/ST -> valueString
    - NM -> valueQuantity (+ OBX-6 units)
    - CE -> valueCodeableConcept
    - DT/TS -> valueDateTime
    Effective date from OBX-14 when present.
    """
    vtype = get_field(obx_fields, 2).upper()
    id_ce = get_field(obx_fields, 3)
    val = get_field(obx_fields, 5)
    units = get_field(obx_fields, 6)
    dt_obs = get_field(obx_fields, 14)

    obs: Dict[str, Any] = {
        "resourceType": "Observation",
        "id": new_id("obs"),
        "status": "final",
        "code": codeable_concept_from_ce(id_ce) or {"text": "Observation"},
    }
    if patient_ref:
        obs["subject"] = {"reference": patient_ref}
    if encounter_ref:
        obs["encounter"] = {"reference": encounter_ref}

    # Effective time from OBX-14
    if dt_obs and len(dt_obs) >= 8:
        # Support YYYYMMDD[HHMMSS]
        y, m, d = dt_obs[0:4], dt_obs[4:6], dt_obs[6:8]
        if len(dt_obs) >= 14:
            hh, mm, ss = dt_obs[8:10], dt_obs[10:12], dt_obs[12:14]
            obs["effectiveDateTime"] = f"{y}-{m}-{d}T{hh}:{mm}:{ss}"
        else:
            obs["effectiveDateTime"] = f"{y}-{m}-{d}"

    # Value typing
    if vtype in ("TX", "ST"):
        obs["valueString"] = val
    elif vtype == "NM":
        try:
            obs["valueQuantity"] = {"value": float(val)}
            if units:
                # Try 'mg/dL' text first; if CE-like, fall back to components.
                if "^" in units:
                    obs["valueQuantity"]["unit"] = comp(units, 2) or comp(units, 1)
                else:
                    obs["valueQuantity"]["unit"] = units
        except Exception:
            obs["valueString"] = val
    elif vtype == "CE":
        obs["valueCodeableConcept"] = codeable_concept_from_ce(val)
    elif vtype in ("DT", "TS"):
        try:
            d = val[:8]  # YYYYMMDD
            obs["valueDateTime"] = f"{d[0:4]}-{d[4:6]}-{d[6:8]}"
        except Exception:
            obs["valueString"] = val
    else:
        obs["valueString"] = val

    return obs

def build_diagnostic_report_from_obr(obr_fields: List[str], patient_ref: Optional[str], encounter_ref: Optional[str], observations_refs: List[str]) -> Dict[str, Any]:
    # OBR-4: Universal Service ID
    svc = get_field(obr_fields, 4)
    code = codeable_concept_from_ce(svc)
    dr: Dict[str, Any] = {
        "resourceType": "DiagnosticReport",
        "id": new_id("dr"),
        "status": "final",
        "code": code or {"text": "Diagnostic Report"},
        "result": [{"reference": r} for r in observations_refs]
    }
    if patient_ref:
        dr["subject"] = {"reference": patient_ref}
    if encounter_ref:
        dr["encounter"] = {"reference": encounter_ref}
    return dr

def build_account_from_ft1(ft1_fields: List[str], patient_ref: Optional[str], encounter_ref: Optional[str]) -> Dict[str, Any]:
    """
    Very light DFT/FT1 -> Claim mapping:
    - FT1-4: date
    - FT1-6: transaction code
    - FT1-7: description
    - FT1-10: amount
    """
    dt = get_field(ft1_fields, 4)
    code = get_field(ft1_fields, 6)
    desc = get_field(ft1_fields, 7)
    amt = get_field(ft1_fields, 10)

    claim: Dict[str, Any] = {
        "resourceType": "Claim",
        "id": new_id("claim"),
        "status": "active",
        "type": {"text": "professional"},
        "item": [],
    }
    if patient_ref:
        claim["patient"] = {"reference": patient_ref}
    if encounter_ref:
        claim["encounter"] = [{"reference": encounter_ref}]
    if dt and len(dt) >= 8:
        d = f"{dt[0:4]}-{dt[4:6]}-{dt[6:8]}"
        claim["billablePeriod"] = {"start": d, "end": d}
    if code or desc or amt:
        entry: Dict[str, Any] = {"sequence": 1, "productOrService": {"text": f"{code} {desc}".strip()}}
        if amt:
            try:
                entry["unitPrice"] = {"value": float(amt)}
            except Exception:
                pass
        claim["item"].append(entry)
    return claim

# -------------------------
# Message type conversions
# -------------------------

def detect_message_type(parsed: Dict[str, Any]) -> str:
    """Return e.g., 'ORU^R01', 'ADT^A01', 'DFT^P03'."""
    if not parsed.get("MSH"):
        return "UNKNOWN"
    ev = get_msh_field(parsed["MSH"][0]["_fields"], 9)  # MSH-9
    return f"{comp(ev, 1)}^{comp(ev, 2)}".upper()

def convert_oru(parsed: Dict[str, Any]) -> Dict[str, Any]:
    msh = parsed["MSH"][0]["_fields"]
    pid = parsed["PID"][0]["_fields"] if parsed.get("PID") else None
    pv1 = parsed["PV1"][0]["_fields"] if parsed.get("PV1") else None

    msg_header = build_message_header(msh)
    patient = build_patient_from_pid(pid) if pid else None
    patient_ref = f"Patient/{patient['id']}" if patient else None
    encounter = build_encounter_from_pv1(pv1, patient_ref) if (pv1 and patient_ref) else None
    encounter_ref = f"Encounter/{encounter['id']}" if encounter else None

    observations = [build_observation_from_obx(o["_fields"], patient_ref, encounter_ref)
                    for o in parsed.get("OBX", [])]
    obs_refs = [f"Observation/{o['id']}" for o in observations]

    if parsed.get("OBR"):
        dr = build_diagnostic_report_from_obr(parsed["OBR"][0]["_fields"], patient_ref, encounter_ref, obs_refs)
    else:
        dr = {
            "resourceType": "DiagnosticReport",
            "id": new_id("dr"),
            "status": "final",
            "code": {"text": "Diagnostic Report"},
            "subject": {"reference": patient_ref} if patient_ref else None,
            "result": [{"reference": r} for r in obs_refs]
        }
        if encounter_ref:
            dr["encounter"] = {"reference": encounter_ref}

    entries = [{"resource": msg_header}]
    if patient: entries.append({"resource": patient})
    if encounter: entries.append({"resource": encounter})
    entries.append({"resource": dr})
    for o in observations:
        entries.append({"resource": o})

    return {"resourceType": "Bundle", "type": "message", "id": new_id("bundle"), "entry": entries}

def convert_adt(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    ADT now also emits Observations for any OBX segments present.
    If an OBR is present, we wrap OBX-derived Observations in a DiagnosticReport.
    """
    msh = parsed["MSH"][0]["_fields"]
    pid = parsed["PID"][0]["_fields"] if parsed.get("PID") else None
    pv1 = parsed["PV1"][0]["_fields"] if parsed.get("PV1") else None

    msg_header = build_message_header(msh)
    patient = build_patient_from_pid(pid) if pid else None
    patient_ref = f"Patient/{patient['id']}" if patient else None
    encounter = build_encounter_from_pv1(pv1, patient_ref) if (pv1 and patient_ref) else None
    encounter_ref = f"Encounter/{encounter['id']}" if encounter else None

    # NEW: Turn ADT OBX segments into Observations
    observations = [build_observation_from_obx(o["_fields"], patient_ref, encounter_ref)
                    for o in parsed.get("OBX", [])]
    obs_refs = [f"Observation/{o['id']}" for o in observations]

    # Optional DR wrapper if OBR provided
    dr = None
    if parsed.get("OBR"):
        dr = build_diagnostic_report_from_obr(parsed["OBR"][0]["_fields"], patient_ref, encounter_ref, obs_refs)

    entries = [{"resource": msg_header}]
    if patient: entries.append({"resource": patient})
    if encounter: entries.append({"resource": encounter})
    if dr: entries.append({"resource": dr})
    for o in observations:
        entries.append({"resource": o})

    return {"resourceType": "Bundle", "type": "message", "id": new_id("bundle"), "entry": entries}

def convert_dft(parsed: Dict[str, Any]) -> Dict[str, Any]:
    msh = parsed["MSH"][0]["_fields"]
    pid = parsed["PID"][0]["_fields"] if parsed.get("PID") else None
    pv1 = parsed["PV1"][0]["_fields"] if parsed.get("PV1") else None

    msg_header = build_message_header(msh)
    patient = build_patient_from_pid(pid) if pid else None
    patient_ref = f"Patient/{patient['id']}" if patient else None
    encounter = build_encounter_from_pv1(pv1, patient_ref) if (pv1 and patient_ref) else None
    encounter_ref = f"Encounter/{encounter['id']}" if encounter else None

    claims = [build_account_from_ft1(ft["_fields"], patient_ref, encounter_ref) for ft in parsed.get("FT1", [])]

    entries = [{"resource": msg_header}]
    if patient: entries.append({"resource": patient})
    if encounter: entries.append({"resource": encounter})
    for c in claims:
        entries.append({"resource": c})

    return {"resourceType": "Bundle", "type": "message", "id": new_id("bundle"), "entry": entries}

# -------------
# Orchestration
# -------------

def convert_message_to_bundle(hl7_text: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse a single message, detect type, and convert.
    Returns (FHIR Bundle, message_type_string), e.g., ('ORU^R01').
    """
    parsed = parse_hl7(hl7_text)
    msg_type = detect_message_type(parsed)

    if msg_type.startswith("ORU^"):
        return convert_oru(parsed), msg_type
    if msg_type.startswith("ADT^"):
        return convert_adt(parsed), msg_type
    if msg_type.startswith("DFT^"):
        return convert_dft(parsed), msg_type

    # Fallback: MessageHeader (+ Patient if present)
    msh = parsed["MSH"][0]["_fields"]
    mh = build_message_header(msh)
    patient = build_patient_from_pid(parsed["PID"][0]["_fields"]) if parsed.get("PID") else None
    entries = [{"resource": mh}]
    if patient:
        entries.append({"resource": patient})
    bundle = {"resourceType": "Bundle", "type": "message", "id": new_id("bundle"), "entry": entries}
    return bundle, msg_type
