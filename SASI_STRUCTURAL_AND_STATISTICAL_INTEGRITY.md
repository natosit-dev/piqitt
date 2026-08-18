# SaSI — Structural and Statistical Integrity

**Pronounced:** “sassy” 😹

## Naming Family

- **PIQI** — “picky” — Patient Information Quality Improvement
- **PIQITT** — “pick it” — PIQI Transformation Tool
- **SaSI** — “sassy” — Structural and Statistical Integrity

The names are allowed to be useful *and* amusing.

---

## 1. Purpose

PIQI and SaSI answer different questions.

**PIQI asks:**

> Is the resulting healthcare data good according to the configured assessment rules?

**SaSI asks:**

> What happened to the information while PIQITT transformed it?

Or, in Nat language:

> What went in, what came out, and did we accidentally eat anything important?

SaSI measures whether important properties remain intact across a representation change. The fancy word is **invariance**: which properties survive the transformation unchanged in meaning, even when their syntax changes.

SaSI intentionally sits **beside** PIQI. It does not redefine PIQI, inflate PIQI with generator-specific checks, or turn one number into a description of five different things.

```text
HL7 v2
   │
   ├─────────────── source representation
   │
   ▼
PIQITT converter
   │
   ├─────────────── transformation
   │
   ▼
FHIR Bundle
   │
   ├── PIQI evaluator
   │      └── data quality
   │
   └── SaSI evaluator
          └── structural + statistical integrity
```

---

## 2. What SaSI Measures

SaSI has two top-level domains.

### Structural Integrity

Structural integrity asks whether the pieces and their important relationships survived transformation.

Examples:

- Did a supported HL7 message produce the expected FHIR resource family?
- If 27 OBX segments went in, did 27 Observations come out?
- Did patient identity survive?
- Did encounter context survive?
- Did codes, values, units, and timestamps survive?
- Do FHIR references still resolve to the correct resources?
- Did information silently disappear?

### Statistical Integrity

Statistical integrity asks whether population-level signals survive processing and aggregation.

Examples:

- Did category proportions remain stable?
- Did rare categories survive?
- Did code frequencies drift?
- Did the proportion of PASS/FAIL/SKIP outcomes change unexpectedly with scale?
- Did a transformation distort a distribution even when individual records still look valid?

Nat version:

> Structural integrity checks whether the individual Lego pieces and connections survived. Statistical integrity checks whether the pile still has the same shape when you zoom out.

---

## 3. Source

SaSI V1 requires no change to MediLacra.

The necessary source material already exists at the PIQITT transformation boundary:

1. the **raw HL7 v2 message**, and
2. the **FHIR Bundle PIQITT produced from that message**.

PIQITT already performs:

```text
raw HL7
   ↓
convert_message_to_bundle(...)
   ↓
FHIR Bundle
```

SaSI simply receives both sides of that transformation.

Conceptually:

```python
bundle, message_type = convert_message_to_bundle(raw_hl7)

piqi = evaluator.evaluate_bundle(bundle, profile)

sasi = analyzer.evaluate(
    raw_hl7=raw_hl7,
    bundle=bundle,
    message_type=message_type,
)
```

Nothing upstream needs to change for V1.

---

## 4. Input

The primitive SaSI input is one **transformation event**.

Fancy term: **evaluation unit**.

Nat term:

> One thing PIQITT did.

Suggested conceptual input:

```text
TransformationInput

source_hl7
source_message_type
source_file
source_index

fhir_bundle
```

A future version may optionally accept:

```text
generator_truth
```

But generator truth is explicitly **not required for V1**.

### Grain

The first evaluation grain is:

> **One HL7 message and the FHIR Bundle produced from it.**

Patient, file, facility, message type, and benchmark run are aggregation grains above that.

```text
SaSI result
    ↓
message transformation
    ↓
file
    ↓
message type
    ↓
sending facility
    ↓
benchmark run
```

---

## 5. SaSI Assessment Module

SaSI should reuse the useful grammar of PIQI SAMs without pretending transformation-fidelity checks are PIQI measures.

Each SaSI assessment returns:

```text
PASS
FAIL
SKIP
```

with metadata such as:

```text
mnemonic
dimension
source_path
target_path
source_value
target_value
meaning
```

### Definition

**Fancy definition:**

