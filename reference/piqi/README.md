# PIQI Reference Artifacts — Connectathon Bridge

This directory is the start of replacing PIQITT's hand-authored YAML SAM/profile configuration with the PIQI Alliance reference artifacts used by the Connectathon.

## What is copied from the PIQI reference application

- `USCDI_V2.json` — official USCDI V2 Evaluation Rubric, copied unchanged from `piqiframework/reference_application/PIQI_Engine.Server/ReferenceData/Evaluations/USCDI_V2.json`.
- `USCDI_V3.json` — official USCDI V3 Evaluation Rubric, copied unchanged from the corresponding reference-application path.
- `SAMs_USCDI_V2_V3.json` — a reduced copy of the official SAM library containing the SAMs directly referenced by V2/V3 plus their prerequisite/conditional dependency closure.

The reduced SAM file intentionally preserves the PIQI field names and mnemonics. It is not translated into the old `piqi_sam_library.yaml` shape.

## What belongs to PIQITT

- `fhir_bindings_v0.json` — an explicit adapter from FHIR resources/paths to `PAT_CLINICAL_V1` entity mnemonics.

This is **not** PIQI Alliance reference content. It exists because the official rubric evaluates model entities such as `LAB_TEST` or `DEM_DOB`, while PIQITT currently starts from raw FHIR Bundles.

Keeping this mapping separate matters. The official rubric should not be rewritten into `Observation.code`, `Patient.birthDate`, etc. The FHIR-to-model transformation is a different concern from the quality rubric.

## Execution path

The experimental reference path is:

```text
FHIR Bundle
    -> fhir_bindings_v0.json
    -> PAT_CLINICAL_V1 entity mnemonic
    -> USCDI_V2.json / USCDI_V3.json criterion
    -> official SAM metadata
    -> local SAM execution only where semantics are implemented faithfully
```

Run a coverage report:

```bash
python scripts/piqi_reference.py
```

Run V3 coverage:

```bash
python scripts/piqi_reference.py --rubric reference/piqi/USCDI_V3.json
```

Run a FHIR Bundle through the bridge:

```bash
python scripts/piqi_reference.py --bundle path/to/bundle.json
```

## Important current behavior

The bridge reports four non-scoring states explicitly:

- `SKIP` — the criterion does not apply to the supplied data.
- `UNBOUND` — PIQITT does not yet have a FHIR-to-model binding for the official rubric entity.
- `UNSUPPORTED` — the official SAM is known, but PIQITT does not yet implement its semantics faithfully.
- missing SAM definition — artifact-set error; this should be zero for V2/V3.

This is deliberate. In particular, terminology-backed SAMs such as `CONCEPT_ISVALIDMEMBER`, `CONCEPT_ISACTIVE`, and `ATTR_INEXTERNALLIST` are **not** replaced with approximate local guesses. They remain unsupported until PIQITT is wired to appropriate terminology/content-set data or a PIQI terminology provider.

Primitive/date/presence semantics can already execute directly from the reference artifacts, including the dependency chains around `ATTR_ISPOPULATED`, `ATTR_ISDATE`, and `ATTR_ISPASTDATE`.

## Migration plan

1. Keep the original YAML evaluator untouched as the known-working baseline.
2. Exercise V2/V3 through `scripts/piqi_reference.py` and compare the extracted entities against published VA/Nava PIQI-converted artifacts.
3. Expand `fhir_bindings_v0.json` only when mappings are supported by the PIQI model/converter behavior; do not guess model semantics.
4. Add terminology/content-set resolution for the official code-system mnemonics (`REGEN_LOINC`, `SNO_INT_USEXT`, `NLM_RXN`, `CDC_CVX`, `UCUM`, etc.).
5. Compare outputs against the VA Connectathon audit fixtures.
6. Once the reference path reproduces expected results, make it the default and retire the YAML configuration path.

## Provenance snapshot

Copied from `piqiframework/reference_application` main branch on 2026-09-17 for HL7 Connectathon 43 preparation. Before the Connectathon, re-check upstream SHAs in case the track publishes a last-minute rubric/SAM update.
