# PIQITT 2.0 — Engineering Documentation

This directory is the working record for PIQITT 2.0 consolidation and enhancement on the `piqitt-2.0` branch of the original `natosit-dev/piqitt` repository.

## Planning baseline

- [Gap analysis and phased build plan — v0.4](PIQITT_2.0_GAP_ANALYSIS_BUILD_PLAN_v0.4.md) — approved review draft imported from the original Word document on 2026-11-08. Includes topology comparison, standard run package, scope, phases, tests, raw prompts and decision log.
- [Build work log](WORK_LOG.md) — chronological evidence of repository inspection, implementation, tests and decisions.
- [E-00 source freeze and capability inventory](E00_BASELINE_FREEZE_AND_CAPABILITY_INVENTORY.md) — inspected source map, executed original-converter smoke baseline, historical evidence, blocked tests and explicit exit gates.
- [Source import manifest](SOURCE_IMPORT_MANIFEST.json) — machine-readable pinned donor revisions, selected Git blob hashes, licensing observations and test artifacts.
- [E-00 frozen converter baseline](baselines/e00_converter_smoke_summary.json) — normalized outputs for 4 synthetic v2 messages; input fixture at `../tests/fixtures/e00/hl7_smoke_messages.hl7` and repeatable tests at `../tests/test_e00_converter_baseline.py`.

## Documentation conventions

- Record the date, branch/commit, action taken, observed result, test evidence, and next step for every substantive build increment.
- Distinguish **historical reported results**, **source inspection**, and **locally executed verification**.
- Append new build notes rather than rewriting earlier observations.
- Keep source-import provenance (donor repo/ref/SHA and file identity) when modules are harvested.
- Treat the plan as a versioned baseline; document intentional changes rather than silently altering the original version.
- Preserve raw user prompts or links to their redacted provenance when changes materially arise from them.

**Status:** E-00 partially complete. The original converter smoke corpus has been run (5/5 tests), and source/donor revisions are documented. Full core, SaSI, WAP_AS, official-PIQI and IRIS runtime baselines remain pending; see the E-00 report. No application code or donor modules have been changed or imported.
