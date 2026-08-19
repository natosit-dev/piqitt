# PIQITT

PIQI Transformation Tool (PIQITT): **HL7 v2 → FHIR → PIQI scorecard testing**.

PIQITT converts HL7 v2 messages into simplified FHIR Bundles and evaluates those Bundles using the PIQI (Patient Information Quality Improvement) framework.

The `WAP_AS` branch — **Write-Audit-Public at Scale** — adds a backend execution path for large HL7 files and folders so bulk workloads do not have to pass through the Streamlit upload widget.

## Goals

1. Standardize data-quality checks across sources.
2. Apply reusable **Simple Assessment Modules (SAMs)** to FHIR resources.
3. Produce portable **PIQI scorecards**.
4. Preserve the existing interactive workflow for small samples.
5. Support large local workloads with bounded-memory backend processing and durable run history.

## Architecture

```text
piqitt.py
  └── Streamlit control surface
        ├── Upload files mode
        └── Backend path mode
                ↓
        scripts/wap_runner.py
                ↓
        scripts/fhir_convert_backend.py
                ↓
        scripts/piqi_eval.py
                ↓
        NDJSON result artifacts + DuckDB run repository
```

Core files:

- `piqitt.py` → Streamlit UI / control surface
- `scripts/fhir_convert_backend.py` → HL7 → FHIR conversion
- `scripts/piqi_eval.py` → evaluator, SAMs, and PIQI scoring
- `scripts/wap_runner.py` → file/folder discovery, streaming execution, aggregation, artifacts
- `scripts/run_repo.py` → DuckDB run/file/finding/artifact repository
- `scripts/wap_cli.py` → non-Streamlit entry point for the same backend runner
- `profiles/*.yaml` → evaluation profiles
- `piqi_sam_library.yaml` → SAM taxonomy and prerequisites
- `ref/plausibility.yaml` → physiologic plausibility configuration
- `ref/loinc.csv`, `ref/cpt.csv` → local terminology/value-set reference files

---

## 1. HL7 → FHIR Conversion

`scripts/fhir_convert_backend.py` converts supported HL7 v2 messages into simplified FHIR Bundles.

Key functions include:

- `split_messages(text)` — split multi-message HL7 payloads by `MSH|`
- `parse_hl7(text)` — normalize and collect segments/fields
- `build_patient_from_pid(pid)` — create `Patient`
- `build_encounter_from_pv1(pv1, patient_ref)` — create `Encounter`
- `build_observation_from_obx(obx, patient_ref, encounter_ref)` — create `Observation`
- `build_diagnostic_report_from_obr(...)` — create `DiagnosticReport`
- `build_account_from_ft1(...)` — map DFT/FT1 to a minimal `Claim`
- `convert_message_to_bundle(hl7_msg)` — detect message type and assemble a `Bundle`

ADT OBX segments are also mapped to `Observation`, and OBX-6 units feed plausibility checks.

---

## 2. PIQI Evaluation Engine

`scripts/piqi_eval.py` contains `PIQIEvaluator` and the SAM implementations.

The evaluator loads:

- SAM library
- Clinical / Claims profiles
- LOINC / CPT local reference sets
- plausibility configuration

`evaluate_bundle(bundle, profile_name)` returns a message-level scorecard with step-level detail.

### Scoring

1. Select target resources.
2. Run optional condition SAM.
3. Extract values.
4. Run prerequisite SAM if configured.
5. Run the main SAM.
6. Aggregate PASS / FAIL outcomes into PIQI indices.
7. Track critical failures separately.

Each detail record includes fields such as `stepId`, `sam`, `status`, `dimension`, and `valuePreview`.

---

## 3. Input Modes

### Upload files

The original Streamlit workflow remains available for small `.hl7` / `.txt` files.

Use it for:

- demos
- debugging
- small samples
- quick interactive inspection
- scorecard downloads and drill-down

This path still loads the uploaded workload into Streamlit/Python objects and is **not the scale path**.

### Backend path — WAP_AS

