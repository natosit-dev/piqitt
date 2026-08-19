# SaSI Project Plan
## Structural and Statistical Integrity for PIQITT

**Project:** SaSI ("sassy")  
**Repository:** `natosit-dev/piqitt`  
**Branch:** `sasi`  
**Status:** MVP operational — good enough for now  
**Updated:** 2026-08-19

---

# Prompt History

## Prompt 1
> While I'm gone, think about other data we could pull from this without changing what's working now. Look at the PIQITT and PIQITT-CONTEST repos. Consider what MediLacra is doing. I'm thinking we could come up with a custom SAM evaluator to bolt on?

## Prompt 2
> I think we should bolt a fork onto the non contest repo first. The contest was messy and fast. Let's map out the analyzer function- source, input, evaluations, definitions, workflow, output, meaning of output. Use Nat language along with the actual fancy words

## Prompt 3
> No, we're going to give it an awesome name. Structural and Statistical Integrity, but we can can call it SaSI 😹 (sassy) So we have PIQI- picky PIQITT- pick it SaSI- sassy Gotta keep myself amused! 😁😁

## Prompt 4
> Ok, put that all in an MD, create the SaSI fork, and drop in the documentation

## Prompt 5
> Ah, yeah a branch is what I meant anyways. I think I should pull a fresh copy to my machine. Give me the commands

## Prompt 6
> Ok, now what are the changes we need for SaSI?

## Prompt 7
> Ok, put together a project plan for how we will do this. Include a decision log at the bottom and my prompts at the top. Create a new MD in the SaSI branch and drop it in. Once I review, you'll go make the changes

## Prompt 8
> Do you have any questions before I set you loose on this?

## Prompt 9
> Brilliant, go get 'em tiger 🦾

## Prompt 10
> Ok, walk me through testing it, command by command

## Prompt 11
> Lol you can give me all the commands in a row ...

## Prompt 12
> Ran all the way through

## Prompt 13
> let's add a findings folder in the repo, add these results and what they may mean.

## Prompt 14
> What I suspect the issue was is PIQITT may not have those concepts available to validate. I couldn't get every CPT/ICD/LOINC code stuffed in there, so it's a sampling

## Prompt 15
> Oh, you are correct! They do use CWE, I wanted them to be able to be used as CE if possible, but as free text if not. It was an assumption that not every facility has these in place yet

## Prompt 16
> Update the project plan with what we've completed so far. Include prompts at the top, decision log at the bottom if it's not there already.

## Prompt 17
> I feel like we're at the "good enough" phase with this now?

## Prompt 18
> Let's update the documentation with some of these phase 2 ideas, but intentionally say this is good enough for now. We're building primitives, not polished products

---

# 1. Purpose

SaSI stands for **Structural and Statistical Integrity**.

PIQI asks:

> Is the resulting data good according to the configured quality checks?

SaSI asks:

> Did the important structure, relationships, values, counts, and population shape survive the transformation?

Fancy version:

> SaSI measures transformation fidelity through structural invariants, cardinality preservation, semantic equivalence, referential integrity, and statistical preservation.

Nat version:

> **What went in, what came out, and did PIQITT quietly eat or flatten anything important?**

SaSI remains separate from PIQI because data quality and transformation fidelity are different things.

---

# 2. Project Philosophy

SaSI is intentionally a **primitive**, not a polished product.

The goal is not to finish every possible feature, UI, statistical method, or interoperability edge case. The goal is to create a reusable measuring instrument that can expose transformation behavior clearly enough to support later work.

Fancy version:

> SaSI is a composable interoperability-analysis primitive.

Nat version:

> **Build the useful little machine. Don't spend three weeks making the useful little machine wear a tuxedo.**

The current implementation has crossed the threshold from prototype to usable primitive.

**This is good enough for now.**

Further work should be pulled by real findings, Connectathon needs, or reuse in another project — not by a desire to make SaSI feel "finished."

---

# 3. Architecture

```text
HL7 v2
   │
   ▼
PIQITT conversion
   │
   ▼
FHIR Bundle
   │
   ├── PIQI
   │     └── How good is the resulting data?
   │
   └── SaSI
         └── Is the result still faithfully representing the source?
```

SaSI evaluates one **transformation event** at a time:

