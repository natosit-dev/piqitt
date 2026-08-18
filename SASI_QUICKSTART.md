# SaSI Quickstart

SaSI (**Structural and Statistical Integrity**, pronounced "sassy") runs beside PIQI and asks a different question:

> Did the important structure, values, relationships, counts, and population shape survive the HL7 v2 → FHIR transformation?

SaSI does **not** change PIQI scoring and does **not** modify PIQITT's current converter behavior.

## Run SaSI

From the repository root:

```powershell
python scripts/sasi_run.py C:\path\to\hl7\folder --out sasi_results.ndjson
```

The input can be either:

- one `.hl7` / `.txt` file, or
- a folder containing `.hl7` / `.txt` files.

SaSI uses PIQITT's existing `fhir_convert_backend.py` to transform every message, then compares the raw HL7 message with the generated FHIR Bundle.

To include the full source and target inventories in every result:

```powershell
python scripts/sasi_run.py C:\path\to\hl7\folder --out sasi_results.ndjson --include-inventories
```

## Summarize a Run

```powershell
python scripts/sasi_summary.py sasi_results.ndjson
```

This creates:

```text
sasi_summary.json
sasi_summary.md
```

The summary reports:

- PASS / FAIL / SKIP by message type
- PASS / FAIL / SKIP by SaSI SAM
- PASS / FAIL / SKIP by structural dimension
- source vs target patient-gender distributions
- source vs target observation-code distributions
- source vs target coded-observation-value distributions
- count retention for each compared population
- maximum distribution drift in percentage points

## Current V1 SAMs

```text
XFORM_MessageTypeSupported
XFORM_PatientPreserved
XFORM_EncounterPreserved
XFORM_OBXCardinalityPreserved
XFORM_FT1CardinalityPreserved
XFORM_CodePreserved
XFORM_ValuePreserved
XFORM_UnitPreserved
XFORM_EffectiveTimePreserved
XFORM_ReferencesResolve
```

The definitions live in:

```text
sasi_sam_library.yaml
```

The active assessment profile lives in:

```text
profiles/profile_sasi_minimal.yaml
```

## What PASS / FAIL / SKIP Mean

**PASS** means the specific transformation invariant tested by that SAM was preserved.

**FAIL** means the invariant was not preserved.

**SKIP** means there was no meaningful evaluation opportunity. For example, an ORU with no FT1 segments should SKIP FT1 cardinality rather than PASS it.

SaSI does not currently produce a 0–100 score. Ten checks with eight PASS, one FAIL, and one SKIP do **not** mean the data is "80% correct." The individual findings are the product.

## Statistical Integrity

SaSI reports two different aggregate signals:

### Count retention

Nat version:

> Did the same amount of stuff survive?

Example:

```text
Source observation-code count: 2
Target observation-code count: 1
Retention: 50%
```

### Distribution drift

Nat version:

> Of the stuff that survived, did the population shape change?

Example:

```text
Source:
A = 90%
B = 10%

Target:
A = 70%
B = 30%
```

These are deliberately separate. A transformation can lose half the records while preserving exactly the same percentages, or preserve every record while disproportionately changing categories.

## Run Tests

```powershell
pytest -q tests/test_sasi.py
```

The initial tests cover:

- normal ORU structural preservation
- unsupported ORM / fallback loss
- DFT FT1 → Claim cardinality
- aggregate SaSI summary behavior
- code-system canonicalization such as `SCT` ↔ `urn:hl7v2:SCT`

## Current Boundary

SaSI observes the existing PIQITT transformation. It does not repair it.

That is deliberate.

If SaSI says an ORM message is unsupported or data disappears, that is a measurement result. Converter fixes come after the measuring instrument is trusted.