> A SaSI assessment module is a deterministic assessment of an invariant, expected mapping relationship, structural property, or statistical property across representations.

**Nat definition:**

> One small question about whether a particular thing survived the trip.

---

## 6. Structural Evaluation Dimensions

### 6.1 Transformation Support

**Fancy:** representational coverage / transformation support.

**Question:**

> Did PIQITT actually recognize this thing?

Example SAM:

```text
SaSI_MessageTypeSupported
```

An unsupported message must not receive accidental credit merely because a small subset of easy fields survived a generic fallback path.

---

### 6.2 Presence / Semantic Retention

**Fancy:** semantic retention.

**Question:**

> Something existed in HL7. Is there a corresponding thing in FHIR?

Examples:

```text
SaSI_PatientPreserved
SaSI_EncounterPreserved
SaSI_ObservationPreserved
SaSI_TransactionPreserved
```

Nat version:

> Did the thing fucking disappear?

---

### 6.3 Cardinality Preservation

**Definition:**

> Cardinality preservation measures whether multiplicity survives transformation.

Nat version:

> If five things went in, did five things come out?

Example:

```text
HL7:
27 OBX

FHIR:
27 Observation

PASS
```

Possible SAMs:

```text
SaSI_OBXCardinalityPreserved
SaSI_FT1CardinalityPreserved
```

This is stronger than simply checking whether *an* Observation or Claim exists.

---

### 6.4 Value Preservation

**Fancy:** value invariance.

**Question:**

> Did the actual value survive?

Example:

```text
OBX-5 = 132

FHIR:
Observation.valueQuantity.value = 132
```

Possible SAMs:

```text
SaSI_ObservationValuePreserved
SaSI_IdentifierValuePreserved
```

---

### 6.5 Terminology Preservation

**Fancy:** terminological fidelity.

**Question:**

> Did the code, system, and display preserve the same clinical concept?

Example source:

```text
8480-6^Systolic BP^LN
```

Possible FHIR target:

```text
code:    8480-6
system:  http://loinc.org
display: Systolic BP
```

These are not syntactically identical, but they are semantically equivalent.

That distinction matters:

```text
equivalent != identical
```

SaSI should treat legitimate **normalization** or **canonicalization** as preservation, not corruption.

Nat version:

> We changed how it looks, not what it means.

Potential terminology outcomes can remain PASS/FAIL/SKIP in V1. A later version could add explanatory sub-statuses such as `PRESERVED`, `NORMALIZED`, `ALTERED`, and `LOST` without changing the primary evaluation grammar.

---

### 6.6 Referential Integrity

Individual FHIR resources can each be valid while the relationships between them are wrong.

Fancy term: **referential integrity**.

Nat version:

> Do the pieces still point at the right shit?

Example relationship:

```text
Patient
   ↑
Encounter
   ↑
Observation
```

Possible SAMs:

```text
SaSI_ReferenceResolves
SaSI_PatientEncounterLinkPreserved
SaSI_ObservationEncounterLinkPreserved
```

This is also a legitimate use of the phrase **topological preservation**: the important nodes and connections of the resource graph remain intact.

Nat version:

> Same nodes, same important connections.

---

### 6.7 Temporal Preservation

Dates and timestamps frequently change syntax during transformation.

Example:

```text
20260817142530
```

may legitimately become:

```text
2026-08-17T14:25:30Z
```

A SaSI temporal check asks whether the same time meaning survived canonicalization.

Possible SAM:

```text
SaSI_EffectiveTimePreserved
```

---

### 6.8 Silent Loss

Silent loss deserves its own dimension.

It does not ask:

> Is the FHIR valid?

or:

> Did PIQI like the result?

It asks:

> Did PIQITT receive information that disappeared during transformation without making that loss visible?

Suggested dimension:

```text
Transformation.SilentLoss
```

Possible SAM:

```text
SaSI_NoSilentLoss
```

For V1, this should remain coarse and deterministic: known source structure, expected target structure, expected value or relationship.

---

## 7. Statistical Evaluation Dimensions

Structural checks operate on one transformation event. Statistical checks operate over collections of events.

### 7.1 Distribution Preservation

**Fancy:** distributional fidelity.

**Question:**

> Did the proportions of meaningful categories remain stable after transformation?

Examples:

- administrative sex distribution
- Gender Harmony category distribution
- diagnosis distribution
- code-system distribution
- message-type distribution
- PASS/FAIL/SKIP distribution

A statistical comparison should use tolerance bands rather than requiring exact equality when sampling variation is expected.

---

### 7.2 Rare-Category Retention

Common categories can hide selective loss of uncommon values.

SaSI should explicitly report whether rare categories present upstream remain visible downstream.

Nat version:

> Did the weird 0.5% case survive, or did the pipeline quietly round reality back into the common buckets?

---

### 7.3 Scale Stability

SaSI can compare the same workload shape at increasing scale.

Examples:

```text
100 messages
10,000 messages
100,000 messages
500,000+ messages
```

Question:

> Do structural and statistical results stay stable as volume increases?

Fancy term: **scale-dependent drift**.

Nat version:

> Does the system start lying differently when we make it work harder?

---

### 7.4 Seed / Cohort Stability

Synthetic generation allows repeated cohorts with controlled seeds.

SaSI can distinguish:

- expected population variation,
- transformation behavior,
- evaluator drift.

This supports **distributional regression testing**: compare rates and distributions instead of requiring identical message IDs.

---

## 8. Workflow

The initial workflow should be mechanically boring.

```text
1. Receive raw HL7 message
        ↓
2. Parse HL7
        ↓
3. PIQITT converts it normally
        ↓
4. SaSI inventories source semantics
        ↓
5. SaSI inventories target semantics
        ↓
6. Run structural SaSI assessments
        ↓
7. Produce message-level SaSI result
        ↓
8. Existing PIQI evaluator runs normally
        ↓
9. Aggregator summarizes PIQI + SaSI
        ↓
10. Statistical SaSI assessments run across the batch
```

PIQI and SaSI can technically execute in either order after conversion. Conceptually, the clean sequence is:

```text
convert
analyze transformation
assess resulting data quality
```

because those are different stages of meaning.

---

## 9. Output

SaSI V1 should **not** begin with another magic 0–100 score.

Start with transparent counts and assessment records.

Example message-level output:

```json
{
  "messageType": "ORU^R01",
  "sourceFile": "ORU_20260817.hl7",
  "sourceIndex": 12,
  "evaluations": 37,
  "passes": 35,
  "fails": 2,
  "skips": 0,
  "details": [
    {
      "sam": "SaSI_OBXCardinalityPreserved",
      "dimension": "Structural.Cardinality",
      "status": "PASS",
      "sourceValue": 27,
      "targetValue": 27
    }
  ]
}
```

### Aggregations

SaSI should support aggregation by:

```text
message type
file
SAM
dimension
source field
target resource
sending facility
benchmark run
```

### Candidate Summary Measures

Only after the underlying records exist should SaSI calculate summary rates such as:

```text
semantic retention rate
cardinality preservation rate
terminology preservation rate
reference integrity rate
unsupported transformation rate
silent-loss rate
distribution drift
rare-category retention
```

These rates must remain decomposable back to their assessment records.

---

## 10. Meaning of the Output

PIQI and SaSI must never be treated as interchangeable.

### PIQI

A PIQI result means approximately:

> The resulting data performed this well against the configured PIQI assessments.

### SaSI

A SaSI result means approximately:

> This proportion of explicitly tested structural, semantic, and statistical properties survived transformation.

### Combined Interpretation

| PIQI | SaSI | Meaning |
|---|---|---|
| High | High | Good transformation producing good downstream data |
| Low | High | Input problems were faithfully preserved |
| High | Low | Dangerous: clean-looking output after information loss or distortion |
| Low | Low | Bad input, bad transformation, or both |

The most interesting quadrant is:

```text
HIGH PIQI
LOW SaSI
```

Fancy phrase:

> **Transformation-induced false confidence.**

Nat version:

> We dropped the ugly parts and then congratulated ourselves on how clean the remainder is.

---

## 11. Why MediLacra Is Useful

SaSI must not depend on MediLacra, but MediLacra is an unusually useful test source because it generates linked synthetic healthcare data with known relationships and controlled distributions.

The current batch path already produces linked:

- patients,
- encounters,
- observations,
- transactions,
- ADT,
- ORU,
- DFT,
- ORM lab orders,
- ORU lab results,
- vitals,
- Gender Harmony values.

The same generated encounter can be projected into multiple message representations, making it possible to test cross-message coherence later.

