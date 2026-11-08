**PIQITT 2.0**

Full Repository Gap Analysis  
and Phased Build Plan

BRANCH-FIRST CONSOLIDATION \| ENGINEERING REVIEW v0.4

Proposed working branch: natosit-dev/piqitt / piqitt-2.0

Final packaging and repository topology: deliberately undecided

| **VERSION** | 0.4 \| Review draft                                                        |
|-------------|----------------------------------------------------------------------------|
| **DATE**    | 8 November 2026                                                            |
| **STATUS**  | Architecture and implementation proposal only; no repository modifications |

Baseline material: PIQITT 2.0 plan v0.3 (8 November 2026), Radiant Control engineering handoff v1.0 (8 November 2026), current user review notes, and repository source evidence.

Review purpose: approve the existing-capability consolidation, UI/core responsibility boundary, standard run evidence package, supported input policy, and test gates before implementation.

# Contents

Use these section links or the Word Navigation pane to review the plan. Section and appendix headings are structured for document navigation.

> **01** [<u>Decision summary</u>](#decision-summary)
>
> **02** [<u>Scope and guardrails</u>](#scope-and-guardrails)
>
> **03** [<u>Current repository inventory</u>](#current-repository-inventory)
>
> **04** [<u>Target architecture and ownership</u>](#target-architecture-and-ownership)
>
> **05** [<u>Full capability gap analysis</u>](#full-capability-gap-analysis)
>
> **06** [<u>Defect and technical-debt register</u>](#defect-and-technical-debt-register)
>
> **07** [<u>Contracts and evidence model</u>](#contracts-and-evidence-model)
>
> **08** [<u>Branch and source-import strategy</u>](#branch-and-source-import-strategy)
>
> **09** [<u>Phased build plan</u>](#phased-build-plan)
>
> **10** [<u>Regression and experimental test plan</u>](#regression-and-experimental-test-plan)
>
> **11** [<u>Release gates and stop conditions</u>](#release-gates-and-stop-conditions)
>
> **12** [<u>Risks, dependencies, and open decisions</u>](#risks-dependencies-and-open-decisions)
>
> **13** [<u>Review checklist</u>](#review-checklist)
>
> **14** [<u>Appendix A. Source and evidence ledger</u>](#appendix-a-source-and-evidence-ledger)
>
> **15** [<u>Appendix B. Requirements provenance</u>](#appendix-b-requirements-provenance-and-decision-history)
>
> **16** [<u>Appendix C. Change history</u>](#appendix-c-change-history)

17 Appendix D. Raw user prompts and review provenance

18 Appendix E. Decision log (latest; final section)

# 1 Decision summary

Recommendation: develop PIQITT 2.0 on a new piqitt-2.0 branch of the original natosit-dev/piqitt repository, using the existing repositories and experimental branches as evidence-bearing sources. Do not commit to the ultimate repository topology until the integrated prototype passes explicit acceptance gates.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>DECISION DELTA</strong></p>
<p>The 6 November v0.2 plan designated piqitt_connect as the long-term destination. The subsequent design discussion changed that recommendation: piqitt/piqitt-2.0 is the temporary consolidation and enhancement workbench. This document supersedes the earlier repository-selection decision only; it retains the technical requirements and historical evidence.</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

**The architectural thesis.** PIQITT should be an experimental laboratory for what survives healthcare data transformations, not merely a converter with a data-quality scorecard.

**The biggest gap.** No one working path yet connects an immutable MediLacra synthetic reality, independent native v2 and FHIR projections, v2-to-FHIR conversion, PIQI quality assessment, SaSI preservation tests, structural conformance and unified provenance.

**The practical conclusion.** Most infrastructure exists. Consolidation, source-of-truth discipline, conformance and data contracts matter more than writing another engine.

## 1.1 What is already established

• piqitt_connect already integrates a two-page Streamlit evaluator and an IRIS demonstration using shared converter/evaluator/configuration modules.

• SaSI already implements source-to-target preservation assertions and recorded a 1,000-message synthetic corpus analysis.

• WAP_AS already implements streaming execution, CLI, DuckDB run metadata and NDJSON artifacts; its 1,000-message smoke test is documented.

• The official PIQI-artifact branch already separates reference rubrics/SAM metadata from an experimental FHIR-to-PIQI binding adapter.

• MediLacra Connect already produces deterministic control and single-defect mutation artifacts with hashes and evidence packs.

• The original piqitt main, sasi and WAP_AS branches share byte-identical converter/evaluator blobs. piqitt_connect has a different, partly improved implementation.

## 1.2 What has not been established

• An integrated PIQITT 2.0 running all capabilities on the agreed branch.

• A stable, independently projected reality snapshot and a three-stage loss-attribution system.

• Full independent FHIR R4/profile validation on every declared supported mapping slice.

• End-to-end acceptance of native IRIS FHIR storage/read-back and official PIQI endpoint scoring.

• Reliable causal labels or held-out-family evaluation for later Random Forest research.

## 1.3 v0.4 review decisions and corrections

This revision adopts the Radiant Control handoff as the positive architecture direction and incorporates the owner’s subsequent clarifications. It does not authorize a new framework, a general defect hunt, or an immediate merge of donor branches. The source document remains intact as the basis for the full inventory and original phased plan.

• Thin UI means no domain-function implementations or duplicated workflow policy inside Streamlit. The UI may call canonical Python functions/services directly to set dials, accept file drops, start experiments and display results. An HTTP service layer is not required.

• Name both source standards correctly: HL7 v2 and HL7 FHIR R4 are both HL7 standards and both are accepted input families. Synthetic reality is an additional optional input type.

• Make ExperimentRun the durable experiment/evidence boundary; define a portable run package and companion DuckDB index before joining independent engines.

• Resolve unsupported ORM^O01 before trusting any aggregate score. Legacy 100% PIQI remains a historical artifact, not a valid conformance or conversion outcome.

• Place SaSI and WAP_AS on distinct, deliberately modest Experiments pages. SaSI is investigational until independently exercised and its assertions validated; WAP_AS has stronger operational precedent, but still needs a pinned parity run after import.

• Keep phase ordering: preserve/consolidate, prove backend parity, then stabilize semantics, then extend controlled-reality and standards coverage.

# 2 Scope and guardrails

## 2.1 Scope retained from the November 6 plan

• Consolidate first; inventory, preserve and connect existing code before materially changing behavior.

• Convert PIQITT-owned run/profile configuration from YAML to versioned, schema-validated JSON with measured parity. Keep executable semantic mapping logic in code.

• Use pinned HL7 v2-to-FHIR mapping references and official PIQI artifact formats. Respect the separate FHIR-to-PIQI model adaptation boundary.

• Support FHIR R4 4.0.1 and a precisely declared HL7 v2 input slice, not universal HL7 v2-to-FHIR coverage.

• Generate native FHIR directly from the same synthetic reality that also produces native HL7 v2; do not round-trip the control through v2.

• Make IRIS connectivity a built-in optional adapter while preserving a fully offline execution path.

• Retain old defective cases as negative controls and only repair behavior after the initial parity baseline is captured.

• Defer Random Forest / meaning-loss inference until the semantic labels and lineage are independently defensible.

## 2.2 Initial supported slice and exclusions

Initial interoperability input: HL7 v2.5-style MediLacra ADT^A01, ORU^R01 and DFT^P03 messages, with a pinned local message profile and regression fixtures. ORM^O01 remains a deliberately unsupported negative control until ServiceRequest/order semantics are intentionally implemented. New input families require an explicit support-matrix change.

FHIR R4 resource targets should include Patient, Encounter, Observation and DiagnosticReport where source semantics justify them; charge events should be assessed for ChargeItem versus true Claim semantics. Bundle packaging, references, coded values, UCUM, and temporal precision are in scope. Coverage, PractitionerRole, orders and more elaborate payer data enter only as source facts and profiles are demonstrated.

Not in first tranche: universal HL7 v2 support, FHIR-to-v2 reverse mapping, a complete MPI, wholesale MediLacra import, a new web framework, real PHI, a hosted multi-user service, formal conformance certification, or a predictive model.

## 2.3 Meaning and evidence discipline

**FHIR valid is not meaning preserved.** Structural/profile conformance, PIQI quality, SaSI semantic retention and transport outcomes are separate assessment channels.

**Synthetic reality is the controlled reference.** It supplies generated ground truth for the experiment, not proof that the data reflects clinical reality.

**Unsupported is not PASS.** Missing resources, unbound official PIQI criteria and unavailable terminology must remain explicit non-success states rather than being silently excluded from reassuring summary scores.

**Evidence outlives UI.** Run identity, source revisions, configs, fixtures, observed outputs and failure reproduction must be navigable without Streamlit or IRIS.

# 3 Current repository inventory

Classification below distinguishes implementation verified by code inspection from results reported in existing project documentation. Recorded historical outcomes have not been rerun for this review.

| **Source / branch**                                 | **Established capability**                                              | **Recommended use**                                        | **Evidence status**                              |
|-----------------------------------------------------|-------------------------------------------------------------------------|------------------------------------------------------------|--------------------------------------------------|
| piqitt / main                                       | Original converter, YAML PIQI evaluator, scorecards                     | Working branch base; preserve legacy behavior              | Code inspected                                   |
| piqitt / sasi                                       | 10 preservation SAMs; source/target inventories; 1,000-message findings | Selectively import semantic engine + tests                 | Code + recorded run                              |
| piqitt / WAP_AS                                     | Streaming file runner; CLI; DuckDB catalog; NDJSON                      | Import execution/catalog modules                           | Code + recorded run                              |
| piqitt / experiment/official-piqi-artifacts         | USCDI V2/V3 reference rubrics, SAM metadata, FHIR bindings              | Import as separate experimental PIQI path                  | Code inspected                                   |
| piqitt_connect / main                               | Two-page UI; common core; custom IRIS REST; FHIR POST helper            | Import selected newer implementations and UI               | Code + recorded local baseline                   |
| piqitt-contest / main                               | Early synthetic HL7 \> FHIR \> PIQI \> IRIS pipeline                    | Historical regression specimens                            | Documentation + code lineage                     |
| medilacra_connect / integrate/piqi-43               | Controlled baseline, one-defect mutations, SHA manifests                | External experiment adapter; preserve evidence             | Code docs + local acceptance                     |
| medilacra_connect / feature/piqi-endpoint-execution | Endpoint transport and pairwise response comparisons                    | Optional endpoint adapter; separate from PIQI validation   | Implementation branch; no live acceptance proven |
| medilacra_fhir_engine / main                        | Deterministic models, FHIR/ePA payload builders and test scenarios      | Possible snapshot/rendering interface, not wholesale merge | Harvest docs + limited offline tests             |
| piqitt_dev / main                                   | Older private experimental variant                                      | Reference and historical comparisons only                  | Repository inspected                             |

## 3.1 Exact reuse and divergence observations

GitHub blob SHA comparison shows the main, sasi and WAP_AS branches in the original piqitt repository have byte-identical versions of both scripts/fhir_convert_backend.py and scripts/piqi_eval.py. Import SaSI and WAP_AS as additional services, not their duplicate copies of the core.

The piqitt_connect implementation is distinct: its MessageHeader includes endpoint fields and its evaluator returns complete detail records. It also includes an optional FHIR transaction-post helper. That implementation should be evaluated for promotion into the new branch by explicit golden comparisons, rather than blindly replacing original-main behavior.

## 3.2 Historical experimental results worth preserving

| **Evidence source**            | **Recorded result**                                                                 | **Interpretation / limitation**                                            |
|--------------------------------|-------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| SaSI, 19 Aug 2026              | 1,000 messages: 200 ADT, 200 DFT, 200 ORM, 400 ORU                                  | Experimental record; not a fresh execution                                 |
| SaSI, 19 Aug 2026              | 9,038 source and target Observation codes retained in sampled corpus                | Cardinality/code survival does not establish value fidelity                |
| SaSI, 19 Aug 2026              | 600 coded source values; zero retained as coded target values                       | Known semantic-structure loss signal on older converter                    |
| SaSI, 19 Aug 2026              | 200 ORM messages marked unsupported                                                 | Deliberate negative control                                                |
| WAP_AS, 19 Aug 2026            | 1,000 messages across five files; 4.658 seconds; mean PIQI 77.14907                 | Local smoke benchmark, not scale proof                                     |
| WAP_AS, 19 Aug 2026            | 200 unsupported ORM messages averaged PIQI 100                                      | Demonstrates unsupported conversion can coexist with high apparent quality |
| MediLacra PIQI-43, 11 Sep 2026 | One baseline + deterministic single-path mutants; zero-delta control; SHA manifests | Local acceptance; external PIQI evaluation not executed                    |

## 3.3 Source-of-truth caution

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th><p><strong>DO NOT OVER-MERGE</strong></p>
<p>One codebase may expose one user-facing application without absorbing every source repository. Keep MediLacra responsible for generating synthetic reality; keep PIQITT responsible for mapping, comparison, assessment, conformance, evidence and optional transport.</p></th>
</tr>
</thead>
<tbody>
</tbody>
</table>

## 3.4 Original PIQITT topology versus the consolidated topology

The original piqitt/main topology is an in-process Streamlit application that directly invokes parsing, conversion and evaluation functions, loads YAML/CSV reference configuration, and prepares scorecard exports. This is a workable interactive tool, not an invalid design. Separate branches and applications later acquired batch persistence (WAP_AS), transformation analysis (SaSI), official-reference experiments and IRIS integration. The problem is fragmentation and duplicate orchestration, not the fact that Streamlit invokes Python.

| **ORIGINAL PIQITT (main)**                                                             | **PIQITT 2.0 (proposed)**                                                                                        |
|----------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| Streamlit UI: file upload, user controls, scorecard display, exports                   | Streamlit thin pages: inputs and dials, service calls, progress, results and downloads                           |
| UI calls HL7 split/convert functions, evaluator, reference loading and export assembly | CLI and UI call same core library / ExperimentRun service; pure function calls remain allowed                    |
| HL7 v2 -\> FHIR Bundle -\> local YAML-driven PIQI score                                | HL7 v2 OR FHIR R4 -\> stage-based analysis; optionally one synthetic RealitySnapshot -\> independent projections |
| SaSI, WAP_AS, official PIQI adapter and IRIS live on other branches/repos              | SaSI, WAP_AS, PIQI reference and optional IRIS are coordinated as typed run stages / experiment pages            |
| Run outputs are UI files or module-specific artifacts                                  | Standard evidence package + derived DuckDB catalog, with immutable inputs and stage output references            |

> ORIGINAL piqitt/main TARGET piqitt-2.0  
> Streamlit (upload / score / export) Streamlit pages \| CLI / tests  
> \| \|  
> +--\> v2 parse --\> FHIR --\> PIQI +--\> Python core / RunService  
> \| \| +--\> input: v2 / FHIR / reality  
> +--\> YAML / CSV reference ---+ +--\> convert / PIQI / SaSI / validate  
> +--\> download scorecard +--\> optional IRIS adapter  
> +--\> evidence files + DuckDB index

A strict “UI cannot call converter functions” rule would be excessive. The correct test is whether the interpretation and orchestration logic lives in canonical reusable modules and behaves the same under Streamlit, CLI and tests. A direct call to a canonical library function from Streamlit is acceptable; redefining its clinical logic, mappings, retries or persistence behavior in the page is not.

Source basis: original piqitt/main piqitt.py, scripts/fhir_convert_backend.py and scripts/piqi_eval.py; separate piqitt/sasi and piqitt/WAP_AS; and piqitt_connect/main piqitt.py plus pages/2_IRIS_Connect_Demo.py. This is a comparison of documented/source-observed topologies, not a fresh end-to-end benchmark.

# 4 Target architecture and ownership

The same immutable synthetic reality is the root of two independent representation paths. External HL7/FHIR can also be assessed without claiming a reality-based baseline when none was supplied.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th>MediLacra generated reality (one immutable snapshot, one run ID)<br />
| |<br />
v v<br />
native HL7 v2 projection native FHIR R4 projection<br />
| |<br />
v |<br />
PIQITT v2 -&gt; FHIR R4 converter |<br />
| |<br />
+-------------------+-----------------------+<br />
|<br />
preservation / comparison<br />
+------------------+<br />
| |<br />
PIQI quality SaSI fidelity<br />
| |<br />
+---- FHIR R4 validation ----+<br />
|<br />
immutable evidence + DuckDB run catalog<br />
|<br />
Streamlit / CLI / optional IRIS FHIR<br />
|<br />
supervised research (later)</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

## 4.1 Separation of responsibility

| **Owner / component**       | **Owns**                                                                              | **Explicitly does not own**                                   |
|-----------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------------|
| MediLacra                   | Synthetic fact generation, seeds, entities, relationships, narrative/scenario reality | PIQI scoring, semantic assessment, IRIS test verdicts         |
| PIQITT / reality adapter    | Snapshot contract, source identifiers, generator version, non-mutating reader         | Independent invented clinical facts                           |
| PIQITT / mappings           | v2 parsing, native FHIR construction, mapping registry, source-to-target derivation   | Hidden best-effort semantic repairs with no recorded evidence |
| PIQITT / assessment         | Local/official PIQI adapters, SaSI, structural conformance, typed findings            | Conflating HTTP success with clinical-data quality            |
| PIQITT / runtime            | CLI and UI, streaming execution, run ledger, artifacts, optional IRIS                 | Making a live server mandatory for offline tests              |
| Research notebook / package | Observed labels and held-out predictive experiments                                   | Inferring root cause solely from model feature importance     |

## 4.2 Three transformation opportunities

For every fact, the comparison should distinguish: (1) reality -\> HL7 v2 projection, (2) HL7 v2 -\> derived FHIR, and (3) reality -\> independent native FHIR. Without these three boundaries, a missing fact in both outputs might be incorrectly blamed on the converter rather than on source projection or incomplete synthetic reality.

**Independent rendering rule.** Both renderers read an unchanged snapshot. Rendering cannot recalculate an HbA1c, change an encounter state or create an unrecorded insurer simply to satisfy a target schema.

**Equivalence rule.** Compare semantically meaningful facts and relationships, not raw JSON, array order, resource IDs or serialization bytes alone.

## 4.3 Thin-client policy and experiment navigation

The UI is where a person chooses input files, endpoints, test profiles, settings and execution modes; initiates runs; watches progress; browses findings; and downloads evidence. This is intentional, not a design smell. All substantive healthcare or experiment behavior belongs in canonical Python modules. Streamlit and CLI may import/call those modules without an intermediary HTTP server.

| **UI MAY DO**                                                              | **CORE LIBRARY MUST DO**                                                                                 |
|----------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| Drop/browse files, choose v2/FHIR input, select profiles and set dials     | Parse source formats, determine supported mappings and validate run specifications                       |
| Call run(), convert(), assess() or query methods from canonical modules    | Implement conversions, SAMs, semantic comparisons, applicability and score math                          |
| Choose optional IRIS target and request a transport stage                  | Build HTTP(S) requests, redact and persist exchanges, retry/read-back, record transport status           |
| Render tables, plots, filters, progress, JSON explorers and download links | Create immutable evidence artifacts, run manifests, hashes, NDJSON, standard exports and DuckDB metadata |
| Control which Experiment page is visible and start/inspect run IDs         | Enforce consistent semantics whether invoked by Streamlit, CLI, tests or notebooks                       |

Proposed minimal navigation: Inspect & Score (HL7 v2 or FHIR R4); Experiments \> SaSI (clearly marked experimental); Experiments \> WAP_AS (batch/corpus); IRIS Connect (optional transport and read-back); Run Browser (history, artifacts and comparisons). Pages can begin as thin wrappers around existing modules, with no visual redesign. WAP_AS does not become a separate computational engine just because it has a separate page.

Acceptance invariants: no st.\* imports in domain/core modules; no duplicated mapping/SAM definitions in pages; CLI and UI yield equivalent normalized outputs on pinned fixtures; Streamlit reruns cannot silently duplicate submitted runs; offline assessment works with IRIS unavailable; large-corpus handling does not require browser upload or in-memory concatenation.

# 5 Full capability gap analysis

Priority: P0 foundational correctness/architecture; P1 essential integration/hardening; P2 later consolidation/extension; P3 deferred research. Status describes the reviewed sources, not certification of deployed behavior.

## 5.1 Capability matrix

| **ID / priority** | **Existing implementation**                                      | **Gap to 2.0**                                               | **Required action / gate**                                                                                            |
|-------------------|------------------------------------------------------------------|--------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------|
| G01 / P1          | Two-page UI in piqitt_connect                                    | Not running from piqitt-2.0                                  | Selective UI import; one shared API                                                                                   |
| G02 / P0          | Multiple old/new converter copies                                | Behavioral source of truth unresolved                        | Choose canonical converter by parity tests                                                                            |
| G03 / P0          | Local PIQI evaluator; YAML profiles                              | Scoring applicability and effect correctness                 | Typed result states; scoring tests                                                                                    |
| G04 / P0          | SaSI branch, 10 source-target assertions                         | Index-based matching; no reality-level comparison            | Stable fact matching; relation fidelity                                                                               |
| G05 / P1          | WAP_AS runner and DuckDB                                         | Disconnected from destination core                           | Use common executor and run ledger                                                                                    |
| G06 / P1          | Official PIQI artifacts experiment                               | Incomplete entity bindings and SAM semantics                 | Preserve official JSON; expand adapter                                                                                |
| G07 / P0          | MediLacra data/models                                            | No single PIQITT immutable snapshot                          | Versioned read-only reality contract                                                                                  |
| G08 / P0          | FHIR/ePA builders in MediLacra                                   | Independent native clinical FHIR route not proven            | Direct FHIR projection for declared slice                                                                             |
| G09 / P0          | HL7 and FHIR conversion paths                                    | No stage-specific fact-loss attribution                      | Fact/relationship preservation ledger                                                                                 |
| G10 / P0          | Simplified ADT/ORU/DFT conversion                                | Incomplete field and event semantics                         | Mapping coverage registry and cases                                                                                   |
| G11 / P0          | Local FHIR preflight                                             | Independent R4/profile validation incomplete                 | External validator with pinned profiles                                                                               |
| G12 / P1          | YAML local configuration                                         | Versioned JSON/schema/parity missing                         | Dual-load, JSON default after parity                                                                                  |
| G13 / P1          | LOINC/CPT partial local reference                                | Authority, coverage, version/rights unclear                  | Terminology manifest + UNAVAILABLE states                                                                             |
| G14 / P1          | Connectathon deterministic mutants                               | Separate mutation/evidence model                             | Adapter into shared experiment identity                                                                               |
| G15 / P1          | Custom REST + Python FHIR POST                                   | Native IRIS read-back/validation not proven                  | Optional native FHIR integration tests                                                                                |
| G16 / P1          | Multiple output formats and score scales                         | No canonical evidence envelope                               | Typed results + scale/version contract                                                                                |
| G17 / P2          | App/browser + CLI in separate sources                            | No common operation contract                                 | Shared service functions; CLI/UI parity                                                                               |
| G18 / P3          | Historical statistical comparisons                               | No research labels/holdout design                            | Feature/label specification after gates                                                                               |
| G19 / P0          | HL7 v2 accepted; FHIR R4 accepted indirectly as derived output   | Direct FHIR R4 file/Bundle input and independent assessments | Add typed input adapters and assess FHIR without requiring a v2 source; SaSI NOT_EVALUATED if no comparable source    |
| G20 / P0          | Original UI and IRIS demo contain orchestration/HTTP/export code | Presentation vs domain logic boundary                        | UI can call core functions directly; remove implemented transformations/transport/evidence logic from pages           |
| G21 / P0          | WAP_AS DuckDB and MediLacra evidence packs differ                | Portable run artifact standard                               | Standard run folder + manifest + SHA index + JSON/NDJSON + run DuckDB derivative + optional HTTP(S) exchange evidence |
| G22 / P0          | Historical ORM fallback scored 100% PIQI                         | Preflight and coverage guard                                 | ORM conversion explicitly UNSUPPORTED; derived-PIQI not executed by default and numeric score null, not 0 or 100      |
| G23 / P1          | SaSI and WAP_AS are distinct source experiments                  | Separate thin Experiments pages and proof gates              | SaSI treated investigational; WAP_AS regression/scale evidence preserved; both use shared core                        |

## 5.2 P0: correctness and meaning-preservation gaps

**G02 + G03 - canonical core and assessment semantics.** Promote one tested converter and evaluator. Preserve scores and details from historic fixtures before fixes. Distinguish SCORING from INFORMATIONAL checks; when a profile did not evaluate its required subjects, expose coverage and NOT_EVALUATED rather than inventing a perfect score.

**G04 + G09 - fact matching and provenance.** Replace observation-array positional pairing with stable semantic keys (subject, encounter, source ID, code/system, effective time, instance ID where supported). Ambiguous matches must return AMBIGUOUS, not a fabricated correspondence. Derive stage-specific losses only when source and target anchors support them.

**G07 + G08 - reality model and direct FHIR.** Define an immutable snapshot with fact IDs, relationship IDs, missingness, temporal precision and version provenance. Reuse the MediLacra model and FHIR engine where appropriate; do not make the converter itself generate synthetic data.

**G10 + G11 - mapped/conformant supported slice.** Pin a specific HL7 v2 profile and official mapping references. Register supported, partial, unsupported and inapplicable source elements. Independently validate every supported R4/profile fixture. Test message Bundle and resource semantics independently.

## 5.3 P1: disconnected capabilities

**G05 - WAP_AS.** Reuse its streaming reader, CLI, run repository and NDJSON rather than replacing them with Streamlit loops. Add an executor abstraction that accepts structured or raw input and records consistent run IDs and exceptions.

**G06 - official PIQI.** Preserve USCDI V2/V3 JSON rubrics and official SAM metadata unchanged. The FHIR-to-PAT_CLINICAL_V1 adapter is separate and partial: expose UNBOUND/UNSUPPORTED; do not equate the local YAML-derived quality index with an official PIQI reference-service outcome.

**G12 + G13 - config and terminology.** Migrate only PIQITT-owned configuration to schema-validated JSON with dual-read parity; do not rewrite official rubrics. Capture reference-set versions, file hashes and licenses. A code absent from a small local CSV may be UNKNOWN rather than invalid.

**G14 - mutations.** Reuse the zero-delta control and exactly-one-declared-change pattern from MediLacra Connect. Capture before/after paths, baseline hash, mutant hash, expectation, observed result and endpoint response separately.

**G15 + G16 - IRIS and typed evidence.** Retain custom REST and offline mode while adding native R4 storage/read-back tests. Store data-quality, structural, semantic and transport outcomes as separate fields, with consistent percent score scales and legacy 0..1 compatibility.

## 5.4 P2/P3: explicitly deferred

UI polish, large-volume benchmarks, expanded message families and predictive research should not block the first narrow reality-to-v2/FHIR experiment. There is already enough software to test the foundational theory with one patient, one encounter, and two observations.

# 6 Defect and technical-debt register

The register combines source-inspected current behavior, historical observations, and interpretation risks. A historical defect fixed in a newer repository is not counted as an unfixed defect in that repository.

| **ID / severity** | **Observed issue and source status**                                                                                                                                     | **Required regression / resolution**                                                                     |
|-------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------|
| B01 / Critical    | Evaluator skips steps when target resource is absent; unsupported ORM historically achieved high PIQI. Current piqitt_connect evaluator also skips missing target types. | Explicit UNSUPPORTED / NOT_EVALUATED / coverage counts. Never label an unassessed conversion successful. |
| B02 / High        | Current piqitt_connect evaluator increments score denominator/numerator for SAMs even when effect != Scoring.                                                            | Only Scoring affects score; informational steps stay visible and unweighted.                             |
| B03 / High        | SaSI checks pair source and FHIR Observations by array index.                                                                                                            | Reordering test must preserve fidelity verdict; wrong/ambiguous match explicitly flagged.                |
| B04 / High        | WAP_AS notes local LOINC reference was incomplete/informally sourced and ref/ files may be missing.                                                                      | Pin terminology version, hash, rights; distinguish unknown coverage from invalid member.                 |
| B05 / High        | FHIR-local reference resolution checks can PASS with a semantically wrong patient/encounter link.                                                                        | Compare links to source/reality entity identities; fail wrong-target even if reference resolves.         |
| B06 / Critical    | Unsupported message types take simplified fallback with a MessageHeader and possibly Patient.                                                                            | Supported-slice registry and explicit unsupported finding; ORM negative control retained.                |
| B07 / High        | Current piqitt_connect OBX builder maps CE to valueCodeableConcept, but CWE/CNE fall through to valueString.                                                             | Typed code/system/display/alternate handling for declared CE/CWE/CNE fixtures.                           |
| B08 / High        | Current piqitt_connect timestamp conversion can add Z to zone-less time and drop explicit offset.                                                                        | Preserve precision and explicit offsets; zone-less meaning must not be silently replaced.                |
| B09 / Critical    | Current Encounter.status is hardcoded finished; Observation.status is hardcoded final.                                                                                   | Map from source event/status where justified; explicitly record unmapped/unknown cases.                  |
| B10 / High        | FT1 charge data currently becomes a minimal Claim without verified claim context.                                                                                        | Determine ChargeItem/Claim by actual source semantics and R4 required elements; no fabricated claim.     |
| B11 / High        | Current homegrown PIQI YAML evaluation differs from official PIQI model/rubric contract.                                                                                 | Reference adapter with UNBOUND and UNSUPPORTED, official artifacts pinned; comparison tests.             |
| B12 / High        | Independent full R4/profile validation is not part of proven core flow.                                                                                                  | Run external validator, record warnings/errors and exact profile, never substitute local preflight.      |
| B13 / Medium      | Historical IRIS persisted some scores on 0..1 while Python uses 0..100.                                                                                                  | Versioned score unit; compatibility read for old rows; golden test of 70.59 vs 0.7059.                   |
| B14 / Medium      | Current bundle IDs/transport metadata and hardcoded endpoints are not a full provenance contract.                                                                        | Run identity, source hash, conditional config defaults, successful read-back evidence.                   |

## 6.1 Corrections to the earlier uploaded-file audit

The standalone uploaded piqi_eval.py was previously observed to reference undefined last-loop variables for empty input and to omit useful detail in its result. Current piqitt_connect/main lib/piqi_eval.py does not have those specific failures: it returns the details collection and does not return uninitialized status/value variables. Similarly, its MessageHeader already includes source.endpoint and destination\[\].endpoint. Those are historical/different-version findings, not proven current defects.

The current code still exhibits the P0/P1 semantics recorded above. Before any fix, tests should reproduce the actual behavior on the frozen piqitt-2.0 base and on the donor revision being promoted. This avoids treating an older attachment as the authoritative current release.

## 6.2 Defect repair policy

• Capture old behavior as a golden baseline, including defects and negative controls, before any code change.

• Use separate tests for current observed behavior and desired post-fix behavior; expected failures must be explicitly labelled, not silently ignored.

• Repair defects after the parity baseline is secured, in the phase where that semantics becomes necessary. Do not defer every correctness repair until the final phase.

• Every intentional semantic change needs an ADR, updated profile/mapping version, and an old-versus-new comparison artifact.

# 7 Contracts and evidence model

## 7.1 RealitySnapshot minimum

Minimum envelope: snapshot_id, schema_version, generator revision and seed, creation context, immutable fact records, stable entity identifiers, relationship assertions, event assertions, coding systems/versions, temporal precision and offset, and explicit missingness. The schema should be limited to facts actually supplied by a chosen MediLacra adapter.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th>RealitySnapshot (conceptual)<br />
snapshot_id / schema_version / generator_revision / seed<br />
entities: [Patient, Encounter, Observation, Order, Charge, ...]<br />
facts: [fact_id, entity_id, kind, value, type, system, time, source]<br />
relationships: [relation_id, subject_id, predicate, object_id]<br />
events: [event_id, type, effective_time, workflow_state, source]<br />
manifest: [source_hash, config_hash, source_record_keys]</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

Read-only DuckDB projection may be the first adapter. Schema inspection must precede assumptions about which MediLacra entities are actually persisted. The earlier MediLacra Reality Model concept proposed six small seams (ConceptDef, GeneratorRegistry, RelationshipDef, RealityContext, Constraint and RealityEvent); harvest them only where a real snapshot field, identity or linkage requires one. No graph database or universal event-sourcing rewrite is required for the first acceptance slice.

## 7.2 Representation and mapping registry

Each produced message/resource should carry an artifact ID, a snapshot ID, source fact IDs where possible, representation type/version, mapping revision, and declared source coverage. Maintain a mapping table keyed by v2 segment/field/component/repetition and target R4 path, with evidence of the governing official mapping reference and any local override.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th>Mapping coverage state: SUPPORTED | PARTIAL | UNSUPPORTED | NOT_APPLICABLE<br />
Preservation state: PRESERVED | CHANGED | LOST | AMBIGUOUS | NOT_EVALUATED<br />
Independent FHIR state: VALID | INVALID | NOT_VALIDATED<br />
PIQI reference binding: BOUND | UNBOUND | UNSUPPORTED | SKIP</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

## 7.3 Assessment result envelope

A high PIQI score is not evidence of conformance, transport acceptance or semantic retention. The durable result envelope should keep these dimensions and their coverage denominators separate.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th>{<br />
"run_id": "...", "artifact_id": "...", "snapshot_id": "...",<br />
"conformance": {"status": "NOT_VALIDATED", "profile_version": "..."},<br />
"piqi_local": {"status": "NOT_EVALUATED", "score_percent": null},<br />
"piqi_reference": {"status": "UNSUPPORTED", "rubric": "USCDI_V3"},<br />
"sasi": {"status": "NOT_EVALUATED", "preserved": 0, "evaluated": 0},<br />
"mapping_coverage": {"supported": 0, "partial": 0, "unsupported": 0},<br />
"transport": {"status": "NOT_ATTEMPTED"},<br />
"provenance": {"source_sha256": "...", "mapping_sha": "..."}<br />
}</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

Schema shown as a design sketch; final keys, enums and nesting must be versioned, tested and accepted before consumers depend on them.

## 7.4 JSON configuration versus executable mappings

**JSON owns declarative policy.** Profiles, steps, weights, conditional checks, thresholds, terminology identities, seeds, endpoint references, and schema versions.

**Code owns transformation semantics.** HL7 field parsing, repetitions, coded data types, FHIR construction, workflow-state interpretation, relationship matching and error behavior.

**Official artifacts remain authoritative inputs.** Use pinned PIQI reference JSON and HL7 mapping publications as source data, with a separate adapter; do not translate them into a hand-authored lookalike and present it as official.

During migration, YAML and JSON loaders must normalize to the same typed AssessmentProfile. Before switching defaults, compare rule ordering, prerequisites, effects, applicability, weights and exact scorecards on frozen fixtures. Runs capture schema and SHA for every effective config/reference file.

## 7.5 Evidence persistence

Use WAP_AS DuckDB as the starting operational index. Every run is additionally exportable as a portable evidence package with a per-run DuckDB snapshot and its own immutable files, checksums and effective policy. The DuckDB snapshot is a queryable derivative/index, never the only surviving evidence. See sections 7.6-7.9 for a precise artifact contract.

Keep local credentials and secrets out of artifacts and version control. All examples and tests use synthetic patients. A future PHI mode is a separate governance decision.

## 7.6 Standard ExperimentRun evidence package (v0.4 proposal)

“Standard payload” means a self-contained, portable run package, not a requirement that one large JSON object contain every binary or transcript. The manifest/index carries the relationships; individual artifacts keep native formats. A package can be zipped, copied, opened locally and inspected without Streamlit or IRIS.

Mandatory baseline artifacts exist for every completed or failed run. Optional/conditional artifacts exist only when the relevant input family, assessment or integration was invoked. Every expected-but-absent stage is represented explicitly as NOT_RUN, UNSUPPORTED, NOT_EVALUATED or FAILED in the manifest; no empty FHIR or artificial v2 data is invented to fill a folder.

| **Artifact / example path**                                | **Presence**                          | **What it establishes**                                                                                                                       |
|------------------------------------------------------------|---------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| manifest.json                                              | Required                              | run_id, schema/version, input types, stage statuses, source/mapping/config revisions, artifact IDs and relationships                          |
| inputs/\* (original .hl7, .json, .ndjson, snapshot)        | Required: original as supplied        | Immutable raw source bytes, source URI, original filename, SHA-256 and media/standards type                                                   |
| config/effective_run.json                                  | Required                              | Resolved non-secret dials, selected profile, seeds/timezone, settings and effective policy hash                                               |
| config/sams_effective.json + rubric/reference manifest     | Required if SAM assessment selected   | Exact SAM definitions, prerequisites, weights, scope and rubric identity used; reference versions/hashes; no unlicensed bulk reference copies |
| representations/\*.hl7                                     | When v2 input or generated            | Raw/native HL7 v2 artifacts and mapping lineage; not required for FHIR-only runs                                                              |
| representations/\*.fhir.json or \*.fhir.ndjson             | When provided or produced             | Input/derived/native FHIR R4 representation, role/format/version and links to source artifacts                                                |
| assessments/piqi_local.ndjson and/or piqi_reference.ndjson | When PIQI selected and applicable     | Per-message/per-criterion result, denominator, score, effective SAM IDs and coverage state                                                    |
| assessments/sasi.ndjson; validation/\*.json                | When executed                         | Source-target preservation findings and independent FHIR validator reports; separate status channels                                          |
| transport/http_exchanges.ndjson + exchange JSON/body refs  | Only if network stage executed        | HTTP or HTTPS method, redacted URL/headers, status, timing, error, request/response body hashes and optional synthetic-safe body files        |
| evidence/events.ndjson and findings.ndjson                 | Required                              | Stage lifecycle, errors, warnings, negative controls and linked finding records                                                               |
| catalog/run.duckdb                                         | Required for portable complete export | Query-ready, per-run snapshot of derived catalog tables; shared operational DuckDB remains optional implementation storage                    |
| checksums.sha256 + artifacts/index.json                    | Required                              | Content identities and verification of packaged artifacts; optional signature handled separately                                              |

DuckDB policy: WAP_AS may maintain one shared operational piqitt_runs.duckdb for all runs. The portable evidence export must include a single-run run.duckdb snapshot or an explicitly equivalent snapshot view derived from the canonical immutable files. Do not turn either database into the only source of truth. Pin DuckDB schema/version and make export reproducible from raw evidence.

## 7.7 Proposed layout and minimal manifest keys

> run-{run_id}/  
> manifest.json  
> inputs/ \# native input bytes: v2, FHIR, or reality  
> config/  
> effective_run.json  
> sams_effective.json \# when PIQI/SAMs selected  
> references_manifest.json  
> representations/ \# v2 and/or FHIR, with source roles  
> assessments/  
> results.ndjson \# typed outcomes for all selected channels  
> piqi_local.ndjson \# when applicable  
> piqi_reference.ndjson \# when applicable  
> sasi.ndjson \# when invoked  
> validation/ \# FHIR R4/profile report when run  
> transport/ \# HTTP(S) exchanges if invoked  
> http_exchanges.ndjson  
> evidence/  
> events.ndjson  
> findings.ndjson  
> catalog/run.duckdb \# queryable export snapshot  
> artifacts/index.json  
> checksums.sha256

Minimum manifest contract: run_id; run_schema_version; created_at and completed_at; execution status; input artifact identifiers and standards/version (HL7 v2.5.x or FHIR R4 4.0.1); stage plan and outcomes; source revision/hash; mapping/evaluator/PIQI rubric/SAM/reference versions and hashes; declared supported/partial/unsupported coverage; environment/dependencies; optional synthetic snapshot/seed/timezone; and pointers to artifact IDs, paths, content types and SHA-256. Add stable parent/child run or artifact relationships as needed, without treating the run object as the payload store.

HTTP(S) logging rule: record protocol honestly (local IRIS may use HTTP), redact passwords/tokens/cookies and sensitive headers, preserve status/response timing and hashes, and store request/response bodies only when synthetic-only policy permits. An offline run has transport stage NOT_ATTEMPTED, not a fabricated successful HTTPS log. Log schema and redaction tests belong in P1.

Execution state can advance while work is running, but raw inputs and finalized evidence are immutable. A corrected output is a new artifact revision or new run linked to the original, not an in-place overwrite. Run IDs are not patient IDs or message IDs.

## 7.8 Standards-correct input and assessment semantics

Do not call the input options “HL7 versus FHIR.” HL7 v2 and HL7 FHIR R4 are both HL7 standards. PIQITT’s explicit source formats are (1) HL7 v2 message/file, (2) HL7 FHIR R4 resource/Bundle/NDJSON where supported, and (3) optional MediLacra synthetic reality snapshot. The format adapter validates shape, records a source-standard/version label and routes to applicable stages.

For a FHIR-only input, direct local PIQI/reference PIQI and FHIR conformance can run; v2-to-FHIR preservation cannot legitimately be measured without a reference source, so SaSI reports NOT_EVALUATED. For v2 input, converter coverage and stage statuses must precede any derived-FHIR assessment. For reality inputs, retain independent native v2 and native FHIR projections as different artifacts.

## 7.9 ORM^O01 and experimental maturity gates

The historical 100.00 mean PIQI for ORM^O01 in the WAP_AS regression record is a misleading success signal: the original conversion dispatch falls back to a limited MessageHeader/Patient Bundle while the evaluator can score what remains. The immediate safeguard belongs before scoring, not only in a UI warning.

• Default ORM^O01 behavior: conversion coverage UNSUPPORTED; no successful derived-FHIR transformation claim; local PIQI on that unsupported conversion is NOT_EVALUATED and piqiIndex=null (not zero, not 100). The raw v2 input and diagnostic result remain in the package.

• A separately supplied FHIR artifact may be assessed as FHIR, but must not be mislabeled as a successful ORM conversion. Historical scorecards remain unchanged and explicitly marked legacy, while the current behavior is fixed and testable.

• SaSI maturity: repository tests and a historical 1,000-message analysis exist, but the owner regards the experiment as not independently validated. Mark the page Experimental; run fresh pinned controls, negative controls and independent source assertions before promoting any fidelity claim.

• WAP_AS maturity: owner reports substantial local CLI workload experience; the cited public-repository execution evidence proves a 1,000-message smoke baseline, not a fresh multi-hundred-MB benchmark. Mark the page Batch Experiment; re-run pinned controls before claiming scale or throughput.

# 8 Branch and source-import strategy

## 8.1 Branch choice

Create piqitt-2.0 from the original piqitt/main after fetching remote history and recording its exact base commit. The new branch is a temporary engineering workbench; it is not a premature claim that the final application must remain in this repository. Preserve main and all other project repositories untouched while doing the initial audit and imports.

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th>git clone https://github.com/natosit-dev/piqitt.git<br />
cd piqitt<br />
git fetch origin<br />
git switch main<br />
git pull --ff-only origin main<br />
git switch -c piqitt-2.0<br />
# Record the base SHA before importing anything.<br />
git rev-parse HEAD<br />
# Publish only when the baseline inventory is ready.<br />
# git push -u origin piqitt-2.0</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

Commands are proposed operator steps, not a record of execution. If a local checkout already exists, do not reclone or overwrite uncommitted work.

## 8.2 Selective import manifest

| **Source**                       | **Import candidates**                                                        | **Import rule / tests**                                               |
|----------------------------------|------------------------------------------------------------------------------|-----------------------------------------------------------------------|
| piqitt main                      | Current root UI, core, profiles, fixtures                                    | Base behavior pinned; old outputs captured.                           |
| piqitt_connect main              | Newer converter/evaluator, multipage UI, IRIS REST helpers and documentation | Version-by-version comparison; promote one core.                      |
| piqitt sasi                      | sasi_analyzer, sasi_sams, summary and tests                                  | Rebind to canonical converter; reproduce findings before enhancement. |
| piqitt WAP_AS                    | wap_runner, wap_cli, run_repo, run artifacts                                 | Import without original duplicate core; 1,000-message parity.         |
| piqitt official-artifacts branch | piqi_reference, JSON rubrics/SAM definitions, FHIR binding experiments       | Retain upstream provenance and experimental status.                   |
| MediLacra Connect                | Mutation engine, evidence pack, endpoint comparison interfaces               | Call through adapter/package; no wholesale code copy.                 |
| MediLacra / FHIR Engine          | Snapshot/renderer-capable domain models where verified                       | Pin package/version or adapter; maintain ownership boundary.          |
| piqitt-contest + piqitt_dev      | Reference fixtures, regression comparisons, historic notes                   | No automatic promotion; harvest only justified specimens.             |

## 8.3 Working layout (provisional)

<table>
<colgroup>
<col style="width: 100%" />
</colgroup>
<thead>
<tr class="header">
<th>piqitt/ [branch piqitt-2.0]<br />
pyproject.toml<br />
src/piqitt/<br />
core/ # orchestration, contracts, result envelopes<br />
formats/ # v2/FHIR read and serialization utilities<br />
mappings/hl7v2/ # explicit tested v2 -&gt; FHIR mappings<br />
mappings/fhir_r4/ # independent reality -&gt; FHIR renderers<br />
reality/ # immutable snapshot model and MediLacra adapter<br />
assessment/piqi/ # local + official-artifact adapters<br />
assessment/sasi/ # source/target and stage fidelity<br />
validation/ # v2 support, R4/profile validation interfaces<br />
execution/ # streaming runner, DuckDB, manifest, artifact IO<br />
experiments/ # mutation wrappers and experiment controls<br />
connectors/iris/ # optional FHIR/legacy REST clients<br />
piqitt.py, pages/ # compatibility Streamlit entry points<br />
config/ # versioned JSON + JSON Schema (new)<br />
reference/ # pinned standards metadata/artifacts<br />
tests/fixtures/ # frozen corpora and negative controls<br />
docs/ # work log, decisions, source-import manifest</th>
</tr>
</thead>
<tbody>
</tbody>
</table>

This is a proposed package topology, not an excuse to move all files immediately. Keep compatibility imports until both Streamlit pages, CLI and tests use the same production implementations.

## 8.3a Experiment pages are interfaces, not engine forks

> piqitt.py \# existing primary thin UI shell  
> pages/  
> 1_Inspect_and_Score.py \# v2 or FHIR R4 inputs, PIQI and validation  
> 2_Experiments_SaSI.py \# preservation experiment controls/results  
> 3_Experiments_WAP_AS.py \# CLI/batch path controls/history  
> 4_IRIS_Connect.py \# optional transport/read-back  
> 5_Run_Browser.py \# artifact and evidence inspection  
> piqitt_core/ \# canonical callable modules / RunService  
> ... \# decide exact decomposition during import

These names are illustrative, not a requirement to rename existing pages immediately. The UI may import/call canonical module functions directly; avoid embedding clinical assessment or HTTP transport implementations in the page files.

## 8.4 Work log discipline

• docs/WORK_LOG.md: chronological commands, observed outputs, blockers and decisions; separate verified behavior from recommendation.

• docs/DECISION_LOG.md: ADR ID, options, rationale, consequence and reversibility.

• docs/SOURCE_IMPORT_MANIFEST.json: source repository/ref/commit/blob SHA, license, destination path, tests and import disposition.

• docs/PROJECT_BUILD.md: milestone status, commands, functional boundaries, build environment and known limitations.

• docs/PROMPTS_RAW.md: relevant source prompts and decision provenance, redacted for secrets.

• tests/fixtures/: original controls and negative cases with hashes; never rewrite a golden input in place.

# 9 Phased build plan

The ordering below makes consolidation the first implementation milestone. Correctness fixes occur after source-parity capture, but before a new mapping or research layer is allowed to rely on an unsound result.

## E-00 Baseline freeze and evidence harness

No behavior changes.

• Pin main and donor branch commits, reference sets and dependency versions.

• Harvest existing PIQITT, SaSI, WAP_AS, PIQI-43 and IRIS regression fixtures and historical outputs.

• Inventory actual files, imports, entry points, tests, configuration paths, duplication, license notices and unsupported features.

• Reproduce available offline tests; record inability to reproduce as a blocker rather than a claimed PASS.

**Deliverables.** Source import manifest; baseline test matrix; frozen inputs/outputs; known-defect corpus; initial WORK_LOG.

**Acceptance.** Gate: every donor has pinned provenance; at least one documented control for each major existing workflow; no modification of historical repos.

## E-01 One coherent executable core

Integration without silent semantic repairs.

• Create piqitt-2.0 branch from original main.

• Promote one canonical converter/evaluator after old/new behavior comparison; leave historical implementations as fixtures, not runtime duplicates.

• Import SaSI, WAP_AS and reference-PIQI adapters without their copied legacy engines.

• Expose one library API for conversion, assessment, run execution and evidence; redirect UI and CLI entry points.

• Add import/run/CLI smoke tests on Python 3.10/3.11 and the existing local Docker/WSL stack.

**Deliverables.** Unified package; compatibility entry points; CI harness; migration notes; parity difference report.

**Acceptance.** Gate: existing upload and IRIS demo workflows still exercise the same core; SaSI and WAP_AS run offline; score differences individually explained.

## E-01a Minimum shared experiment runtime and UI seam

• Create the smallest stable RunSpec/ExperimentRun/artifact references needed to call converter/assessment/batch functionality once from both CLI and Streamlit. The full JSON schema can mature during E-02.

• Add typed v2 and FHIR R4 input intake and an explicit unsupported-family preflight; distinguish conversion from direct FHIR assessment.

• Use existing SaSI and WAP_AS engines as donor capabilities without importing competing converter/evaluator copies; keep historical output fixtures alongside new normalized results.

• Provide separate thin SaSI and WAP_AS Experiment pages. Pages can pass dials/files directly into canonical library calls; no subprocess orchestration, separate scoring definitions or HTTP request implementation in the page.

• Expose the standard run package in section 7.6; include manifest/inputs/effective policy/JSONL outcomes/checksums/run DuckDB snapshot; network evidence only when transport was attempted.

E-01a acceptance: one offline v2 run and one offline FHIR R4 run produce valid run packages via CLI and Streamlit; one unsupported ORM is reported without a PIQI success score; SaSI and WAP_AS run from separate experiment controls and share the same artifact identity/canonical modules; zero unaccounted behavior drift in imported control cases.

## E-02 Versioned JSON, official references and result envelope

Contracts and coverage become explicit.

• Define JSON Schema for PIQITT-owned profiles/config; dual-load YAML/JSON to identical typed objects.

• Pin PIQI official JSON rubrics/SAM metadata and HL7 v2-to-FHIR mapping artifacts with source and checksum.

• Normalize PIQI result envelope: score unit, assessment applicability, unsupported/unbound states, critical failures and provenance.

• Create mapping coverage registry and terminology availability/version manifest.

• Add parity checks for rule effects, prerequisites, conditions, weights and scorecards.

**Deliverables.** JSON schemas and configs; official-artifact inventory; schema-versioned results; coverage report.

**Acceptance.** Gate: YAML/JSON behavioral parity; no unsupported or missing criterion silently counted as success; all run configs hashed.

## E-03 Correctness stabilization and negative controls

Repairs begin only after E-00/E-01 parity.

• Repair scoring-effect semantics and missing-resource applicability reporting.

• Correct CE/CWE/CNE typed values, temporal offset precision and unsupported message routing within declared slice.

• Replace unfounded Encounter/Observation status constants with sourced/event-aware policy.

• Establish source-aware reference matching and explicit unknown/ambiguous results.

• Turn historic ORM, coded value, time and FT1 defects into versioned tests with old/new comparison.

**Deliverables.** Defect tests; mapping change log; versioned expected outputs; typed error and status reports.

**Acceptance.** Gate: no silent semantic fabrication; negative controls fail in the intended dimension; unrelated historic baselines unchanged.

## E-04 Immutable reality snapshot and two independent projections

Prove the scientific control.

• Define RealitySnapshot and a read-only MediLacra adapter for a narrow Patient/Encounter/Observation slice.

• Produce native v2 from the snapshot via existing generation interface; record field-to-fact linkage.

• Produce direct FHIR R4 from the same snapshot without passing through v2.

• Add fact-level stage comparison and deterministic reordering/wrong-link/missingness mutations.

• Preserve source coverage and valid ambiguities; do not promote generated reality to clinical truth.

**Deliverables.** Versioned snapshot fixture; native v2 and native FHIR; stage-attributed preservation ledger; paired-run evidence.

**Acceptance.** Gate: single frozen patient + encounter + two observations yield independently generated representations and interpretable preservation results.

## E-05 Standards-backed mapping and declared conformance

Expand only the stated minimum supported slice.

• Pin HL7 v2.5 local profiles and reviewed official v2-to-FHIR mapping references.

• Apply field/datatype semantics to PID, PV1, OBX, OBR, FT1 and appropriate MSH/Bundle portions.

• Resolve charge event versus actual claim representation according to source meaning and applicable R4 profile.

• Validate every declared supported fixture using an independent FHIR R4/profile validator, including references and terminology policies.

• Keep ORM as an explicit unsupported control until an order mapping is deliberately added and verified.

**Deliverables.** Versioned mapping catalog; declared coverage report; R4 validation reports; corrected fixtures.

**Acceptance.** Gate: declared supported fixtures pass independent R4/profile validation; unsupported coverage remains visible and reproducible.

## E-06 Optional native IRIS FHIR integration and end-to-end evidence

Do not break the offline or legacy paths.

• Retain current PIQITT custom REST integration as a compatibility target.

• Stand up/configure native IRIS FHIR R4 endpoint and query CapabilityStatement.

• Use POST/transaction + read/search/read-back with synthetic fixtures; capture responses and FHIR OperationOutcome.

• Keep file-based HL7 interoperability production separately testable.

• Verify offline runs still work with IRIS absent; redact secrets and bind all network artifacts to run IDs.

**Deliverables.** IRIS setup notes; smoke and negative tests; persisted resource IDs; request/response manifest; offline parity evidence.

**Acceptance.** Gate: one native FHIR round-trip and one IRIS-down offline run pass; transport and semantic verdicts remain distinct.

## E-07 Research corpus and Random Forest inference (deferred)

Requires all evidentiary foundations.

• Build dataset keyed by snapshot, representation, mapping revision, mutation, source fact and assessment label.

• Separate observed loss from causal hypothesis; normalize categories such as missing, coerced, mislinked, mis-coded and temporally distorted.

• Split training/testing by scenario and mapping family rather than randomly leaking near-duplicate generated messages.

• Benchmark simple rule-based baselines and a Random Forest; inspect calibration, performance and feature stability.

• Treat feature importance as investigatory evidence, not conclusive explanation or a product readiness claim.

**Deliverables.** Reproducible supervised dataset; evaluation protocol; research report; go/no-go criteria.

**Acceptance.** Gate: trustworthy held-out labels, no identity leakage and clear separation from production or official PIQI scores.

## 9.1 Immediate first tranche

The first code tranche is E-00 and E-01, with a minimal versioned ExperimentRun and artifact contract introduced immediately in E-01. The broader JSON Schema/configuration formalization remains in E-02. First prove one canonical backend callable from both CLI and Streamlit, preserving old output evidence. Direct HL7 FHIR R4 input, unsupported ORM handling and separate SaSI/WAP_AS experiment pages are first-tranche acceptance cases; they must not be postponed until later phases. Do not add new message families or rewrite the UI.

## 9.2 Definition of done for each implementation change

• Source path, source revision and license recorded in import manifest when content is reused.

• Acceptance criterion linked to an automated test or recorded manual validation with exact inputs/outputs.

• No unreviewed behavior change hidden in a refactor or generated fixture replacement.

• Test result, benchmark (when applicable), provenance and rollback point entered in WORK_LOG.

• Docs/decision log revised, including explicitly deferred defects and known unsupported operations.

# 10 Regression and experimental test plan

| **Case**                  | **Input / perturbation**                     | **Required observation**                                                                 |
|---------------------------|----------------------------------------------|------------------------------------------------------------------------------------------|
| T01 Legacy ADT            | Golden ADT^A01                               | Same baseline outputs before fixes; patient and encounter references inspected.          |
| T02 Legacy ORU            | Golden ORU^R01 with NM                       | Typed numeric value and unit preserved on supported path.                                |
| T03 Gender Harmony        | CE/CWE/CNE coded OBX values                  | No caret-packed coded value in valueString for supported coded types.                    |
| T04 Temporal              | Source timestamp with -0400 offset           | No dropped offset or fabricated Z; precision retained.                                   |
| T05 Zone-less clock       | Source local time without offset             | Explicit policy and no silent assumption of UTC.                                         |
| T06 DFT charge            | FT1 charge with code/amount/date             | Valid semantic charge representation; Claim only with sourced claim facts.               |
| T07 Unsupported ORM       | ORM^O01 negative control                     | UNSUPPORTED mapping, not a successful assessment based on sparse output.                 |
| T08 Missing target type   | Profile expects absent Observation           | NOT_EVALUATED or missingness finding; denominator/coverage explains outcome.             |
| T09 Informational SAM     | Effect=Informational check fails             | Visible finding without affecting PIQI score.                                            |
| T10 Reordered OBS         | Same observations in different target order  | No false semantic loss where stable matching is possible.                                |
| T11 Wrong patient link    | Resolvable reference points to wrong Patient | Local reference validity PASS; relationship fidelity FAIL.                               |
| T12 Duplicate/missing OBS | One duplication / one dropped Observation    | Cardinality and fact coverage account for each instance.                                 |
| T13 Zero-delta            | Unmutated FHIR control                       | Byte/canonical hash equivalence under documented policy; no changed path.                |
| T14 Single mutation       | One targeted coding/identifier edit          | Exactly one declared changed path and its evidence receipt.                              |
| T15 Missing terminology   | Unavailable/partial local LOINC file         | UNKNOWN or CONFIG_ERROR, not automatic invalid-code truth.                               |
| T16 YAML/JSON parity      | Same profile via both loaders                | Equal normalized profile, results, rule order and score count.                           |
| T17 Official binding      | Missing PAT_CLINICAL_V1 binding              | UNBOUND rather than PASS/FAIL guessed semantics.                                         |
| T18 Independent FHIR      | Native and derived FHIR from one snapshot    | Both independently validated; difference attributed to a stage.                          |
| T19 Batch WAP_AS          | Historical five-file 1,000-message corpus    | Run completion, detailed NDJSON and catalog parity against pinned baseline.              |
| T20 IRIS-down             | Run offline with endpoint absent             | Offline assessment succeeds; optional integration fails separately.                      |
| T21 Native IRIS           | Controlled transaction and read-back         | Persisted resource/IDs; validation result and request/response evidence.                 |
| T22 Repeatability         | Same seed/config/code, repeated run          | Stable semantic content and preserved hashes with volatile fields normalized explicitly. |

## 10.1 Experimental proof of loss attribution

For the first reality experiment, select one patient, one encounter, one numeric Observation and one coded Observation. Freeze the source snapshot, emit both representations, convert the v2, and evaluate all three stage boundaries. Then mutate the v2 coded representation and the target FHIR association separately. A successful result produces an exact source fact ID, source path, destination path, evidence pointer, and an unambiguous stage of degradation (or AMBIGUOUS if evidence is insufficient).

## 10.2 Validation execution levels

**Unit.** HL7 parsing/field mapping, status, timestamps, coded values, profile/config loaders, match algorithms, scoring math.

**Contract.** Typed snapshot/representation/evaluation envelopes, schema versions, source mapping coverage and artifact manifests.

**Integration.** One CLI and Streamlit service, streaming catalog, PIQI adapters, IRIS client and R4 validator.

**Experimental.** Deterministic zero-delta, one-defect mutants, wrong link, order permutations, unsupportable coverage and held-out realism checks.

## 10.3 v0.4 contract and UI regression additions

| **Test**                   | **Exercise**                                                     | **Expected evidence**                                                                                  |
|----------------------------|------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------|
| T23 FHIR-only ingest       | Drop/upload an HL7 FHIR R4 Bundle; no v2 source                  | Native FHIR artifact accepted; PIQI/validation where enabled; SaSI NOT_EVALUATED                       |
| T24 ORM default            | Submit ORM^O01 through UI, CLI, WAP backend                      | UNSUPPORTED conversion; PIQI NOT_EVALUATED with null score; raw v2 retained; never 100                 |
| T25 Thin UI parity         | Execute same pinned v2 and FHIR inputs through UI and CLI        | Equivalent normalized scientific results and artifact contents except run-specific IDs/timestamps      |
| T26 Page isolation         | Open SaSI and WAP_AS Experiments pages                           | Both call canonical modules; switching pages does not create/alter a run                               |
| T27 Portable package       | Export and inspect run without active UI or IRIS                 | All required artifacts present; hashes verify; per-run DuckDB opens; manifest links resolve            |
| T28 HTTP(S) capture        | Execute optional local IRIS request with fake credentials        | Protocol/status/body hashes captured; credentials redacted; offline mode produces NOT_ATTEMPTED        |
| T29 SAM snapshot           | Compare selected profile and effective SAM definitions to output | Exact effective rubric/SAM identifiers, policy hash and weights are traceable                          |
| T30 Run restart            | Restart Streamlit while a completed run exists                   | No accidental re-execution; historical run and artifacts still browseable                              |
| T31 SaSI negative controls | Reordered observations, wrong link and unsupported family        | Independent source assertion yields expected preserved/changed/ambiguous/unsupported result            |
| T32 Batch corpus           | WAP_AS on pinned multi-file and larger representative corpus     | Streaming with bounded memory and durable file/run failures; compare documented 1,000-message baseline |

# 11 Release gates and stop conditions

| **Gate**         | **Necessary evidence**                                                                 | **Blocker if not satisfied**                                        |
|------------------|----------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| C0 Baseline      | Pinned revisions, frozen fixtures, old outputs and recorded known-defect behavior      | No untraceable donor code or absent control.                        |
| C1 One core      | One runtime implementation for converter, PIQI, SaSI and run catalog; UI/CLI share API | Competing production copies or unexplained output drift.            |
| C2 Configuration | JSON Schema, YAML/JSON parity, official artifact/reference hashes                      | Unversioned effective policy or invalid config accepted.            |
| C3 Assessment    | Scoring effect correct; unsupported/unbound/missingness explicit                       | Untested/unsupported path represented as perfect quality.           |
| C4 Reality       | One immutable snapshot; independent v2 and native FHIR; stage ledger                   | Renderers generate different patients or facts without declaration. |
| C5 Conformance   | Independent FHIR R4/profile validation for declared supported fixtures                 | Invalid R4 accepted as conformant or unsupported mapping hidden.    |
| C6 Connectivity  | Native IRIS read-back, preserved legacy path and offline success                       | Transport PASS mistaken for semantic PASS or IRIS required offline. |
| C7 Research      | Held-out scenarios/mappings, source-independent labels, baselines                      | Leakage, post-outcome features or untrustworthy label origin.       |

## 11.1 Stop-work rules

• An unexplained parity change appears during the consolidation-only phase.

• Source artifact or applicable mapping authority cannot be pinned or licensing is unclear.

• Unsupported input produces success by default, or missing subjects disappear from coverage counts.

• An independent renderer uses v2-derived FHIR rather than the immutable original snapshot.

• Offline test execution unexpectedly requires IRIS, credentials, live HTTP access or external terminology.

• A proposed research feature includes the score or a post-outcome artifact, invalidating model evaluation.

## 11.2 Additional first-tranche release gates

• C1-UI: no Streamlit implementation of parsing, SAMs, conversion, evidence packaging or network transport; direct calls into canonical Python functions are permitted.

• C1-INPUT: HL7 v2 and HL7 FHIR R4 independently ingestible and stage-applicable; no invented source representation.

• C1-PKG: portable manifest, original inputs, effective policy/SAM snapshot where applicable, JSONL/NDJSON findings, artifact hashes and per-run DuckDB snapshot validated without UI.

• C1-ORM: known unsupported ORM^O01 is visibly unsupported, not 100% or 0%, and not counted as a completed conversion PIQI result.

• C1-EXP: SaSI and WAP_AS each exposed on a distinct experimental page with separate maturity evidence and a single shared runtime.

# 12 Risks, dependencies, and open decisions

| **Risk / impact**                                                              | **Mitigation / owner-facing decision**                                                                      |
|--------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| Older original-main base contains fewer integration fixes than piqitt_connect. | Treat donor files as candidates; compare and promote deliberately. Preserve base behavior before replacing. |
| A large merge inadvertently duplicates implementations or changes imports.     | Selective, file-level imports with provenance manifest; package-level API smoke tests.                      |
| Official PIQI model semantics differ from local FHIR-facing scoring.           | Two distinct assessment pathways; explicit adapter and state; only claim parity when validated.             |
| Source v2 omissions incorrectly assigned to converter.                         | Three-stage source fact ledger with independent native FHIR and v2 projections.                             |
| Direct FHIR adapter duplicates MediLacra models or imports SHN-specific logic. | Read-only snapshot contract; minimal shared package; no bulk generator transfer.                            |
| FHIR R4 validity confused with clinical or semantic equivalence.               | Independent conformance and SaSI channels; negative test specimens.                                         |
| FT1 charge/claim semantic ambiguity distorts results.                          | Review actual FT1 semantics and R4 mapping; typed unsupported instead of fabricated Claim.                  |
| Insufficient terminology rights or incomplete local LOINC coverage.            | Versioned external reference manifest; explicit coverage state and licensing review.                        |
| IRIS storage binds PIQITT to local deployment or historical score scale.       | Optional connectors, new result envelope, score compatibility conversion and offline CI.                    |
| Synthetic corpus patterns leak into training and testing.                      | Split by scenario/mapping family; random seed plus source-family group holdouts.                            |
| Historical performance claims no longer reproduce.                             | Keep old outputs as documented evidence, rerun after environment pinning and report differences.            |

## 12.1 Decisions pending review

**D-01 Temporary development repo/branch.** Proposed agreement: natosit-dev/piqitt / piqitt-2.0; final topology deferred.

**D-02 Canonical converter/evaluator.** Decide after side-by-side source and golden comparison; do not select solely by recency.

**D-03 Reality snapshot boundary.** Read-only MediLacra model or DuckDB adapter; no wholesale import.

**D-04 PIQI official versus local scoring.** Separate versioned result types and credentials/evaluation evidence.

**D-05 Configuration migration.** JSON Schema / dual-read parity, remove YAML only after acceptance.

**D-06 FHIR R4 validator and target profiles.** Select versioned external validator/artifact set during E-02/E-05.

**D-07 FT1 representation.** Prove ChargeItem/Claim choice against source semantics rather than applying blanket conversion.

**D-08 IRIS role.** Native R4 and custom REST coexist until read-back parity and migration decision.

**D-09 Release and repository topology.** Revisit after C5-C6; packaging as library versus app versus split remains open.

**D-10 ML / Drummond commercial boundary.** Separate research and commercial agreement; no inference claims before labeled evidence.

D-11 Thin client contract (DECIDED v0.4). Streamlit may directly call Python library functions, but does not implement domain, transformation, assessment, evidence or transport logic; no web API required.

D-12 Input terminology (DECIDED v0.4). HL7 v2 and HL7 FHIR R4 both first-class external inputs; absent source comparisons NOT_EVALUATED.

D-13 Standard package (PROPOSED v0.4). Portable files + per-run DuckDB snapshot, immutable hashes, effective SAM JSON, run manifest, stage NDJSON and optional HTTP(S) exchange evidence.

D-14 ORM control (DECIDED v0.4). ORM^O01 unsupported; piqiIndex=null/NOT_EVALUATED by default; retain old 100% as historical defect evidence.

D-15 Experiment pages (DECIDED v0.4). SaSI and WAP_AS each receive a thin Experiment page, without duplicating backend engines. SaSI remains explicitly unvalidated pending tests.

# 13 Review checklist

This section is intended for owner review before the first branch creation or source import. Approval of a phase does not automatically approve later milestones.

> \[ \] Agree piqitt-2.0 on the original piqitt repository as the temporary integration branch, with no decision yet on the final home.
>
> \[ \] Confirm which source and donor branch revisions must be captured during E-00, including private piqitt_dev treatment.
>
> \[ \] Confirm original supported message slice: ADT^A01, ORU^R01, DFT^P03, ORM negative control.
>
> \[ \] Confirm the first snapshot scope: one patient, one encounter, one numeric and one coded Observation, not a full synthetic hospital.
>
> \[ \] Approve separate terminology and PIQI reference-artifact manifests; identify licensed reference sources before import.
>
> \[ \] Approve distinct results for local PIQI, official PIQI, SaSI, FHIR conformance and IRIS transport.
>
> \[ \] Approve compatibility strategy for historical score units and the old custom IRIS REST service.
>
> \[ \] Approve the E-00/E-01 stop gate: no unrecorded semantic behavior change before parity freeze.
>
> \[ \] Choose the conformance validator and resource/profile scope before E-05 acceptance is claimed.
>
> \[ \] Retain ML/Random Forest and possible commercial integration as deferred, separately scoped work.

\[ \] Confirm direct invocation of canonical Python functions from Streamlit is allowed; no domain implementations or duplicated scoring policy inside UI.

\[ \] Confirm both HL7 v2 and HL7 FHIR R4 as external input standards; verify FHIR-only runs without fabricated v2 provenance.

\[ \] Confirm mandatory run package files and per-run DuckDB export; decide whether every SAM snapshot is full or contains licensed-reference pointers plus hashes.

\[ \] Confirm ORM preflight gate and null PIQI score for unsupported conversion; retain historical WAP_AS result as negative control.

\[ \] Confirm separate SaSI/WAP_AS Experiment pages, with SaSI unvalidated until independent acceptance tests and WAP_AS scale revalidation.

# Appendix A Source and evidence ledger

Repository links identify the inspected paths or historical evidence artifacts. For exact reproducibility, E-00 must pin branch heads and hashes at implementation start; the refs here document review provenance, not a guarantee of unchanged future branch state.

## A.1 Repositories and primary files

[<u>Original PIQITT repository</u>](https://github.com/natosit-dev/piqitt) - Original main; proposed branch origin.

[<u>Original PIQITT converter</u>](https://github.com/natosit-dev/piqitt/blob/main/scripts/fhir_convert_backend.py) - Converter compared across main/sasi/WAP_AS.

[<u>Original PIQITT evaluator</u>](https://github.com/natosit-dev/piqitt/blob/main/scripts/piqi_eval.py) - Earlier 26.9 KB implementation; current original main.

[<u>PIQITT Connect README</u>](https://github.com/natosit-dev/piqitt_connect/blob/main/README.md) - Integrated UI/IRIS architecture and score units.

[<u>PIQITT Connect converter</u>](https://github.com/natosit-dev/piqitt_connect/blob/main/lib/fhir_convert_backend.py) - Current canonical-candidate converter.

[<u>PIQITT Connect evaluator</u>](https://github.com/natosit-dev/piqitt_connect/blob/main/lib/piqi_eval.py) - Current canonical-candidate evaluator.

[<u>PIQITT Connect provenance</u>](https://github.com/natosit-dev/piqitt_connect/blob/main/docs/PROVENANCE.md) - Reconstructed IRIS baseline.

[<u>SaSI invariants implementation</u>](https://github.com/natosit-dev/piqitt/blob/sasi/scripts/sasi_sams.py) - Structural and semantic comparison logic.

[<u>SaSI invariant tests</u>](https://github.com/natosit-dev/piqitt/blob/sasi/tests/test_sasi.py) - Expected supported/unsupported behavior.

[<u>SaSI 1,000-message findings</u>](https://github.com/natosit-dev/piqitt/blob/sasi/findings/2026-08-19_initial_sasi_findings.md) - Recorded observations; not rerun.

[<u>WAP_AS branch README</u>](https://github.com/natosit-dev/piqitt/blob/WAP_AS/README.md) - Streaming and run catalog architecture.

[<u>WAP_AS runner</u>](https://github.com/natosit-dev/piqitt/blob/WAP_AS/scripts/wap_runner.py) - Stream-based execution code.

[<u>WAP_AS run catalog</u>](https://github.com/natosit-dev/piqitt/blob/WAP_AS/scripts/run_repo.py) - DuckDB catalog schema/operations.

[<u>WAP_AS validation</u>](https://github.com/natosit-dev/piqitt/blob/WAP_AS/WAP_AS_VALIDATION_2026-08-19.md) - Historical 1,000-message smoke evidence.

[<u>Official PIQI artifacts bridge</u>](https://github.com/natosit-dev/piqitt/blob/experiment/official-piqi-artifacts/reference/piqi/README.md) - Separate official artifacts and binding adapter.

[<u>PIQI reference Python bridge</u>](https://github.com/natosit-dev/piqitt/blob/experiment/official-piqi-artifacts/scripts/piqi_reference.py) - Experimental local execution states.

[<u>MediLacra Connect README</u>](https://github.com/natosit-dev/medilacra_connect/tree/integrate/piqi-43) - Controlled baseline and mutations.

[<u>MediLacra PIQI-43 acceptance</u>](https://github.com/natosit-dev/medilacra_connect/blob/integrate/piqi-43/docs/PIQI_V1_BASELINE_RESULTS_2026-09-11.md) - Recorded local pack acceptance; no external PIQI.

[<u>MediLacra endpoint boundary</u>](https://github.com/natosit-dev/medilacra_connect/blob/feature/piqi-endpoint-execution/docs/connectathon/PIQI_ENDPOINT_EXECUTION.md) - Transport versus PIQI evaluation distinction.

[<u>MediLacra FHIR Engine</u>](https://github.com/natosit-dev/medilacra_fhir_engine) - Synthetic domain model and build harvest.

[<u>FHIR Engine harvest scope</u>](https://github.com/natosit-dev/medilacra_fhir_engine/blob/main/docs/HARVEST_SCOPE.md) - Source parity and ownership caveats.

[<u>MediLacra unified baseline</u>](https://github.com/natosit-dev/medilacra_fhir_engine/blob/main/README.md) - Accepted October 2026 local application summary.

[<u>Contest baseline</u>](https://github.com/natosit-dev/piqitt-contest) - Historical IRIS demonstration.

[<u>HL7 v2-to-FHIR IG</u>](https://hl7.org/fhir/uv/v2mappings/) - Mapping reference; pin exact applicable release.

[<u>FHIR R4 resource documentation</u>](https://hl7.org/fhir/R4/) - FHIR R4 4.0.1 specification home.

[<u>FHIR R4 ChargeItem mapping</u>](https://hl7.org/fhir/R4/chargeitem-mappings.html) - Starting point for charge representation review.

Radiant Control handoff v1.0 (8 Nov 2026) - experiment-run architecture, positive-capability sequencing, requirements/ownership decisions, and research boundaries.

Original piqitt/main piqitt.py and piqitt_connect/main pages/2_IRIS_Connect_Demo.py - evidence of current UI orchestration and in-page transport functions.

Current owner review prompt (8 Nov 2026) - clarifies direct UI calls, v2/FHIR terminology, standard run package, ORM negative control, SaSI/WAP experiment pages, and raw prompt preservation.

## A.2 Repository commit snapshots observed during review

| **Repository**        | **Recent commit seen on 8 Nov 2026**     | **Review significance**                                     |
|-----------------------|------------------------------------------|-------------------------------------------------------------|
| piqitt                | a40300e4950d73ed192a2112cf516b4ec46a184b | Recent default-branch commit; E-00 must confirm exact base. |
| piqitt_connect        | b2b85d556bb8dc4443a8b9d57bea5a408ec5b6ef | Recent donor default-branch commit.                         |
| piqitt-contest        | fa01286f93b54da48e3660620fabc2e2da2bb548 | Known contest provenance commit.                            |
| medilacra_connect     | d26829fb1eb4b5c8b1db6cd8a45376dfaf459e74 | Recent default-branch commit; features use other refs.      |
| medilacra_fhir_engine | 35b4b88c5c7e71da5965c5731c5efeac22673492 | Recent harvest baseline commit.                             |

The review also used the local source document PIQITT_2_Project_Plan_Download.docx (version 0.2, 6 November 2026) and the supplied PIQITT evaluator/converter/config files for historical comparison. Those attachments are not asserted to match newer GitHub branches.

# Appendix B Requirements provenance and decision history

Selected original statements retained from the 6 November working plan and the subsequent branch decision. They explain scope and rationale; they are not a new approval of every architectural recommendation.

## B.1 Original implementation intent

"Ok, let's start thinking about it. Go review all existing PIQITT functionality"

"The generated FHIR is simplified; it is not a complete semantic mapping of every field in those message families."

"We should beef this up. Get to full conformance for minimum fields."

"The PIQIEvaluator loads configurable YAML"

"We should convert to JSON."

"This is a good opportunity to consolidate PIQITT into 1 repo"

"IRIS connectivity should be built in"

"6 limitations These should all be bugs to address after the initial consolidation"

"Also, it shouldn't just convert HL7 v2 to FHIR. It should be capable of generating FHIR from the synthetic reality. The mappings should be code and we should grab it from HL7."

"Let's see a consolidated plan, then initial enhancements to bring it up to snuff"

## B.2 Research intent (deferred)

"Back to Drummond. I should offer 10 plus compute resources to build. This project is an performance for future contracts. I should give them The Prestige"

"No, that's the existing product, not the prestige. The prestige is using the data for an RF ML inference pipeline to see where data tends to lose meaning"

This research objective remains in the plan, but the initial build produces evidence and labels rather than claiming a predictive implementation.

## B.3 New repository strategy

"I'm assuming yes, but could we simply create a PIQITT 2.0 branch on the original PIQITT repo to do all this consolidation and enhancement? Then figure out where to put it all once it's looking good?"

Decision reflected in v0.3: use piqitt-2.0 on the original piqitt repository as the temporary integration branch. Final architecture/packaging deferred until empirical acceptance.

# Appendix C Change history

| **Version** | **Date**   | **Change**                                                                                                                                                                                                                                       |
|-------------|------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 0.1         | 6 Nov 2026 | Initial consolidation architecture and technical defect plan (source planning record).                                                                                                                                                           |
| 0.2         | 6 Nov 2026 | Consolidated working plan; expanded reality-model, standards and implementation handoff detail.                                                                                                                                                  |
| 0.3         | 8 Nov 2026 | Full repository gap analysis incorporated; original piqitt/piqitt-2.0 branch decision adopted; current-vs-historical defects reconciled; phase gates and detailed acceptance matrix added.                                                       |
| 0.4         | 8 Nov 2026 | Radiant handoff and owner review: original-versus-target topology, thin Python UI seam, dual HL7-standard inputs, standard evidence package, ORM scoring guard, SaSI/WAP experiment pages, regression gates, raw prompts and final decision log. |

# Appendix D Raw user prompts and review provenance

Verbatim prompts visible in the current review sequence are preserved below, including wording, capitalization, punctuation and emojis. Earlier quoted source-excerpts from the preceding v0.3 document are retained in Appendix B; they are not misrepresented as full transcripts. The Radiant Control handoff is a separate reviewed source, not a user chat message.

## D.1 Direct user prompts in this review sequence

### 2026-11-08 · Repository gap comparison

> Show me a gap analysis between what you're proposing and the existing PIQITT repos

### 2026-11-08 · Branch-first decision

> I'm assuming yes, but could we simply create a PIQITT 2.0 branch on the original PIQITT repo to do all this consolidation and enhancement? Then figure out where to put it all once it's looking good?

### 2026-11-08 · Document request

> Ok, print the full gap analysis and build plan to doc. I want to review it all

### 2026-11-08 · Radiant handoff review

> I had Radiant Control review and provide some feedback, along with my comments. Let's review and make sure we've got the core capabilities solid, and that we're keeping the UI as stupid as possible- it's a thin client.

### 2026-11-08 · Current amendment

> For 1- I think calling stuff from the UI is OK, we just don't want the UI containing the functions themselves  
> The UI is the human interface where the dials are set, files can be dropped...  
> Ok I should've kept reading 😅 Seems like we're on the same page.  
>   
> 2-show me how this compares to the original PIQITT topology.  
>   
> 3-  
> A- define simply exactly what's in a standard payload. Off the top of my head it should include v2, FHIR, duckdb, JSON with HTTPS logs, NDJSON for PIQI output, JSON of SAM used, manifest... Am I missing anything?  
>   
> B- lol be clear about what you're referencing- FHIR and V2 are both HL7 standards. Agree that both standards should be available as inputs.  
>   
> C-Yes, we need to fix the ORM 100% PIQI problem.  
>   
> D- yeah, SASI is entirely untested. I feel like it should have separate pages for that and potentially WAP AS as an experiments section. WAP may be more solid- it was built from massive local CLI runs.  
>   
> 4- this sounds good.  
>   
> Let's update the gap analysis and build plan, version it, include my raw prompts, decision log at the bottom. Print to doc

## D.2 Earlier intent retained from v0.3

Appendix B already preserves selected statements from the earlier PIQITT 2.0 planning exchanges, including the original desire to consolidate one repo, move from YAML to JSON, beef up the minimal FHIR mapping, adopt official HL7 mapping materials, build in IRIS connectivity, and defer defects until after consolidation. Those are source-derived excerpts, not reconstructed full prompts.

## D.3 Evidence classification

Owner-authored prompts and Radiant Control handoff statements are requirements/decisions. Repository files and GitHub blob identity establish inspected implementation. SaSI and WAP_AS performance claims in older notes are historical execution records, not rerun results. The proposed contracts and acceptance tests in this v0.4 plan are engineering recommendations until implemented.

# Appendix E Decision log

Latest decision register, 8 November 2026. “Decided” reflects the owner’s statements or established Radiant handoff scope; “proposed” requires review; “open” must not be silently decided through an implementation detail.

| **ID**  | **State** | **Decision**                           | **Rationale / implementation handling**                                                                                                                                                         |
|---------|-----------|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ADR-001 | DECIDED   | Temporary development branch           | Work on piqitt-2.0 in natosit-dev/piqitt; preserve original main and other branches. Final package/repository split deferred.                                                                   |
| ADR-002 | DECIDED   | Primary experimental object            | ExperimentRun is the durable identity/lineage/evidence boundary; messages, Bundles, findings and transports are artifacts or stages, not competing primary objects.                             |
| ADR-003 | DECIDED   | MediLacra boundary                     | MediLacra owns synthetic source reality; PIQITT evaluates transformations and evidence. Use read-only versioned adapter; avoid whole-project import.                                            |
| ADR-004 | DECIDED   | First supported v2 slice               | ADT^A01, ORU^R01 and DFT^P03; ORM^O01 unsupported negative control.                                                                                                                             |
| ADR-005 | DECIDED   | Build order                            | Freeze and consolidate existing capabilities before semantic repairs and feature expansion; preserve evidence and intentionally changed outcomes.                                               |
| ADR-006 | DECIDED   | UI thin-client meaning                 | UI may directly call canonical Python functions/services for execution. UI owns dials, file drop, navigation, display; domain, SAM, transport and evidence implementations live outside the UI. |
| ADR-007 | DECIDED   | External input standards               | Both HL7 v2 and HL7 FHIR R4 are first-class inputs. SaSI source-target comparisons require actual corresponding source evidence.                                                                |
| ADR-008 | DECIDED   | ORM misleading 100%                    | Unsupported ORM conversion is explicitly UNSUPPORTED; no automatic derived PIQI success score. Current run value null/NOT_EVALUATED; retain historical 100% artifact as negative evidence.      |
| ADR-009 | DECIDED   | Experiments navigation                 | SaSI and WAP_AS have distinct thin experiment pages. SaSI remains experimental/unvalidated; WAP_AS has historical operational baseline but needs pinned parity/scale confirmation.              |
| ADR-010 | DECIDED   | PIQI/quality separation                | Keep local PIQI, reference PIQI, SaSI, independent FHIR conformance and network transport results distinct; unknown/missing coverage is not PASS.                                               |
| ADR-011 | DECIDED   | Policy ownership                       | PIQITT-owned declarative configuration moves toward schema-validated JSON; executable code owns mappings; official versioned standards artifacts remain separate.                               |
| ADR-012 | DECIDED   | IRIS role                              | Built-in optional transport/read-back adapter, preserve custom REST compatibility; no dependency on IRIS for offline assessment.                                                                |
| ADR-013 | PROPOSED  | Standard run package                   | Portable manifest, raw input, effective SAM/config JSON, v2/FHIR files as applicable, JSONL/NDJSON assessments, HTTP(S) exchange logs if attempted, SHA index, per-run DuckDB snapshot.         |
| ADR-014 | PROPOSED  | CLI/UI calling seam                    | Minimum Python RunService plus canonical callable modules and shared evidence store; no HTTP API needed initially. Exact module/API shape selected during P1.                                   |
| ADR-015 | OPEN      | Canonical converter/evaluator          | Select after source parity comparison and frozen fixtures; do not infer superiority from newest code.                                                                                           |
| ADR-016 | OPEN      | Run schema/versioning and storage      | Finalize artifact-reference schema, derived DuckDB snapshot/export mechanics and schema migration policy after the first working package.                                                       |
| ADR-017 | OPEN      | FHIR validation / mapping              | Pin R4 validator version, supported target profiles, official v2-to-FHIR mapping release, terminology sources and allowed rights.                                                               |
| ADR-018 | OPEN      | FT1 semantics                          | Select defensible ChargeItem/Claim mapping per source event and required target profile; do not fabricate submitted claim workflow.                                                             |
| ADR-019 | OPEN      | Official PIQI bridge                   | Complete FHIR-to-PIQI model binding/official SAM semantics and endpoint execution; maintain strict distinction from local YAML score.                                                           |
| ADR-020 | OPEN      | Final deployment topology and research | Choose packaging only after proven behavior; Random Forest and commercial decisions remain outside initial consolidation.                                                                       |