```text
raw HL7 message
+
FHIR Bundle produced from that message
```

MediLacra is a controlled synthetic corpus for testing, not a SaSI dependency.

---

# 4. V1 Evaluation Model

SaSI reuses the SAM pattern but keeps its own SAM library and profile.

Each assessment returns:

```text
PASS
FAIL
SKIP
```

V1 does not produce a 0-100 SaSI score.

A detail record contains the SAM, dimension, source and target paths, source and target values, status, meaning, and evidence.

The first ten SAMs are:

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

---

# 5. Source and Target Inventories

## Source semantic inventory

Nat version: **write down what actually went in.**

SaSI currently extracts:

- message type
- segment counts
- PID patient identity fields
- PV1 encounter fields
- OBX count, code, value, unit, datatype, and time
- FT1 count and selected transaction values
- OBR order identifiers where useful

## Target semantic inventory

Nat version: **write down what came out.**

SaSI currently extracts:

- FHIR resource counts
- Patient resources
- Encounter resources
- Observation resources
- Claim resources
- DiagnosticReport resources
- MessageHeader resources
- internal FHIR references

The source and target inventories are the comparison substrate beneath the SAMs.

---

# 6. Canonicalization

SaSI compares meaning rather than byte equality.

Implemented normalizers cover:

- code systems
- timestamps
- numeric values
- units
- text

Examples:

```text
LN == http://loinc.org
```

when they represent the same terminology system.

SaSI also preserves explicit timezone semantics during comparison so timezone stripping is visible as a temporal integrity failure rather than normalized away.

Nat version:

> **Make equivalent shit look equivalent, but don't normalize away a real loss of meaning.**

---

# 7. Implementation Progress

## Phase 0 — Freeze baseline ✅ COMPLETE

Existing PIQI scoring and HL7→FHIR behavior were left unchanged so SaSI could observe them.

## Phase 1 — Source inventory ✅ COMPLETE

Implemented using PIQITT's existing parser helpers rather than creating a second HL7 parser.

## Phase 2 — Target inventory ✅ COMPLETE

Implemented over the generated FHIR Bundle.

## Phase 3 — Normalization layer ✅ COMPLETE

Code-system, timestamp, numeric, unit, and text normalization are implemented.

## Phase 4 — SaSI result schema ✅ COMPLETE

Message-level PASS / FAIL / SKIP results with detailed evidence are implemented.

## Phase 5 — Structural SAMs ✅ COMPLETE

All ten V1 SAMs are implemented.

## Phase 6 — SaSI library and profile ✅ COMPLETE

Created:

```text
sasi_sam_library.yaml
profiles/profile_sasi_minimal.yaml
```

## Phase 7 — Runnable orchestration ✅ COMPLETE

Created a standalone runner that sends raw HL7 through PIQITT conversion and then through SaSI without mutating the FHIR Bundle.

## Phase 8 — NDJSON output ✅ COMPLETE

Created:

```text
scripts/sasi_run.py
```

Output:

```text
sasi_results.ndjson
```

## Phase 9 — Summary analyzer ✅ COMPLETE

Created:

```text
scripts/sasi_summary.py
```

Outputs:

```text
sasi_summary.json
sasi_summary.md
```

The summary reports structural PASS / FAIL / SKIP counts plus statistical count retention and distribution drift.

## Phase 10 — Test suite ✅ COMPLETE

Created:

```text
tests/test_sasi.py
```

Current validation:

```text
pytest -q tests/test_sasi.py
7 passed
```

Tests cover normal ORU preservation, unsupported ORM behavior, DFT cardinality, aggregate retention, code-system canonicalization, timezone semantics, and current converter timezone loss.

## Phase 11 — Findings repository ✅ COMPLETE

Created:

```text
findings/
```

Initial observed results are preserved as project artifacts rather than disappearing into chat history.

## Phase 12 — Initial MediLacra corpus run ✅ COMPLETE

First real SaSI corpus:

| Message Type | Messages |
|---|---:|
| ADT^A01 | 200 |
| DFT^P03 | 200 |
| ORM^O01 | 200 |
| ORU^R01 | 400 |
| **Total** | **1000** |

---

# 8. Initial Corpus Results

## Structural results