Backend mode accepts a filesystem path visible to the machine running PIQITT.

The path may point to:

- one `.hl7` file
- one `.txt` file
- a folder containing supported files

Folder discovery is currently **non-recursive**.

The backend runner:

1. discovers supported input files
2. creates a durable `run_id`
3. processes files sequentially
4. streams HL7 messages on `MSH|` boundaries
5. converts and evaluates one message at a time
6. writes detailed results incrementally as NDJSON
7. checkpoints aggregate run/file state into DuckDB
8. writes Markdown and JSON run summaries

A failed file is logged and marked `FAILED`; PIQITT continues with the remaining files. The overall run is marked `FAILED` if any file failed. A quarantine/retry queue is intentionally deferred.

---

## 4. WAP_AS Run Repository

Default DuckDB path:

```text
data/piqitt_runs.duckdb
```

Default artifact root:

```text
runs/
```

DuckDB stores operational metadata rather than the complete detailed result corpus.

Tables:

- `runs`
- `run_files`
- `run_findings`
- `run_artifacts`

Detailed per-message PIQI output is written to NDJSON files under the run artifact directory.

Generated DuckDB and run-artifact contents are ignored by Git.

---

## 5. Reference Data: Important Caveat

The evaluator expects local reference/configuration files such as:

```text
ref/loinc.csv
ref/cpt.csv
ref/plausibility.yaml
```

`ref/` is gitignored in this repository, so **a fresh clone does not include these local files**. Either place the required files at the configured paths or change the paths in the Streamlit sidebar / runner configuration.

A missing reference file will prevent evaluator initialization. During the first WAP_AS local smoke test, a fresh checkout failed before processing any messages because `ref/loinc.csv` was absent. After the local reference file was supplied, the same backend run completed successfully.

### LOINC reference coverage

The current development `loinc.csv` is a **small, informally sourced local reference file found online**. It is not presented as a complete or authoritative LOINC distribution, and PIQITT should not interpret its coverage as equivalent to full LOINC terminology coverage.

This matters when interpreting `Concept_IsValidMember` or other terminology-membership findings:

> A code missing from the local CSV may mean the local reference file is incomplete; it does not by itself establish that the real-world code is invalid.

For benchmark and Connectathon work, record which local reference files were used with the run. A future cleanup can add explicit reference-file preflight checks and stronger provenance/version metadata.

---

## 6. Running PIQITT

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start Streamlit:

```powershell
streamlit run piqitt.py
```

For large data, select **Backend path** and point PIQITT to the local input file/folder instead of uploading the files through the browser.

The backend path is resolved on the machine running PIQITT.

### CLI

The same backend runner can be invoked without Streamlit:

```powershell
python scripts/wap_cli.py "C:\path\to\hl7_folder"
```

Use `python scripts/wap_cli.py --help` for available options.

---

## 7. WAP_AS Validation Baseline

A local end-to-end backend-folder smoke test completed successfully on 2026-08-19:

- files: **5**
- messages: **1,000**
- status: **COMPLETE**
- critical failures: **0**
- elapsed: **4.658 seconds**
- overall mean PIQI: **77.14907**

Per-file results:

| Message family | Messages | Mean PIQI |
|---|---:|---:|
| ADT | 200 | 88.24 |
| DFT | 200 | 66.67 |
| ORM | 200 | 100.00 |
| ORU | 200 | 34.12 |
| ORU_LABS | 200 | 96.72 |

These values reproduce the known small-run PIQI behavior and establish that the new backend execution path did not change scoring semantics for the regression dataset.

The next scale target is the larger MediLacra benchmark, including the previously excluded ~200 MB DFT and ~600 MB ORU files.

---

## Project Documentation

- `PIQITT_WAP_AS_PROJECT_PLAN_2026-08-18.md` — architecture, definitions, workflow, phases, decisions, expected results
- `WAP_AS_BUILD_NOTES_2026-08-18.md` — implementation and validation notes
- `WAP_AS_VALIDATION_2026-08-19.md` — local runtime validation and reference-data caveats
