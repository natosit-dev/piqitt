# SaSI Project Plan
## Structural and Statistical Integrity for PIQITT

**Project:** SaSI ("sassy")  
**Repository:** `natosit-dev/piqitt`  
**Branch:** `sasi`  
**Status:** MVP implemented and initial corpus validated  
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

# 2. Architecture

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

# 3. V1 Evaluation Model

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

# 4. Source and Target Inventories

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

# 5. Canonicalization

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

# 6. Implementation Progress

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

# 7. Initial Corpus Results

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

# 8. What the First Findings Mean

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

This distinction is important. SaSI should tell the difference between:

```text
preserved
normalized
degraded
lost
```

Even if V1 continues using PASS / FAIL / SKIP internally.

---

# 9. PIQI Terminology Coverage vs SaSI Fidelity

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

# 10. Statistical Integrity Rule Learned During Testing

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

# 11. PIQI + SaSI Interpretation

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

# 12. V1 Non-Goals

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

V1 remains a measuring instrument.

---

# 13. MVP Status

The original MVP definition is now met:

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

**SaSI V1 MVP is operational.**

---

# 14. Next Work

Do not repair the converter yet.

Next observational steps:

1. run representative CWE messages with inventories enabled
2. inspect exactly where the CWE source value lands in the FHIR Observation
3. determine whether the value is preserved as text, partially preserved, or truly lost
4. decide whether SaSI should add a richer semantic classification such as `DEGRADED`, or keep PASS / FAIL / SKIP and carry degradation in evidence/meaning
5. keep PIQI terminology-reference coverage findings separate from SaSI transformation-fidelity findings
6. only after the CWE behavior is fully described, decide whether PIQITT should add explicit CWE/CNE coded-value conversion support

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

## D011 — Do not fix the converter while building the measuring instrument
**Decision:** Existing transformation behavior remains unchanged during V1 instrumentation.  
**Status:** Maintained.

## D012 — Canonicalize before comparison
**Decision:** Compare semantic equivalence rather than literal strings without hiding meaningful loss.  
**Status:** Implemented.

## D013 — Ten structural SAMs for V1
**Decision:** Start small enough to understand every result.  
**Status:** Implemented and validated.

## D014 — Count retention and distribution drift are separate measures
**Decision:** Statistical summaries report both.  
**Reason:** Uniform loss can preserve percentages while destroying records.  
**Status:** Implemented.

## D015 — Treat CWE behavior as degradation until inspected
**Decision:** Do not call the 600 coded values simply "lost" yet. The confirmed result is that they were not retained as FHIR `valueCodeableConcept`.  
**Reason:** CWE intentionally supports coded-or-text reality; the resulting human-readable value may still exist in a less structured representation.  
**Status:** Accepted; detailed inspection pending.

## D016 — Keep terminology coverage separate from transformation fidelity
**Decision:** PIQI sample-reference limitations and SaSI transformation findings are different failure surfaces.  
**Status:** Accepted.

## D017 — Findings are first-class project artifacts
**Decision:** Preserve observed results in `findings/`.  
**Status:** Implemented.