- Patient preservation: **1000 PASS / 0 FAIL**
- Message-type support: **800 PASS / 200 FAIL**
- Encounter preservation: **800 PASS / 200 FAIL**
- Observation code preservation: **600 PASS / 0 FAIL / 400 SKIP**
- OBX cardinality: **600 PASS / 0 FAIL / 400 SKIP**
- FT1 cardinality: **200 PASS / 0 FAIL / 800 SKIP**
- Reference resolution: **800 PASS / 0 FAIL / 200 SKIP**
- Value preservation: **400 PASS / 200 FAIL / 400 SKIP**

## Statistical results

Patient gender:

```text
source count: 1000
target count: 1000
retention: 100%
distribution drift: 0 percentage points
```

Observation codes:

```text
source count: 9038
target count: 9038
retention: 100%
distribution drift: 0 percentage points
```

Coded Observation values:

```text
source coded values: 600
target valueCodeableConcept values: 0
retention as coded FHIR values: 0%
```

---

# 9. What the First Findings Mean

## ORM fallback

The 200 ORM messages are not handled by an explicit PIQITT converter path. SaSI correctly exposes this as unsupported transformation behavior and related structural loss.

This is a useful negative control.

## Gender Harmony CWE behavior

The 600 coded source values come from Gender Harmony-style coded OBXs.

The source intentionally uses **CWE** because real facilities may have uneven terminology implementation. The intended source behavior is:

> use a coded value when possible, but preserve useful human-readable text when local terminology support is incomplete.

PIQITT currently handles `CE` explicitly as a FHIR `valueCodeableConcept`, but CWE does not receive the same coded-value path.

The confirmed SaSI observation is therefore:

> Coded CWE values were not retained as FHIR `valueCodeableConcept` values.

That does **not yet prove the human meaning vanished**. The value may have been flattened into `valueString` or another less structured representation.

Fancy term:

> **Semantic degradation through datatype coverage loss**

Nat version:

> **The value may still be readable, but the machine-readable structure got flattened.**

This distinction is important. SaSI should conceptually distinguish:

```text
preserved
normalized
degraded
lost
```

V1 can continue using PASS / FAIL / SKIP internally while carrying richer meaning in evidence and findings.

---

# 10. PIQI Terminology Coverage vs SaSI Fidelity

These must stay separate.

PIQI may fail terminology validation because the local CPT / ICD / LOINC reference sets are sampled rather than complete.

That means:

> "PIQI does not recognize this code"

may be a **reference-set coverage problem** rather than bad healthcare data.

SaSI asks something else:

> Did the source representation survive the transformation?

Therefore an incomplete PIQI terminology sample does not explain SaSI's CWE structural finding.

Nat version:

> **PIQI may not know the code. SaSI only cares whether PIQITT changed or dropped what was sent.**

---

# 11. Statistical Integrity Rule Learned During Testing

SaSI must report **count retention and distribution drift separately**.

Why:

```text
Source: 100 A
Target: 50 A
```

The distribution is still 100% A, so percentage drift is zero even though half the records disappeared.

Therefore statistical integrity reports both:

```text
retention rate
+
distribution delta
```

This is now implemented.

---

# 12. PIQI + SaSI Interpretation

| PIQI | SaSI | Meaning |
|---|---|---|
| High | High | Good transformation producing good resulting data |
| Low | High | Source problems were faithfully preserved |
| High | Low | Clean-looking output after transformation loss or degradation |
| Low | Low | Poor source quality and/or poor transformation |

The dangerous quadrant remains:

```text
High PIQI
Low SaSI
```

Fancy term: **transformation-induced false confidence**.

Nat version:

> **We dropped the ugly parts and then congratulated ourselves on how clean the remainder is.**

---

# 13. Good Enough Boundary

SaSI V1 has reached the intended stopping point.

It can:

- observe the existing PIQITT transform
- compare source and target structure
- detect unsupported transformation paths
- detect cardinality changes
- compare codes, values, units, and timestamps
- verify FHIR reference resolution
- report population retention and distribution drift
- produce durable findings from real synthetic corpora

That is enough to make SaSI useful as a primitive.

We are **not** trying to make it a polished standalone product right now.

No additional work is required simply to make the repo look more complete.

Future work should happen only when one of these is true:

1. a finding cannot be explained with the current instrument
2. a Connectathon scenario requires another capability
3. another MediLacra/PIQITT experiment needs a reusable primitive
4. a repeated manual analysis is worth automating

Nat version:

> **Stop when the primitive is useful. Build the next layer when reality asks for it.**

---

# 14. Parked Phase 2 Ideas

These are intentionally **not commitments**. They are extension points we now understand well enough to preserve for later.

## 14.1 Richer semantic outcome classification

Possible conceptual states:

```text
PRESERVED
NORMALIZED
DEGRADED
LOST
SKIP
```

Use case: distinguish CWE → readable text from CWE → no surviving value.

Do not implement unless PASS / FAIL / SKIP starts obscuring real findings.

## 14.2 Explicit CWE / CNE transformation support

PIQITT could eventually preserve coded CWE/CNE values as FHIR `valueCodeableConcept` when code/system are present and retain human-readable text where needed.

This is primarily a PIQITT converter enhancement, not a SaSI requirement.

SaSI should measure the current behavior before and after any such change.

## 14.3 Transformation coverage metrics

Possible measures:

- supported message-family rate
- evaluated semantic opportunities
- unsupported semantic opportunities
- transformation coverage percentage

This would make fallback/skip-heavy transformations easier to summarize.

## 14.4 Cross-message integrity

Current SaSI evaluates one transformation event at a time.

Later, it could compare relationships across messages:

- same patient identity across ADT/ORU/DFT
- same encounter context
- placer/filler order continuity
- repeated demographic consistency
- expected message-family cardinalities

MediLacra could provide an optional truth sidecar for this without requiring a full Reality Model.

## 14.5 More statistical measures

Only add when simple retention + percentage-point drift are insufficient.

Possible methods:

- total variation distance
- Jensen-Shannon divergence
- confidence intervals
- chi-square comparisons
- seed-to-seed drift thresholds

No fancy statistics for the sake of fancy statistics.

## 14.6 Scale and performance characterization

Potential future runs:

```text
10K
100K
500K
1M entities
```

Potential measurements:

- SaSI messages/second
- memory behavior
- output size
- structural failure-rate stability
- distribution stability by scale and seed

This becomes useful if SaSI itself needs performance characterization or Connectathon demonstration at scale.

## 14.7 Streamlit / UI integration

Could add SaSI beside PIQI in the existing UI with:

- per-message structural findings
- PIQI/SaSI comparison
- summary tables
- downloadable findings

Parked because the CLI + Markdown/JSON output already solves the current need.

## 14.8 Findings catalog evolution

The `findings/` folder can become a lightweight evidence corpus:

```text
findings/
  YYYY-MM-DD_short_finding_name.md
```

Each finding should separate:

```text
observed
inferred
possible explanation
next test
```

This is likely more valuable than building a findings database right now.

## 14.9 Regression comparison

Later SaSI runs could compare results before and after converter changes:

- SAM failure-rate drift
- retention changes
- new/lost categories
- message-family coverage changes

Useful when PIQITT begins fixing findings that SaSI exposed.

## 14.10 Optional truth sidecar

MediLacra could eventually emit a tiny truth record containing identities, relationships, expected counts, and times.

That would allow SaSI to test not only HL7 → FHIR preservation but also whether the HL7 representation itself preserved generator truth.

This remains optional and should not become a full Reality Model project by accident.

---

# 15. V1 Non-Goals

Still out of scope:

- full HL7 conformance engine
- generalized terminology service
- full MediLacra Reality Model
- database persistence requirement
- machine learning
- probabilistic matching
- broad statistical hypothesis testing
- SaSI 0-100 score
- automated converter repair
- contest UI integration
- IRIS integration
- product-grade packaging
- product-grade UX
- feature completeness for its own sake

V1 is a measuring primitive.

---

# 16. MVP Status

The original MVP definition is met:

1. raw HL7 can be transformed normally by PIQITT
2. SaSI inventories source and target representations
3. SaSI executes the minimal structural profile
4. SaSI emits PASS / FAIL / SKIP details
5. SaSI output remains separate from PIQI
6. NDJSON results are generated
7. summaries aggregate by SAM, dimension, and message type
8. statistical retention and drift are reported
9. MediLacra-generated ADT, ORU, DFT, ORM, and lab ORU data can be exercised
10. real transformation-loss/degradation cases are exposed
11. existing PIQI behavior remains unchanged

