from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import fhir_convert_backend as fhir
from scripts.sasi_analyzer import SaSIAnalyzer
from scripts.sasi_summary import summarize
from scripts.sasi_sams import normalize_code_system, normalize_timestamp


def segment(name, fields):
    return name + "|" + "|".join(fields)


def msh(msg_type):
    return segment("MSH", ["^~\\&", "MEDILACRA", "MEDILACRAHS", "PIQITT", "TEST", "20260818120000", "", msg_type, "MSG1", "P", "2.5.1"])


def pid():
    fields = [""] * 11
    fields[0] = "1"
    fields[2] = "RAD123^^^MRN"
    fields[4] = "SMITH^JANE"
    fields[6] = "19800101"
    fields[7] = "F"
    return segment("PID", fields)


def pv1():
    fields = [""] * 3
    fields[0] = "1"
    fields[1] = "O"
    fields[2] = "RAD^101^1^FAC"
    return segment("PV1", fields)


def obx(set_id="1", code="8480-6^Systolic BP^LN", value="120", unit="mm[Hg]", when="20260818120000"):
    fields = [""] * 14
    fields[0] = set_id
    fields[1] = "NM"
    fields[2] = code
    fields[4] = value
    fields[5] = unit
    fields[13] = when
    return segment("OBX", fields)


def ft1(set_id="1"):
    fields = [""] * 10
    fields[0] = set_id
    fields[3] = "20260818"
    fields[5] = "71045"
    fields[6] = "Chest X-ray"
    fields[9] = "125.50"
    return segment("FT1", fields)


def analyzer():
    return SaSIAnalyzer(str(ROOT / "sasi_sam_library.yaml"), str(ROOT / "profiles/profile_sasi_minimal.yaml"))


def by_sam(result):
    return {d["sam"]: d for d in result["details"]}


def test_oru_preserves_core_structure():
    raw = "\r".join([msh("ORU^R01"), pid(), pv1(), obx()])
    bundle, msg_type = fhir.convert_message_to_bundle(raw)
    result = analyzer().evaluate(raw, bundle, msg_type)
    details = by_sam(result)
    assert details["XFORM_MessageTypeSupported"]["status"] == "PASS"
    assert details["XFORM_PatientPreserved"]["status"] == "PASS"
    assert details["XFORM_EncounterPreserved"]["status"] == "PASS"
    assert details["XFORM_OBXCardinalityPreserved"]["status"] == "PASS"
    assert details["XFORM_CodePreserved"]["status"] == "PASS"
    assert details["XFORM_ValuePreserved"]["status"] == "PASS"
    assert details["XFORM_UnitPreserved"]["status"] == "PASS"
    assert details["XFORM_EffectiveTimePreserved"]["status"] == "PASS"
    assert details["XFORM_ReferencesResolve"]["status"] == "PASS"
    assert details["XFORM_FT1CardinalityPreserved"]["status"] == "SKIP"


def test_unsupported_orm_exposes_silent_loss():
    raw = "\r".join([msh("ORM^O01"), pid(), pv1(), obx()])
    bundle, msg_type = fhir.convert_message_to_bundle(raw)
    result = analyzer().evaluate(raw, bundle, msg_type)
    details = by_sam(result)
    assert details["XFORM_MessageTypeSupported"]["status"] == "FAIL"
    assert details["XFORM_PatientPreserved"]["status"] == "PASS"
    assert details["XFORM_EncounterPreserved"]["status"] == "FAIL"
    assert details["XFORM_OBXCardinalityPreserved"]["status"] == "FAIL"
    assert details["XFORM_CodePreserved"]["status"] == "FAIL"


def test_dft_ft1_cardinality():
    raw = "\r".join([msh("DFT^P03"), pid(), pv1(), ft1("1"), ft1("2")])
    bundle, msg_type = fhir.convert_message_to_bundle(raw)
    result = analyzer().evaluate(raw, bundle, msg_type)
    details = by_sam(result)
    assert details["XFORM_FT1CardinalityPreserved"]["status"] == "PASS"
    assert details["XFORM_OBXCardinalityPreserved"]["status"] == "SKIP"


def test_summary_aggregates_sam_statuses():
    raw_ok = "\r".join([msh("ORU^R01"), pid(), pv1(), obx()])
    bundle_ok, mt_ok = fhir.convert_message_to_bundle(raw_ok)
    raw_bad = "\r".join([msh("ORM^O01"), pid(), pv1(), obx()])
    bundle_bad, mt_bad = fhir.convert_message_to_bundle(raw_bad)
    a = analyzer()
    summary = summarize([a.evaluate(raw_ok, bundle_ok, mt_ok), a.evaluate(raw_bad, bundle_bad, mt_bad)])
    assert summary["messages"] == 2
    assert summary["bySAM"]["XFORM_MessageTypeSupported"]["PASS"] == 1
    assert summary["bySAM"]["XFORM_MessageTypeSupported"]["FAIL"] == 1
    assert summary["distributionComparisons"]["observationCodes"]["retentionRatePct"] == 50.0


def test_hl7v2_code_system_wrapper_is_semantically_equivalent():
    assert normalize_code_system("SCT") == normalize_code_system("urn:hl7v2:SCT")
    assert normalize_code_system("CPT") == normalize_code_system("urn:hl7v2:CPT")


def test_timezone_loss_is_not_canonicalized_away():
    assert normalize_timestamp("20260818120000-0400") == "2026-08-18T12:00:00-04:00"
    assert normalize_timestamp("20260818120000-0400") != normalize_timestamp("2026-08-18T12:00:00")
