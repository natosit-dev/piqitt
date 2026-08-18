# PIQITT WAP_AS Build Notes

**Branch:** `WAP_AS`  
**Date:** 2026-08-18  
**Status:** Initial implementation complete; ready for local runtime validation

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

## Validation performed before publish

- Python syntax compilation passed for the new runner, repository, CLI, UI source, and tests in the available execution environment.
- Streaming harness confirmed CR-delimited HL7 files split correctly across `MSH|` boundaries without reading the complete file at once.
- Folder-discovery harness confirmed sorting, `.hl7` / `.txt` filtering, and non-recursive behavior.
- Failure-continuation harness exercised three files in order:
  - first file: `COMPLETE`
  - second file: forced `FAILED`
  - third file: `COMPLETE`
- The run correctly continued after the failed middle file, preserved two successful message results, and ended with overall status `FAILED`.

## Runtime validation still required

The build environment used for implementation does not have Streamlit or DuckDB installed and cannot reach PyPI, so the actual DuckDB-backed Streamlit run was not executed here.

The first local validation should therefore be deliberately small before feeding WAP_AS the 600 MB ORU:

```powershell
pip install -r requirements.txt
streamlit run piqitt.py
```

Then select **Backend path**, point it at a small known benchmark folder, and compare PIQI values against the existing upload-path baseline.

Expected invariants for the known MediLacra benchmark include:

```text
ADT       88.24
ORM      100.00
ORU_LABS  96.72
```

If those change for identical source data and profiles, treat it as a WAP_AS regression before doing the large run.