**SaSI V1 MVP is operational and intentionally considered good enough for now.**

---

# 17. Current Next Step

There is no mandatory implementation next step.

The immediate mode is:

```text
use SaSI
collect findings
preserve findings
extend only when needed
```

If work resumes, the highest-value observational follow-up remains the CWE source→target inspection:

1. run representative CWE messages with inventories enabled
2. inspect exactly where the CWE source value lands in the FHIR Observation
3. classify the result as preserved, normalized, degraded, or lost
4. decide whether a converter change is warranted

But this is intentionally parked until there is a reason to continue.

---

# Decision Log

## D001 — Use the clean PIQITT repository
**Decision:** Build SaSI in the non-contest `piqitt` repository.  
**Status:** Accepted.

## D002 — Use a branch, not a separate repository
**Decision:** Develop on `sasi`.  
**Status:** Accepted.

## D003 — Name it SaSI
**Decision:** Structural and Statistical Integrity, pronounced "sassy."  
**Status:** Extremely accepted. 😹

## D004 — Keep SaSI separate from PIQI
**Decision:** SaSI results do not alter PIQI scoring.  
**Status:** Accepted.

## D005 — Use raw HL7 + generated FHIR as V1 input
**Decision:** No new MediLacra truth sidecar is required for V1.  
**Status:** Implemented.

## D006 — MediLacra is a test corpus, not a dependency
**Decision:** SaSI must work on arbitrary HL7 input.  
**Status:** Implemented.

## D007 — Structural analysis before statistical analysis
**Decision:** Trust message-level comparisons before adding batch-level statistics.  
**Status:** Implemented.

## D008 — Reuse the SAM pattern
**Decision:** Deterministic PASS / FAIL / SKIP assessments.  
**Status:** Implemented.

## D009 — Separate SaSI library and profile
**Decision:** Keep `sasi_sam_library.yaml` and `profile_sasi_minimal.yaml` separate from PIQI configuration.  
**Status:** Implemented.

## D010 — No SaSI 0-100 score in V1
**Decision:** Report interpretable counts, rates, dimensions, and evidence instead.  
**Status:** Implemented.

## D011 — Do not fix the converter while building SaSI
**Decision:** Preserve current PIQITT transformation behavior during instrumentation.  
**Status:** Implemented.

## D012 — Canonicalize semantic equivalents
**Decision:** Compare equivalent representations rather than raw strings, while preserving real semantic losses such as timezone stripping.  
**Status:** Implemented.

## D013 — Start with ten structural SAMs
**Decision:** Keep V1 deliberately small.  
**Status:** Implemented.

## D014 — Report retention and distribution drift separately
**Decision:** Statistical integrity must not let unchanged percentages hide uniform record loss.  
**Status:** Implemented.

## D015 — Preserve findings in the repository
**Decision:** Use `findings/` as a durable project evidence log.  
**Status:** Implemented.

## D016 — Separate PIQI terminology coverage from SaSI fidelity
**Decision:** Incomplete CPT/ICD/LOINC validation samples may affect PIQI but do not explain SaSI transformation findings.  
**Status:** Accepted.

## D017 — Treat CWE result as possible semantic degradation, not automatic total loss
**Decision:** A coded value flattened to text is different from a value disappearing entirely.  
**Status:** Accepted; deeper inspection parked.

## D018 — SaSI V1 is good enough for now
**Decision:** Stop active feature development after the operational MVP and first real corpus findings.  
**Reason:** The primitive is already useful. Additional work should be driven by real needs rather than product-completion pressure.  
**Status:** Accepted.

## D019 — Build primitives, not polished products
**Decision:** Prioritize small reusable capabilities, clear evidence, and composability over feature completeness, UI polish, packaging, or standalone-product maturity.  
**Reason:** SaSI's value is as a reusable measurement primitive inside broader interoperability experiments.  
**Status:** Accepted.

## D020 — Phase 2 is a parking lot, not a roadmap commitment
**Decision:** Preserve known extension ideas in documentation without treating them as required next work.  
**Reason:** Documenting the next abstraction is useful; building it before reality demands it is not.  
**Status:** Accepted.
