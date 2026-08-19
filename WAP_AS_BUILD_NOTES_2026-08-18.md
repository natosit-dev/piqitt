# PIQITT WAP_AS Build Notes

**Branch:** `WAP_AS`  
**Initial build date:** 2026-08-18  
**Local validation date:** 2026-08-19  
**Status:** Backend path implementation validated end-to-end on the 1,000-message regression dataset; ready for large-file benchmark testing

## What was built

- Backend file/folder execution mode in Streamlit.
- Non-recursive `.hl7` / `.txt` discovery.
- Streaming HL7 message iterator keyed on `MSH|` boundaries.
- Shared backend runner used independently of the UI.
- CLI entry point at `scripts/wap_cli.py`.
- Incremental NDJSON detail output per input file.
- DuckDB operational repository with:
  - `runs`
  - `run_files`
  - `run_findings`
  - `run_artifacts`
- Periodic run/file progress checkpoints every 1,000 successfully evaluated messages by default.
- Run-level Markdown and JSON summaries.
- Local `data/` and `runs/` contents ignored by Git while retaining the directories.
- Basic tests for HL7 streaming and folder discovery.

## Decision 011 — File failure policy

**Decision:** A file-level failure does not stop the remaining run queue.

Behavior:

1. Preserve all successfully written detail output from the failed file.
2. Record the exception in `runs/<run_id>/logs/run.log`.
3. Mark the file `FAILED` in `run_files`.
4. Persist aggregate findings collected before the failure.
5. Continue with the next discovered file.
6. After all files are attempted, mark the overall run `FAILED` if one or more files failed.

**Reason:** At scale, a bad input file should identify itself as bad rather than erase valid work from unrelated files.

## Decision 012 — Quarantine is deferred

A quarantine/retry queue is explicitly out of scope for this implementation.

For now, failed files are logged with enough provenance to support a future quarantine workflow without reconstructing what happened after the fact.

## Decision 013 — Local terminology files are dependencies, not bundled truth

`ref/` is gitignored. A fresh checkout therefore does not include `ref/loinc.csv`, `ref/cpt.csv`, or other locally managed reference material unless the user supplies it separately.

The development `loinc.csv` currently in use was sourced informally from material found online. It is small and is **not claimed to be a complete or authoritative LOINC distribution**.

Consequences:

- PIQITT terminology-membership checks are only as complete as the configured local value set.
- A `Concept_IsValidMember` failure may reflect limited local terminology coverage rather than an invalid real-world code.
- Benchmark results should preserve which reference files/configuration were used.
- A future enhancement should capture stronger terminology provenance/version metadata.

## Decision 014 — Reference-file preflight is desirable but not required before the scale benchmark

The first local backend run exposed a missing-reference failure cleanly:

```text
FileNotFoundError: ref\loinc.csv
```

The run infrastructure successfully preserved the failed execution in DuckDB, but the error occurred before message processing and therefore produced five discovered file records with zero processed messages.

The immediate fix was simply to provide the local `loinc.csv` at the configured path.

A future usability cleanup should validate required reference/configuration paths before beginning the run and present a direct configuration error such as:

```text
LOINC reference not found: ref\loinc.csv
```

This is backlog cleanup, not a blocker for WAP_AS scale testing.

## Validation performed before publish

- Python syntax compilation passed for the new runner, repository, CLI, UI source, and tests in the available implementation environment.
- Streaming harness confirmed CR-delimited HL7 files split correctly across `MSH|` boundaries without reading the complete file at once.
- Folder-discovery harness confirmed sorting, `.hl7` / `.txt` filtering, and non-recursive behavior.
- Failure-continuation harness exercised three files in order:
  - first file: `COMPLETE`
  - second file: forced `FAILED`
  - third file: `COMPLETE`
- The run correctly continued after the failed middle file, preserved two successful message results, and ended with overall status `FAILED`.

## Local runtime validation — 2026-08-19

The actual DuckDB-backed Streamlit/backend path was then run locally against:

```text
C:\Users\spooky\medilacra\output\test_regression
```

### Attempt 1 — expected configuration failure

The first run discovered all five files and created durable DuckDB run/file records, then failed before processing message 1 because the fresh WAP_AS checkout did not contain:

```text
ref\loinc.csv
```

This established that:

- backend folder discovery worked
- run creation worked
- DuckDB persistence worked
- failed-run history was visible in Streamlit
- evaluator initialization correctly surfaced the missing local dependency

### Attempt 2 — successful end-to-end run

After supplying the local LOINC reference file, the same regression folder completed successfully.

Run ID:

```text
run-19b0cd86-1499-4dc9-ab42-da89f70167ae
```

Summary:

- status: `COMPLETE`
- files: **5**
- messages: **1,000**
- overall mean PIQI: **77.14907**
- critical failures: **0**
- elapsed: **4.658 seconds**

Per-file results:

| File family | Type | Messages | Mean PIQI | Critical fails | Seconds |
|---|---|---:|---:|---:|---:|
| ADT | ADT^A01 | 200 | 88.24 | 0 | 0.362 |
| DFT | DFT^P03 | 200 | 66.67 | 0 | 0.107 |
| ORM | ORM^O01 | 200 | 100.00 | 0 | 0.044 |
| ORU | ORU^R01 | 200 | 34.12 | 0 | 0.978 |
| ORU_LABS | ORU^R01 | 200 | 96.72 | 0 | 0.441 |

Detailed NDJSON artifacts were written per input file and run-level JSON/Markdown summaries were produced.

## Semantic equivalence result

The backend execution path reproduced the known PIQI behavior of the existing small-run workflow:

```text
ADT       88.24
DFT       66.67
ORM      100.00
ORU       34.12
ORU_LABS  96.72
```

This is the primary WAP_AS smoke-test invariant:

> **The execution infrastructure changed; PIQI scoring semantics did not.**

## Current next step

Run the large MediLacra benchmark through **Backend path**, especially the files that could not fit through the Streamlit uploader:

- DFT approximately 200 MB
- ORU approximately 600 MB

The purpose of the next run is to move the scale boundary past the UI and observe the actual backend constraints: parser, converter, evaluator, memory, and artifact-writing behavior.
