from datetime import datetime, timezone
from pathlib import Path

from scripts.piqi_reference import PIQIReferenceBridge, PASS, FAIL, UNSUPPORTED, UNBOUND


ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference" / "piqi"
SAMS = REF / "SAMs_USCDI_V2_V3.json"
BINDINGS = REF / "fhir_bindings_v0.json"


def bridge(rubric: str) -> PIQIReferenceBridge:
    return PIQIReferenceBridge(
        SAMS,
        REF / rubric,
        BINDINGS,
        now=datetime(2026, 9, 17, tzinfo=timezone.utc),
    )


def test_v2_and_v3_reference_sam_closure_is_present():
    for rubric in ("USCDI_V2.json", "USCDI_V3.json"):
        coverage = bridge(rubric).coverage()
        assert coverage["missingSamDefinitions"] == []
        assert coverage["criteria"] > 0
        assert coverage["boundCriteria"] > 0
        assert coverage["locallyExecutableCriteria"] > 0


def test_v2_runs_official_date_and_population_sams_without_yaml_profile():
    b = bridge("USCDI_V2.json")
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "p1",
                    "birthDate": "1980-01-02",
                    "communication": [{"language": {"text": "English"}}],
                }
            },
            {
                "resource": {
                    "resourceType": "Condition",
                    "id": "c1",
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "38341003",
                                "display": "Hypertension",
                            }
                        ]
                    },
                    "onsetDateTime": "2020-01-01T00:00:00Z",
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "id": "lab1",
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "laboratory",
                                }
                            ]
                        }
                    ],
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "718-7",
                                "display": "Hemoglobin",
                            }
                        ]
                    },
                    "effectiveDateTime": "2026-09-16T12:00:00Z",
                    "valueQuantity": {
                        "value": 13.4,
                        "unit": "g/dL",
                        "system": "http://unitsofmeasure.org",
                        "code": "g/dL",
                    },
                }
            },
        ],
    }

    result = b.evaluate_bundle(bundle)
    detail = {(row["entity"], row["sam"]): row for row in result["details"]}

    assert detail[("DEM_DOB", "ATTR_ISPASTDATE")]["status"] == PASS
    assert detail[("CND_ONDT", "ATTR_ISPASTDATE")]["status"] == PASS
    assert detail[("LAB_PERFDT", "ATTR_ISPASTDATE")]["status"] == PASS
    assert detail[("LAB_RESVALUE", "ATTR_ISPOPULATED")]["status"] == PASS

    # Terminology-backed membership is deliberately not approximated yet.
    assert detail[("LAB_TEST", "CONCEPT_ISVALIDMEMBER")]["status"] == UNSUPPORTED


def test_future_date_fails_past_date_sam():
    b = bridge("USCDI_V2.json")
    bundle = {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "future-patient",
                    "birthDate": "2099-01-01",
                }
            }
        ],
    }
    result = b.evaluate_bundle(bundle)
    dob = next(
        row
        for row in result["details"]
        if row["entity"] == "DEM_DOB" and row["sam"] == "ATTR_ISPASTDATE"
    )
    assert dob["status"] == FAIL


def test_unmapped_official_entities_are_reported_not_guessed():
    coverage = bridge("USCDI_V3.json").coverage()
    assert "DEM_SEX" in coverage["unboundEntities"]
    assert coverage["unboundCriteria"] > 0
