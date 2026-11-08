# PIQITT 2.0 — Work Log

## 2026-11-08 — Branch and documentation initialization

**Repository:** `natosit-dev/piqitt`  
**Branch:** `piqitt-2.0`  
**Base:** original `main` at `a40300e4950d73ed192a2112cf516b4ec46a184b` (verify against Git history during E-00)  
**Scope:** planning/provenance only; no application code edits.

### Actions

- Created a dedicated `piqitt-2.0` branch to consolidate existing PIQITT components without modifying original `main` or historical experimental branches.
- Converted `PIQITT_2.0_Full_Gap_Analysis_and_Build_Plan_v0.4_2026-11-08.docx` to a Markdown planning baseline under `docs/`.
- Initialized a documentation index and this chronological work log.

### Validation

- Confirmed the plan exists on the new branch and retains the full capability gap analysis, raw prompt appendix, and final decision-log appendix.
- No runtime tests or IRIS operations were performed for this documentation initialization.

### Next gate: E-00 baseline freeze

Record exact source SHAs, inventory candidate modules/fixtures, verify source licenses and dependencies, and capture reproducible historical execution controls before importing or changing runtime behavior.

## 2026-11-08 — E-00 source freeze and minimal executable control

**Branch:** `piqitt-2.0`  
**Reference base:** `main@a40300e4950d73ed192a2112cf516b4ec46a184b`  
**Status:** PARTIAL; original converter baseline reproduced, donor workflows not rerun.

### Actual operations and source evidence

- Enumerated and pinned original, SaSI, WAP_AS, official-reference, PIQITT Connect, contest, development and MediLacra donor revisions and selected source file blob SHAs in `docs/SOURCE_IMPORT_MANIFEST.json`.
- Inspected documented entry points, dependency specifications, root licenses, and test functions. Recorded the source inventory and gaps in `docs/E00_BASELINE_FREEZE_AND_CAPABILITY_INVENTORY.md`.
- Attempted `git clone --depth 1 --branch piqitt-2.0 https://github.com/natosit-dev/piqitt.git` from the isolated execution sandbox; it failed due to DNS resolution (`Could not resolve host: github.com`). GitHub source inspection instead used an authorized repository connector.
- Confirmed local original `fhir_convert_backend.py` has Git blob SHA `fe7709fd217f5316239e844cc85f77530c441a76`, identical to the source on original `main`, `sasi`, and `WAP_AS`.
- Authored a synthetic 4-message input fixture and its normalized converter output control without modifying `scripts/fhir_convert_backend.py`.
- Ran `python -m unittest discover -s tests -p 'test_e00_*.py' -v` in a temporary test workspace with the byte-identical original converter: **5 checks passed, 0 failed** using Python 3.13.5. A `datetime.utcnow()` deprecation warning was emitted.
- Committed the input fixture, expected summary, reproducible regression tests and E-00 documentation to the development branch.

### Critical observations

- ADT CWE yielded `Observation.valueString` in the pinned original converter. This remains a historical negative control, not a proposed correct mapping.
- ORU NM and CE retained their respective Quantity and CodeableConcept shapes under the source-specific smoke fixture.
- DFT FT1 became a minimal Claim; semantic appropriateness has not been independently validated.
- Unsupported ORM produced a fallback Bundle with MessageHeader and Patient but no order resource. No current local PIQI score was measured; a historically recorded ORM 100% result remains a distinct unverified scorer claim.
- `piqitt-contest/requirements.txt` contains unresolved conflict markers. It is not a viable install manifest.
- Observed repository licenses vary (Apache-2.0, GPL-3.0, AGPL-3.0, GPL-2.0). Code reuse rights and final packaging are open decisions.

### Remaining evidence before E-00 completion

- Re-execute local PIQI assessment with exact reference files, profiles and outputs.
- Execute SaSI tests and, where available, the historical MediLacra 1,000-message corpus.
- Execute WAP_AS file-discovery/streaming tests and DuckDB backend regression; benchmark claims stay historical until rerun.
- Execute official PIQI adapter test path; confirm licenses and binding/endpoint limits.
- Verify IRIS connectivity and custom/FHIR read-back against the user's configured environment.
- Record exact Python, dependency, terminology and IRIS environment versions.

**No production behavior was changed or donor code imported in this milestone.** The E-00 release gate is not asserted complete.
