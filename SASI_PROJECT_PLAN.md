# SaSI Project Plan
## Structural and Statistical Integrity for PIQITT

**Project:** SaSI ("sassy")  
**Repository:** `natosit-dev/piqitt`  
**Branch:** `sasi`  
**Status:** Planning / pre-implementation  
**Date:** 2026-08-18

---

# Prompt History

## Prompt 1

> While I'm gone, think about other data we could pull from this without changing what's working now. Look at the PIQITT and PIQITT-CONTEST repos. Consider what MediLacra is doing. I'm thinking we could come up with a custom SAM evaluator to bolt on?

## Prompt 2

> I think we should bolt a fork onto the non contest repo first. The contest was messy and fast. Let's map out the analyzer function- source, input, evaluations, definitions, workflow, output, meaning of output. Use Nat language along with the actual fancy words

## Prompt 3

> No, we're going to give it an awesome name.
> Structural and Statistical Integrity, but we can can call it SaSI 😹 (sassy)
> So we have PIQI- picky
> PIQITT- pick it
> SaSI- sassy
> Gotta keep myself amused! 😁😁

## Prompt 4

> Ok, put that all in an MD, create the SaSI fork, and drop in the documentation

## Prompt 5

> Ah, yeah a branch is what I meant anyways. I think I should pull a fresh copy to my machine. Give me the commands

## Prompt 6

> Ok, now what are the changes we need for SaSI?

## Prompt 7

> Ok, put together a project plan for how we will do this. Include a decision log at the bottom and my prompts at the top. Create a new MD in the SaSI branch and drop it in. Once I review, you'll go make the changes

---

# 1. Project Purpose

SaSI stands for **Structural and Statistical Integrity**.

SaSI will be added beside PIQI in the clean PIQITT codebase.

PIQI asks:

> Is the transformed healthcare data good according to the configured data-quality assessments?

SaSI asks:

> Did the important structure, relationships, values, counts, and distributions survive the transformation?

Nat version:

> **What went in, what came out, and did PIQITT quietly eat or distort anything important?**

The central idea is to measure **transformation fidelity** rather than only downstream data quality.

Fancy version:

> SaSI evaluates structural invariants, referential integrity, cardinality preservation, semantic equivalence, and statistical distribution preservation across a healthcare-data transformation.

Nat version:

> **Same important stuff, same important relationships, same population shape.**

---

# 2. Why SaSI Is Separate from PIQI

SaSI should not be merged into PIQI scoring.

They answer different questions.

## PIQI

Measures the quality of the resulting data.

Examples:

- required value present
- code valid
- value plausible
- unit acceptable
- field conforms to a configured rule

## SaSI

Measures whether the transformation preserved the source.

Examples:

- 27 OBX segments became 27 Observations
- an HL7 code survived as the equivalent FHIR code
- references still point to the correct Patient or Encounter
- a message type was actually supported rather than silently reduced to a fallback
- source and target distributions remain aligned at scale

The important distinction is:

```text
PIQI:
How good is the resulting data?

SaSI:
Is the resulting data still faithfully representing what went in?
```

A high PIQI score does not prove high transformation fidelity.

---

# 3. Current Architecture

PIQITT currently has a simple architecture:

```text
HL7 v2
   ↓
FHIR conversion
   ↓
FHIR Bundle
   ↓
PIQI evaluator
   ↓
PIQI result
```

SaSI will extend the pipeline without replacing it:

```text
HL7 v2
   │
   ├────────────── source representation
   │
   ▼
PIQITT conversion
   │
   ▼
FHIR Bundle
   │
   ├── PIQI evaluator
   │      └── data quality
   │
   └── SaSI analyzer
          └── structural + statistical integrity
```

SaSI must see both sides of the transformation:

```text
raw HL7
+
generated FHIR Bundle
```

PIQI can continue seeing only the resulting FHIR Bundle.

---

# 4. Core Design Principle

## Do not fix the thing while building the measuring instrument

The first SaSI implementation should observe current PIQITT behavior.

It should not simultaneously change:

- HL7 → FHIR mappings
- PIQI scoring
- Clinical-Minimal profile logic
- Claims-Minimal profile logic
- unsupported message behavior
- MediLacra output
- contest UI behavior
- IRIS behavior

This lets existing quirks become useful test cases.

Example:

If ORM currently falls through a generic conversion path and receives a high PIQI score because most clinical content never reaches the evaluator, that is useful SaSI evidence.

SaSI should detect the transformation loss before we decide how PIQITT should fix it.

---

# 5. Unit of Analysis

The primitive SaSI evaluation unit is:

> **One raw HL7 message and the FHIR Bundle produced from that message.**

Fancy term:

**Transformation event**

Nat version:

> **One thing PIQITT did.**

Conceptual input:

```text
TransformationInput

source_hl7
source_message_type
source_file
source_index
fhir_bundle
```

The first version does not require MediLacra ground-truth metadata.

Later, an optional `generator_truth` sidecar can be added.

---

# 6. SaSI Evaluation Model

SaSI will borrow PIQITT's SAM pattern.

A SaSI SAM asks one small deterministic question.

Fancy definition:

> A SaSI assessment module evaluates an invariant or expected mapping relationship between source and target representations.

Nat definition:

> **One small question about whether a particular thing survived the trip.**

Initial result vocabulary:

```text
PASS
FAIL
SKIP
```

Each SaSI detail record should contain enough information to explain the result.

Example shape:

```json
{
  "sam": "XFORM_OBXCardinalityPreserved",
  "dimension": "Structural.Cardinality",
  "status": "PASS",
  "sourcePath": "OBX",
  "targetPath": "Observation",
  "sourceValue": 27,
  "targetValue": 27
}
```

---

# 7. Source Semantic Inventory

SaSI first needs to inventory the source HL7 message.

Fancy term:

**Source semantic inventory**

Nat version:

> **Write down what actually went in.**

Initial source inventory should extract:

- message type
- segment counts
- PID identity values
- PV1 encounter values
- OBR/order identifiers where useful
- OBX count
- OBX codes
- OBX values
- OBX units
- OBX timestamps
- FT1 count
- FT1 values needed for structural comparison

The inventory should be deterministic and small.

It does not need to become a complete HL7 parser.

SaSI should reuse the existing PIQITT parsing helpers wherever possible.

---

# 8. Target Semantic Inventory

SaSI also inventories the generated FHIR Bundle.

Fancy term:

**Target semantic inventory**

Nat version:

> **Write down what came out.**

Initial target inventory should extract:

- resource counts by `resourceType`
- Patient values
- Encounter values
- Observation count
- Observation codes
- Observation values
- Observation units
- Observation timestamps
- Claim count
- important references between resources

This gives SaSI two comparable descriptions:

```text
source inventory
target inventory
```

The SAM layer then evaluates relationships between them.

---

# 9. Canonicalization and Semantic Equivalence

Source and target values may be semantically equal without being textually identical.

SaSI therefore needs a small normalization layer.

Fancy term:

**Canonicalization**

Nat version:

> **Make equivalent shit look equivalent before comparing it.**

Initial normalizers:

```text
normalize_code_system()
normalize_timestamp()
normalize_numeric()
normalize_text()
```

Examples:

```text
LN
```

and

```text
http://loinc.org
```

should compare as equivalent.

Likewise:

```text
20260818122030
```

and

```text
2026-08-18T12:20:30Z
```

may represent the same timestamp.

SaSI should test semantic preservation, not byte equality.

---

# 10. Structural Integrity Dimensions

The first SaSI release should focus primarily on structural integrity.

## 10.1 Transformation Support

Question:

> Did PIQITT actually understand this message type?

Initial SAM:

```text
XFORM_MessageTypeSupported
```

Examples:

- ADT → supported
- ORU → supported
- DFT → supported
- unsupported/fallback path → fail

Meaning:

A message should not receive an apparently strong downstream quality result if most of its intended semantics were never transformed.

---

## 10.2 Presence / Semantic Retention

Question:

> Did a source concept that should have a target representation survive?

Initial SAMs may include:

```text
XFORM_PatientPreserved
XFORM_EncounterPreserved
```

Nat version:

> **Did the thing disappear?**

