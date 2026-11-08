# E-00 Baseline Freeze and Capability Inventory

**Date:** 2026-11-08  
**Status:** PARTIAL - source inventory and minimal original-converter control verified; historical donor workflows not rerun  
**Branch:** `piqitt-2.0` (from `main` `a40300e4950d73ed192a2112cf516b4ec46a184b`)  
**Scope:** observation and evidence only; no application logic changed

## 1. Purpose and verification standard

Freeze what actually exists before consolidation. Separate (1) observed source/metadata, (2) locally executed controls, (3) reported historical findings, and (4) remaining unknowns. `docs/SOURCE_IMPORT_MANIFEST.json` pins observed candidate donor revisions and selected file hashes. **No donor source has been promoted into the new branch.**

Repository visibility and GitHub API reads succeeded. A direct `git clone` from the sandbox failed with `Could not resolve host: github.com`; therefore full repository-local test suites and running IRIS were not available in this execution environment. A supplied original converter source file was available locally and its Git blob hash **exactly matched** the pinned original-main converter.

## 2. Source topology and entry points

| Source | Observed entry points / modules | Primary capability | Reproduction status |
|---|---|---|---|
| `piqitt/main` | `piqitt.py`; `scripts/fhir_convert_backend.py`, `scripts/piqi_eval.py`; YAML configs; scorecard/export scripts | Interactive HL7 v2 conversion, local PIQI scorecard | **Partial executed:** converter only; Streamlit/evaluator not run |
| `piqitt/sasi` | `scripts/sasi_run.py`, `sasi_analyzer.py`, `sasi_sams.py`, `sasi_summary.py`; `tests/test_sasi.py` | Source-v2 to FHIR preservation checks | **Source inspected**, 7 test functions present, not executed |
| `piqitt/WAP_AS` | `scripts/wap_cli.py`, `wap_runner.py`, `run_repo.py`, `testing/test_wap_runner.py` | Streaming HL7 file/folder processing, NDJSON, DuckDB catalog | **Source inspected**, 3 test functions present, not executed |
| `piqitt/experiment/official-piqi-artifacts` | `scripts/piqi_reference.py`; `reference/piqi/*.json`; `tests/test_piqi_reference.py` | Preliminary FHIR-to-PIQI adapter and official rubric/SAM assets | **Source inspected**, 4 test functions present, not executed; no official endpoint parity claim |
| `piqitt_connect/main` | `piqitt.py`, `pages/2_IRIS_Connect_Demo.py`, `lib/{fhir_convert_backend,piqi_eval}.py`, generation scripts, Docker Compose | Shared demonstration of conversion/scoring, synthetic generation, IRIS custom REST and FHIR client | **Source inspected**, IRIS not run |
| `piqitt-contest/main` | `app.py`, `scripts/*.py`, `lib/*.py`, `docker-compose.yaml` | Prior contest HL7 to FHIR to PIQI to IRIS pipeline | **Historical reference** only; `requirements.txt` contains unresolved Git conflict markers |
| `piqitt_dev/main` | `piqitt.py`, `pages/1_FHIR_Viewer.py`, `tests/test_fhir_convert_backend.py` | Earlier interface, FHIR client and converter tests | **Source inspected**; 2 test functions found, not executed |
| `medilacra_connect` | `connectathon/fhir_control.py`, `provenance.py`, `piqitt_bridge.py`; endpoint feature's `piqi_execution.py` | Synthetic control, mutation, endpoint evidence | **Historical reference / adapter candidate** |
| `medilacra_fhir_engine/main` | `src/`, `apps/`, `pyproject.toml` | Synthetic reality/domain engines and linked application shell | **External integration candidate**, not imported |

Source tree counts are *file inventory counts*, not LOC, feature-completion, or executable coverage. The full selected-hash list is in the machine-readable import manifest.

### Canonical-candidate selection remains open

The original main, SaSI, and WAP_AS share byte-identical converter blob `fe7709fd217f5316239e844cc85f77530c441a76` and evaluator blob `1315e2da2c6cf157f4a16b2e116f8312ee054f4e`. `piqitt_connect` has newer **different** converter/evaluator blobs (`122b9f2fe24052dc068efd689da8e4d7e06d831b` and `67bad5cf5ce236358df63b87576e44444f1841ca`). Do not choose by recency; run behavioral parity and negative controls first.

## 3. First executed smoke corpus (exactly pinned original converter)

Four synthetic HL7 v2 messages are in `tests/fixtures/e00/hl7_smoke_messages.hl7`. Frozen deterministic shapes are in `docs/baselines/e00_converter_smoke_summary.json`. Both are reproducible through `tests/test_e00_converter_baseline.py`.

| v2 message | Observed converter output | Intent |
|---|---|---|
| ADT^A01 | MessageHeader, Patient, Encounter, Observation; CWE Observation becomes `valueString` | Preserve known coded-value defect for later remediation |
| ORU^R01 | MessageHeader, Patient, Encounter, DiagnosticReport, 2 Observations; NM -> Quantity, CE -> CodeableConcept | Baseline one numeric and one coded Observation |
| DFT^P03 | MessageHeader, Patient, Encounter, Claim | Preserve legacy FT1-to-Claim behavior; correctness not inferred |
| ORM^O01 | MessageHeader + Patient only; no order resource | Negative control for unsupported mapping; this test does **not** verify PIQI score gating |

