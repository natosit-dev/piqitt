from __future__ import annotations

from pathlib import Path

from scripts.fhir_convert import convert_file


def test_convert_file_materializes_adt_bundle(tmp_path: Path):
    hl7 = "\r".join(
        [
            r"MSH|^~\&|MEDILACRA|FAC|PIQITT|TEST|20260902100000||ADT^A01|MSG1|P|2.5",
            "PID|1||MRN1^^^FAC||Doe^Jane||19800101|F|||1 Main St^^Lowell^MA^01854",
            "PV1|1|I|WARD^101^A^FAC",
        ]
    )
    source = tmp_path / "case.hl7"
    source.write_text(hl7, encoding="utf-8")

    bundle, message_type, message_count = convert_file(source)

    assert message_type == "ADT^A01"
    assert message_count == 1
    assert bundle["resourceType"] == "Bundle"
    resource_types = [entry["resource"]["resourceType"] for entry in bundle["entry"]]
    assert "Patient" in resource_types
    assert "Encounter" in resource_types