---

## 10.3 Cardinality Preservation

Fancy term:

**Cardinality preservation**

Nat version:

> **If five things went in, did five things come out?**

Initial SAMs:

```text
XFORM_OBXCardinalityPreserved
XFORM_FT1CardinalityPreserved
```

Examples:

```text
27 OBX
→
27 Observation
= PASS
```

```text
2 FT1
→
1 Claim
= FAIL
```

---

## 10.4 Code Preservation

Question:

> Did the source terminology survive as an equivalent target terminology representation?

Initial SAM:

```text
XFORM_CodePreserved
```

This should compare:

- code
- system
- display where appropriate

The important distinction is:

```text
equivalent != identical
```

Normalization is allowed.

Semantic mutation is not.

---

## 10.5 Value Preservation

Question:

> Did the actual value survive?

Initial SAM:

```text
XFORM_ValuePreserved
```

Example:

```text
OBX-5 = 81.36
→
Observation.valueQuantity.value = 81.36
```

PASS.

---

## 10.6 Unit Preservation

Question:

> Did the measurement unit survive transformation?

Initial SAM:

```text
XFORM_UnitPreserved
```

Normalization may be allowed where equivalent representations exist.

---

## 10.7 Temporal Preservation

Question:

> Did the effective/result time retain the same meaning?

Initial SAM:

```text
XFORM_EffectiveTimePreserved
```

This should tolerate formatting normalization.

---

## 10.8 Referential Integrity

Fancy term:

**Referential integrity**

Nat version:

> **Do the pieces still point at the right shit?**

Initial SAM:

```text
XFORM_ReferencesResolve
```

Examples:

```text
Observation.subject → Patient/pat-123
```

SaSI verifies that `Patient/pat-123` exists in the Bundle.

Later versions can test whether the source relationship itself was preserved, not only whether the FHIR reference resolves.

---

# 11. Statistical Integrity

Statistical integrity is part of SaSI, but it should be implemented after message-level structural analysis works.

Fancy definition:

> Statistical integrity measures whether aggregate properties of a source population remain materially stable after transformation.

Nat version:

> **Did the individual rows survive, but the population shape get weird?**

Initial comparison candidates:

- PID sex distribution
- Gender Identity distribution
- pronoun distribution
- SPCU distribution
- diagnosis distribution
- CPT distribution
- resource-count distribution
- message-type distribution
- SAM PASS/FAIL/SKIP rates

Initial reporting can remain simple:

```text
source %
target %
delta percentage points
```

Example:

```text
Non-binary Gender Identity

Source: 3.02%
Target: 3.01%
Delta: -0.01 percentage points
```

Advanced statistical methods should not be part of V1.

Possible later methods:

- total variation distance
- Jensen-Shannon divergence
- chi-square testing
- confidence intervals
- distributional regression thresholds

---

# 12. Proposed V1 SaSI SAM Set

The first implementation should stay deliberately small.

Proposed V1:

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

Ten SAMs are enough to create a real measuring instrument.

More SAMs should be added only after running these against real generated corpora.

---

# 13. Proposed File Changes

Initial repository shape:

```text
piqitt/
│
├── scripts/
│   ├── fhir_convert_backend.py       existing
│   ├── piqi_eval.py                  existing
│   │
│   ├── sasi_analyzer.py              NEW
│   ├── sasi_sams.py                  NEW
│   └── sasi_summary.py               NEW, after message-level MVP
│
├── profiles/
│   ├── profile_clinical_minimal.yaml
│   ├── profile_claims_minimal.yaml
│   └── profile_sasi_minimal.yaml     NEW
│
├── piqi_sam_library.yaml
├── sasi_sam_library.yaml             NEW
│
├── SASI_STRUCTURAL_AND_STATISTICAL_INTEGRITY.md
└── SASI_PROJECT_PLAN.md              NEW
```

The SaSI SAM library should remain separate from the PIQI SAM library.

Reason:

> Related machinery does not mean identical semantics.

PIQI and SaSI should remain independently interpretable.

---

# 14. Implementation Phases

## Phase 0 — Freeze Baseline

Before changing conversion behavior:

- preserve current PIQITT behavior
- preserve current PIQI results
- keep current MediLacra benchmark artifacts
- use known quirks as SaSI test cases

Goal:

> establish the thing we are measuring before modifying it

---

## Phase 1 — Source Inventory

Build reusable source extraction.

Tasks:

1. receive raw HL7
2. reuse existing PIQITT parsing helpers
3. extract message type
4. count relevant segments
5. extract selected PID/PV1/OBX/FT1 fields
6. return a deterministic source-inventory object

Output:

```text
source_inventory
```

Validation:

- manually inspect tiny ADT
- manually inspect tiny ORU
- manually inspect tiny DFT
- inspect unsupported/fallback message

---

## Phase 2 — Target Inventory

Build FHIR Bundle extraction.

Tasks:

1. count resources by type
2. extract Patient
3. extract Encounter
4. extract Observations
5. extract Claims
6. extract important references
7. return deterministic target inventory

Output:

```text
target_inventory
```

Validation:

Compare inventory against known PIQITT conversion output.

---

## Phase 3 — Normalization Layer

Implement small semantic normalizers.

Tasks:

```text
code-system canonicalization
timestamp canonicalization
numeric comparison normalization
basic string normalization
```

Do not build a generalized terminology service.

Goal:

> enough normalization to compare what PIQITT currently transforms

---

## Phase 4 — SaSI Result Schema

Create the stable result shape before adding many assessments.

Message-level result should include:

```json
{
  "messageType": "ORU^R01",
  "sourceFile": "example.hl7",
  "sourceIndex": 1,
  "evaluations": 10,
  "passes": 8,
  "fails": 1,
  "skips": 1,
  "details": []
}
```

Do not create a 0–100 SaSI score in V1.

Raw evaluation counts and rates are more informative while the ontology is still being tested.

---

## Phase 5 — Structural SAM Implementation

Implement the V1 SAM set in increasing complexity.

Recommended order:

```text
1. XFORM_MessageTypeSupported
2. XFORM_PatientPreserved
3. XFORM_EncounterPreserved
4. XFORM_OBXCardinalityPreserved
5. XFORM_FT1CardinalityPreserved
6. XFORM_CodePreserved
7. XFORM_ValuePreserved
8. XFORM_UnitPreserved
9. XFORM_EffectiveTimePreserved
10. XFORM_ReferencesResolve
```

Run tiny deterministic messages after each addition.

---

## Phase 6 — SaSI Profile and Library

Create:

```text
sasi_sam_library.yaml
profiles/profile_sasi_minimal.yaml
```

Goal:

Preserve the good PIQITT pattern:

```text
logic in Python
assessment definition/configuration in YAML
```

The profile determines which SaSI checks apply to which message shapes.

---

## Phase 7 — PIQITT Orchestration Hook

Wire SaSI into the existing transformation workflow.

Conceptual flow:

```python
bundle, msg_type = convert_message_to_bundle(msg)

sasi = sasi_analyzer.evaluate(
    raw_hl7=msg,
    bundle=bundle,
    message_type=msg_type,
)

piqi = evaluator.evaluate_bundle(
    bundle,
    profile_name,
)
```

SaSI must not mutate the Bundle before PIQI evaluates it.

SaSI and PIQI results should remain separate.

---

## Phase 8 — NDJSON Output

Add an output stream for SaSI results.

Example:

```text
sasi_results.ndjson
```

Each line:

```text
one source message
one transformation
one SaSI result
```

This makes large-scale analysis easy without requiring a database.

---

## Phase 9 — Summary Analyzer

Add:

```text
scripts/sasi_summary.py
```

Initial summaries:

```text
By message type
By source file
By SAM
By SaSI dimension
PASS rate
FAIL rate
SKIP rate
```

Then add source/target distribution comparison.

---

## Phase 10 — MediLacra Corpus Test

Run SaSI against the existing MediLacra-generated HL7 corpus.

MediLacra's role:

> controlled synthetic source corpus

Not:

> a hard dependency of SaSI

Use known message families:

```text
ADT
ORU
DFT
ORM
ORU_LABS
```

Important first questions:

- which message types are truly supported?
- where does cardinality change?
- which fields normalize cleanly?
- where does information disappear?
- where do FHIR references fail?
- does population shape remain stable?

---

# 15. Testing Strategy

## Tiny Tests First

Use one or a few messages per type.

Purpose:

- inspect source inventory
- inspect target inventory
- verify SAM mechanics
- explain every failure manually

## Regression Corpus

Use a small seeded MediLacra run.

Purpose:

- stable repeatable behavior
- fast enough to rerun frequently

## Scale Tests

After structural behavior is trusted:

```text
10K
100K
500K
1M entity benchmark
```

SaSI should then measure:

- evaluation throughput
- memory behavior
- output size
- result stability
- statistical drift
- structural drift by scale

---

# 16. Meaning of SaSI Output

SaSI must remain interpretable without a magic score.

Example:

```text
Message type: ORU^R01

10 evaluations
8 PASS
1 FAIL
1 SKIP
```

Meaning:

> Eight explicitly tested transformation invariants were preserved, one was not preserved, and one could not be meaningfully evaluated.

The output does not mean:

> This data is 80% correct.

That distinction should remain explicit in documentation and UI.

---

# 17. PIQI + SaSI Interpretation Matrix

| PIQI | SaSI | Meaning |
|---|---|---|
| High | High | Good transformation producing good resulting data |
| Low | High | Source problems were faithfully preserved |
| High | Low | Clean-looking result after transformation loss or distortion |
| Low | Low | Poor source quality and/or poor transformation |

The most important quadrant is:

```text
High PIQI
Low SaSI
```

Fancy term:

**Transformation-induced false confidence**

Nat version:

> **We dropped the ugly parts and then congratulated ourselves on how clean the remainder is.**

---

# 18. Gender Harmony as a SaSI Test Case

Gender Harmony data is useful because the generated data deliberately contains heterogeneous and sometimes discordant semantic values.

SaSI should not assert:

> Gender identity must match administrative sex.

That would be wrong.

Instead SaSI can measure whether:

- Gender Identity survived
- pronouns survived
- SPCU survived
- code/system/display relationships survived
- source and target category distributions remain aligned
- rare categories were not silently lost

This is a good example of why statistical integrity matters.

A transform can preserve common categories while disproportionately losing rare ones.

---

# 19. Explicit Non-Goals for V1

Do not add these yet:

- complete HL7 conformance engine
- generalized terminology server
- full MediLacra Reality Model
- database persistence requirement
- machine learning
- probabilistic matching
- broad statistical hypothesis-testing framework
- new PIQI score semantics
- SaSI 0–100 index
- automated correction of PIQITT mappings
- contest UI integration
- IRIS integration

V1 is a measuring instrument.

---

# 20. Definition of MVP Complete

SaSI MVP is complete when:

1. PIQITT accepts a raw HL7 message.
2. PIQITT produces its normal FHIR Bundle.
3. SaSI inventories source and target representations.
4. SaSI executes the minimal structural profile.
5. SaSI emits PASS / FAIL / SKIP detail records.
6. SaSI results are written independently from PIQI.
7. A small summary script can aggregate results by SAM and message type.
8. MediLacra-generated ADT, ORU, DFT, ORM, and ORU_LABS data can be run through it.
9. At least one known transformation-loss case is correctly exposed.
10. Existing PIQI behavior remains unchanged.

At that point SaSI is real.

Everything after that is expansion.

---

# 21. Expected First Useful Result

The first useful result is not:

> SaSI score = 94.7

It is something like:

```text
ORU^R01
OBX cardinality: PASS
code preservation: PASS
value preservation: PASS
unit preservation: PASS
references: PASS

ORM^O01
message support: FAIL
clinical semantic retention: FAIL
PIQI downstream result: high
```

That result immediately demonstrates why SaSI exists.

---

# 22. Working Philosophy

SaSI should follow the same principle that made the MediLacra experiments useful:

> Build a controlled system, observe it directly, and preserve enough detail to explain the result.

And:

> We solve problems once.

SaSI should therefore reuse:

- PIQITT HL7 parsing
- PIQITT FHIR conversion output
- PIQITT SAM-style result grammar
- YAML configuration patterns
- MediLacra as an existing synthetic-data test rig

No duplicate parser stack unless the existing parser cannot expose what SaSI needs.

---

# Decision Log

## D001 — Use the clean PIQITT repository

**Decision:** Build SaSI in a branch of the non-contest `piqitt` repository.

**Reason:** `piqitt-contest` was intentionally fast and messy. The clean PIQITT repo already has the reusable evaluator/profile architecture SaSI should extend.

**Status:** Accepted.

---

## D002 — Branch rather than separate repository

**Decision:** Use the `sasi` branch in `natosit-dev/piqitt`.

**Reason:** SaSI is an extension of PIQITT and should remain close to the transformation code while its architecture is being proven.

**Status:** Accepted.

---

## D003 — Name the analyzer SaSI

**Decision:** Name the project **Structural and Statistical Integrity (SaSI)**, pronounced "sassy."

**Reason:** Accurate technical name, memorable shorthand, and consistent with PIQI ("picky") and PIQITT ("pick it").

**Status:** Extremely accepted. 😹

---

## D004 — Keep SaSI separate from PIQI scoring

**Decision:** SaSI results will not be folded into PIQI scores.

**Reason:** PIQI measures resulting-data quality. SaSI measures transformation fidelity and aggregate preservation.

**Status:** Accepted.

---

## D005 — Use raw HL7 + FHIR Bundle as V1 input

**Decision:** SaSI will compare the raw source message directly to PIQITT's generated FHIR Bundle.

**Reason:** The required data already exists in the current workflow. No MediLacra changes are necessary for V1.

**Status:** Accepted.

---

## D006 — MediLacra is a test corpus, not a dependency

**Decision:** SaSI must work independently of MediLacra.

**Reason:** MediLacra provides a powerful controlled synthetic corpus, but SaSI should remain a PIQITT capability usable on arbitrary HL7 input.

**Status:** Accepted.

---

## D007 — Structural analysis before statistical analysis

**Decision:** Implement message-level structural integrity first, then batch-level statistical integrity.

**Reason:** Statistical conclusions are only useful once source/target extraction and message-level transformation comparisons are trusted.

**Status:** Accepted.

---

## D008 — Reuse the SAM pattern

**Decision:** SaSI will use deterministic SAM-like assessments returning PASS / FAIL / SKIP.

**Reason:** This preserves a proven PIQITT pattern while keeping SaSI semantics separate.

**Status:** Accepted.

---

## D009 — Separate SaSI SAM library and profile

**Decision:** Create `sasi_sam_library.yaml` and `profile_sasi_minimal.yaml` rather than mixing SaSI rules into PIQI configuration.

**Reason:** Shared machinery should not blur distinct measurement domains.

**Status:** Accepted.

---

## D010 — No SaSI 0–100 score in V1

**Decision:** V1 will report counts, rates, dimensions, and detailed SAM results rather than a single SaSI index.

**Reason:** A magic score would hide exactly the transformation behavior SaSI is being built to expose.

**Status:** Accepted.

---

## D011 — Preserve existing transformation behavior during instrumentation

**Decision:** Do not fix known PIQITT transformation problems during the first SaSI implementation.

**Reason:** Existing behavior provides baseline test cases and lets SaSI prove that it can identify transformation loss.

**Status:** Accepted.

---

## D012 — Canonicalize before comparison

**Decision:** SaSI compares semantic equivalence rather than raw string equality.

**Reason:** Legitimate transformation changes representation format, such as `LN` → `http://loinc.org` or HL7 timestamps → FHIR dateTime.

**Status:** Accepted.

---

## D013 — First implementation target is ten structural SAMs

**Decision:** Start with the ten-SAM minimal set defined in this plan.

**Reason:** Enough surface area to make SaSI real without prematurely building a generalized interoperability framework.

**Status:** Accepted pending implementation review.

---

# Next Step

Review this plan.

After review, implementation begins on the `sasi` branch.

The first code change should be the source and target inventory layer, not the SAM library itself.

That keeps the comparison substrate visible and testable before assessment logic is stacked on top.