**Actual execution:** 5/5 `unittest` checks passed on Python 3.13.5 against the locally available original converter file, verified by `git hash-object` as `fe7709fd217f5316239e844cc85f77530c441a76`. The tests use structural summaries, not random FHIR resource UUIDs or wall-clock timestamps. Runtime observed a `datetime.utcnow()` deprecation warning. This smoke check does **not** prove FHIR R4 validity, PIQI scoring, semantic fidelity, IRIS integration, SaSI correctness, or benchmark scale.

```bash
python -m unittest discover -s tests -p 'test_e00_*.py' -v
```

Input SHA-256: `c3b0780a9804120f05c988665f0594f1c953bd08fd8373b4606703f8b31e8edd`  
Expected summary SHA-256: `fa8dd56df00b767f162b87d79bb8d39c2b649b3c4700b7705c9f04c1c9f9c448`

## 4. Historical evidence not independently rerun

- WAP_AS's August 19, 2026 note records 5 files, 1,000 messages, 4.658 seconds, aggregate PIQI 77.14907, and 0 critical failures **after** a missing local `ref/loinc.csv` file was supplied. The baseline is historical, not re-verified here; results depend on local reference data and configuration.
- SaSI's August 19, 2026 report describes 1,000 messages across ADT, DFT, ORM and ORU. A `tests/test_sasi.py` module exists with 7 named tests, but no SaSI code was executed in this E-00 pass. It remains investigational.
- MediLacra PIQI Connectathon records an accepted local control/mutation workflow but explicitly says external PIQI evaluation was **NOT_RUN**.
- Original WAP_AS reports an **ORM PIQI 100%** historical result. The E-00 converter confirms that the original ORM mapper falls back to MessageHeader + Patient; a strict scoring/applicability test remains outstanding.

## 5. Dependency and reference-data availability

| Component | Declared or observed dependency | Observed readiness |
|---|---|---|
| Original main | No tracked pinned dependency lockfile identified; Streamlit, pandas, PyYAML, etc. imported | This sandbox lacks Streamlit; UI cannot run |
| WAP_AS | `requirements.txt`: streamlit, pandas, PyYAML, duckdb | Sandbox lacks DuckDB; runner/DB not tested |
| PIQITT Connect | `requirements.txt`: requests, PyYAML, Faker, Streamlit, pandas | CLI/UI+IRIS integration not executed |
| PIQI profiles and terminology | YAML SAM/profile files; local LOINC/CPT and plausibility reference data | `ref/` is gitignored in the WAP_AS notes; clean checkout can fail preflight |
| Official PIQI references | JSON rubric/SAM assets and FHIR binding config | Assets inventoried; full rights, provenance and external scorer parity open |
| IRIS | Local IRIS Docker container, credentials and server endpoints | Not available/verified from this sandbox |
| GitHub clone | HTTPS repo access from execution sandbox | Failed DNS resolution; remote metadata obtained through authenticated connector |

Avoid installing ad-hoc terminology files from the internet and then claiming authoritative code membership. Pin versions, coverage, and license rights at integration.

## 6. Licensing and import guard

Observed root licenses: original `piqitt`, its branches, `piqitt-contest` and `piqitt_dev`: **Apache-2.0**; `piqitt_connect`: **GPL-3.0**; `medilacra_connect`: **AGPL-3.0**; `medilacra_fhir_engine`: **GPL-2.0**. These are file/repository observations, **not a legal conclusion** about compatibility or original author ownership.

Do not blindly copy a GPL/AGPL donor into Apache PIQITT; resolve intended distribution terms, licenses/rights and attribution before code import. Prefer narrow external adapter seams where ownership should remain separate. Official PIQI/HL7/terminology artifact rights need their own review.

## 7. E-00 gate / unresolved evidence

| Gate | Status | Evidence or blocker |
|---|---|---|
| Pin original main and known donor revisions | **PASS, scoped** | `SOURCE_IMPORT_MANIFEST.json`, GitHub branch/tree reads |
| Capture one exact original converter control | **PASS** | 4-message synthetic corpus, frozen outputs, 5/5 unittest checks |
| Inspect project entry points and known test modules | **PASS, source inventory** | Module/test inventory above |
| Reproduce existing local PIQI scorer on complete clean checkout | **NOT_RUN** | Source not fully checked out, local terminology files incomplete |
| Reproduce SaSI tests and 1,000-message claims | **NOT_RUN** | No full donor clone/runtime/fixtures |
| Reproduce WAP_AS tests, DuckDB catalog and bulk result | **NOT_RUN** | Missing DuckDB, donor code and corpus |
| Reproduce official PIQI bridge and endpoint parity | **NOT_RUN** | No installed donor/ref runtime; endpoint requires a separate FHIR-to-PIQI path |
| Reproduce existing IRIS demo and read-back | **NOT_RUN** | No reachable configured IRIS target |
| Confirm licenses/third-party artifact redistribution | **OPEN** | Mixed licenses and reference rights require explicit decision |
| Declare complete E-00 exit gate | **NOT YET** | Original core, SaSI, WAP_AS, IRIS and reference paths still lack independently rerun controls |

### Next step

Run the pinned versions on the intended Windows/WSL/Docker development workstation with complete local reference files and original regression datasets. Capture the actual commands, environment lock/version info, raw outputs and hashes, then update this log. **Do not silently mark E-00 complete and do not begin broad consolidation imports** until these missing baselines are either reproduced or explicitly accepted as documented exceptions.
