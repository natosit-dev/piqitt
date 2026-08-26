# SaSI Findings — Initial 1,000-Message Run

**Project:** SaSI — Structural and Statistical Integrity  
**Branch:** `sasi`  
**Date:** 2026-08-19  
**Source corpus:** MediLacra-generated HL7  
**Messages analyzed:** 1,000

---

# Run Shape

The first full SaSI run analyzed:

| Message Type | Messages |
|---|---:|
| ADT^A01 | 200 |
| DFT^P03 | 200 |
| ORM^O01 | 200 |
| ORU^R01 | 400 |
| **Total** | **1,000** |

The run exercised both structural and statistical integrity checks against the existing PIQITT HL7 → FHIR transformation behavior.

Important boundary:

> These findings describe what SaSI observed. They do not automatically identify root cause, and they do not yet change or repair PIQITT behavior.

---

# Finding 1 — ORM Is Not Structurally Supported

## Observed result

Across 200 ORM^O01 messages:

- `XFORM_MessageTypeSupported`: **200 FAIL**
- `XFORM_EncounterPreserved`: **200 FAIL**
- ORM total: **200 PASS / 400 FAIL / 1,400 SKIP**

## What this definitely means

PIQITT does not currently have an explicit ORM conversion path in the same way it does for ADT, ORU, and DFT.

SaSI is successfully distinguishing:

```text
message transformed through a supported path
```

from:

```text
message accepted through fallback behavior
```

This is important because downstream FHIR can still look syntactically clean even when most source semantics were never represented.

## What this may mean

ORM is currently a useful negative control for SaSI.

It demonstrates the class of problem SaSI was designed to expose:

> **High apparent downstream quality can coexist with low transformation fidelity.**

Do not repair ORM yet. Preserve it as a known test specimen until SaSI coverage is more mature.

---

# Finding 2 — Patient Representation Was Fully Retained

## Observed result

`XFORM_PatientPreserved`:

- **1,000 PASS**
- **0 FAIL**
- **0 SKIP**

Statistical comparison of source administrative sex to target FHIR Patient gender:

- Source patients: **1,000**
- Target patients: **1,000**
- Retention: **100%**
- Female: 550 → 550
- Male: 450 → 450
- Maximum distribution delta: **0.0 percentage points**

## What this definitely means

For this corpus, the tested patient representation survived the transformation with complete count retention and identical aggregate distribution for the field SaSI currently compares.

## What this does not mean

It does not prove that every Patient field is preserved.

Current SaSI patient testing is intentionally minimal. Future Patient invariants could cover identifiers, birth date, address, names, assigning authorities, and other demographics independently.

---

# Finding 3 — Observation Cardinality and Observation Codes Were Fully Retained

## Observed result

Observation code population:

- Source observations: **9,038**
- Target observations: **9,038**
- Retention: **100%**
- Maximum code-distribution delta: **0.0 percentage points**

`XFORM_OBXCardinalityPreserved`:

- **600 PASS**
- **0 FAIL**
- **400 SKIP**

`XFORM_CodePreserved`:

- **600 PASS**
- **0 FAIL**
- **400 SKIP**

## What this definitely means

For message types where OBX comparison applies, PIQITT preserved both:

1. the number of observations, and
2. the source observation codes as semantically equivalent target codes.

This includes the tested LOINC, CPT, and HL7-coded observation identifiers.

## Why this matters

This sharply narrows later failures.

If a coded observation value is lost while the Observation itself and its code survive, then the problem is not broad row loss.

Nat version:

> **The container survived. The label survived. Something inside the container changed.**

---

# Finding 4 — Coded Observation Values Show 0% Retention

## Observed result

SaSI found:

- Source coded observation values: **600**
- Target coded observation values: **0**
- Count delta: **-600**
- Retention: **0%**

The affected source values include Gender Harmony-related observations such as:

- LOINC `76691-5` values encoded with SNOMED CT
- LOINC `90778-2` values encoded with LOINC answer codes
- `SPCU` values encoded with HL7 values

At the same time:

- the Observation resources themselves were retained,
- their Observation codes were retained,
- aggregate Observation code distribution remained identical.

`XFORM_ValuePreserved` produced:

- **400 PASS**
- **200 FAIL**
- **400 SKIP**

## What this definitely means

The source corpus contains 600 coded OBX values that SaSI does not find represented as FHIR `Observation.valueCodeableConcept` values after transformation.

This is a genuine semantic-retention signal, but the exact mechanism still needs direct inspection.

## What this may mean

Possible explanations include:

1. the relevant OBX values use HL7 value types that PIQITT currently maps to `valueString` rather than `valueCodeableConcept`,
2. coded source values are being flattened into text,
3. some other representation change is occurring that SaSI's current target inventory does not yet recognize.

The current evidence does **not** support claiming that the entire Observation was dropped. In fact, the Observation count proves the opposite.