MediLacra therefore gives SaSI something rare in healthcare interoperability:

> A synthetic source corpus where we can know what was supposed to survive the transformation.

### Future Ground-Truth Sidecar

A later MediLacra enhancement could optionally emit a tiny NDJSON truth sidecar:

```text
encounter_id
patient_id
visit_number
placer_order
filler_order
observation_ids[]
transaction_ids[]
admit
discharge
expected_message_types[]
```

This is **not** a new reality model and is not required for SaSI V1. It would simply allow SaSI to test deeper cross-message and generator-to-output invariants.

---

## 12. Gender Harmony as a SaSI Test Case

Gender Harmony is valuable because it contains legitimate non-normalized and uncommon relationships.

SaSI must **not** impose false rules such as “gender identity must equal PID administrative sex.” Discordance may be valid and intentional.

Instead SaSI can test:

- code preservation,
- display preservation,
- system preservation,
- distinction between Gender Identity, Personal Pronouns, and SPCU,
- rare-category retention,
- preservation of the generated population distribution.

This makes Gender Harmony a useful test of whether a transformation preserves semantic variation rather than normalizing it away.

---

## 13. PIQITT Baseline Findings That Motivate SaSI

Current inspection of the clean PIQITT repository shows why a separate integrity analyzer is useful.

### ORM Support

The current converter has explicit paths for ORU, ADT, and DFT. Unsupported message types use a generic fallback that can preserve only a small resource subset.

A downstream PIQI score can therefore look excellent even when much of the source message was never represented.

SaSI should make transformation support and semantic retention explicit rather than letting downstream quality scoring stand in for them.

### Scoring Semantics

The current PIQI evaluator and profiles should remain separate from SaSI. SaSI is not a patch for PIQI scoring logic. Where PIQI configuration or evaluator behavior needs correction, that should be handled independently so the distinction between **quality** and **preservation** stays clean.

---

## 14. SaSI V1 Implementation Shape

SaSI should be added to a clean fork/development line of the non-contest `piqitt` repository.

Suggested structure:

```text
scripts/
    sasi_analyzer.py
    sasi_sams.py

profiles/
    profile_sasi_minimal.yaml
```

Potential later addition:

```text
scripts/
    sasi_summary.py
```

### Existing PIQITT Components to Leave Alone Initially

```text
scripts/fhir_convert_backend.py
scripts/piqi_eval.py
piqi_sam_library.yaml
profiles/profile_clinical_minimal.yaml
profiles/profile_claims_minimal.yaml
```

Only a minimal orchestration hook should be required to pass raw HL7 and the resulting Bundle into SaSI.

---

## 15. SaSI Minimal Profile

The first profile should stay small enough to understand completely.

Suggested initial assessments:

```text
SaSI_MessageTypeSupported
SaSI_PatientPreserved
SaSI_EncounterPreserved
SaSI_OBXCardinalityPreserved
SaSI_FT1CardinalityPreserved
SaSI_CodePreserved
SaSI_ValuePreserved
SaSI_UnitPreserved
SaSI_EffectiveTimePreserved
SaSI_ReferenceResolves
```

Ten assessments are enough to learn whether the architecture works.

Statistical checks can then aggregate the message-level output rather than making V1 structurally complicated.

---

## 16. Conceptual Stack

```text
MediLacra
synthetic healthcare reality / controlled source corpus
        ↓
HL7
source representation
        ↓
PIQITT (“pick it”)
representation transformation
        ↓
┌───────────────────────────────┐
│ SaSI (“sassy”)                │
│ Structural + Statistical      │
│ Integrity                     │
│                               │
│ What survived?                │
└───────────────────────────────┘
        ↓
FHIR
transformed representation
        ↓
┌───────────────────────────────┐
│ PIQI (“picky”)                │
│                               │
│ How good is what survived?    │
└───────────────────────────────┘
```

The clean ontology is:

- **MediLacra** generates controlled synthetic healthcare data.
- **HL7** represents it.
- **PIQITT** transforms the representation.
- **SaSI** measures structural and statistical integrity across the transformation.
- **PIQI** measures quality of the resulting representation according to configured assessments.

We stop asking one metric to describe several different processes.

---

## 17. Core SaSI Question

The entire project compresses to one question:

> **Fine, the transformed data looks good. But is it still the same data?**