The next diagnostic step should inspect a small sample of these source OBXs and their corresponding FHIR Observations to identify the actual target representation.

## Why this matters

This is the clearest first demonstration of SaSI's purpose:

```text
Observation count:          100% retained
Observation code:           100% retained
Coded observation value:      0% retained as coded value
```

Fancy version:

> **Structural cardinality was invariant while value-level semantic structure was not.**

Nat version:

> **The rows made it through, but some of the meaning got squished.**

---

# Finding 5 — DFT Structural Cardinality Passed Cleanly

## Observed result

For 200 DFT^P03 messages:

- **1,000 PASS**
- **0 FAIL**
- **1,000 SKIP**

`XFORM_FT1CardinalityPreserved`:

- **200 PASS**
- **0 FAIL**

## What this definitely means

The tested FT1 → Claim cardinality relationship was preserved for every DFT message in this corpus.

## What this does not mean

It does not prove all transaction semantics are preserved.

The current SaSI profile tests FT1 cardinality but does not yet independently compare transaction code, description, amount, date, payer semantics, or claim-item relationships.

---

# Finding 6 — Reference Integrity Passed Wherever Applicable

## Observed result

`XFORM_ReferencesResolve`:

- **800 PASS**
- **0 FAIL**
- **200 SKIP**

## What this definitely means

For the generated FHIR Bundles where reference testing applied, all references SaSI inspected resolved to resources present in the same Bundle.

## What this does not mean

This proves FHIR-local referential integrity, not yet full source-to-target relationship preservation.

Fancy distinction:

- **Reference validity:** the pointer resolves.
- **Relationship fidelity:** it points to the entity the source semantics intended.

SaSI V1 currently proves the first more strongly than the second.

---

# Finding 7 — Statistical Integrity Needs Both Distribution and Retention

## Observed result

The first implementation work surfaced an important measurement rule:

> Percentage distributions can remain identical even when records disappear uniformly.

SaSI therefore reports both:

- source and target counts / retention rate, and
- percentage distribution drift.

Example concepts from this run:

```text
patient gender
1000 → 1000
100% retention
0 pp distribution drift
```

and:

```text
coded observation values
600 → 0
0% retention
large distribution loss
```

## Meaning

Statistical integrity cannot be summarized by distribution percentages alone.

Fancy version:

> **Distributional invariance without cardinality retention is insufficient evidence of statistical integrity.**

Nat version:

> **If half the data vanishes evenly, the pie chart can still look perfect.**

This should remain a permanent SaSI design rule.

---

# Current Structural Summary

| Dimension | PASS | FAIL | SKIP |
|---|---:|---:|---:|
| Structural.Cardinality | 800 | 0 | 1,200 |
| Structural.ReferentialIntegrity | 800 | 0 | 200 |
| Structural.SemanticRetention | 1,800 | 200 | 0 |
| Structural.Support | 800 | 200 | 0 |
| Structural.Temporal | 400 | 0 | 600 |
| Structural.Terminology | 600 | 0 | 400 |
| Structural.Unit | 400 | 0 | 600 |
| Structural.Value | 400 | 200 | 400 |

The dominant observed failure classes in this corpus are therefore:

1. unsupported ORM transformation behavior,
2. encounter loss associated with that unsupported path,
3. coded observation value representation loss/change.

---

# What We Should Investigate Next

## 1. Inspect coded-value source/target pairs

Take a small sample of the 600 coded source OBXs and capture:

```text
OBX-2 value type
OBX-3 observation code
OBX-5 source value
OBX-6 unit if present
resulting FHIR Observation.value[x]
```

Goal:

> Determine whether coded values are lost, flattened to strings, or represented somewhere SaSI V1 does not yet inspect.

---

## 2. Keep ORM unchanged for now

ORM is currently valuable as an intentionally observable unsupported case.

Do not fix it until SaSI has enough tests to prove the before/after behavior.

---

## 3. Expand value representation coverage only after inspection

Do not immediately make SaSI accept more target shapes just to increase PASS rates.

First determine whether the target representation is semantically correct.

Then decide whether:

- PIQITT needs fixing,
- SaSI inventory needs expanding,
- or both.

---

## 4. Expand DFT semantic checks later

Cardinality is clean, so the next useful DFT checks would be:

- transaction amount preservation,
- transaction code preservation,
- date preservation,
- Claim item structure,
- Encounter/Patient linkage.

---

# Initial Conclusion

The first real SaSI run validates the basic architecture.

It successfully distinguishes several different outcomes that a single downstream quality score could blur together:

```text
Patient representation:      retained
Observation cardinality:     retained
Observation terminology:     retained
FHIR references:             valid
DFT cardinality:             retained
ORM support:                 not retained / unsupported
Coded observation semantics: not retained as coded target values
```

The most important result is not a SaSI score.

It is that SaSI can now say **which layer of meaning survived and which layer did not**.

That is the measurement capability the project was built to create.
