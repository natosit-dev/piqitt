# WAP_AS Local Validation — 2026-08-19

**Branch:** `WAP_AS`  
**Purpose:** Preserve the first real local execution evidence for the backend-path architecture before moving to the large MediLacra benchmark.

## Prompt / operator log

### Local checkout separation

> "Should I create a new wap_as folder in my users/spooky directory? Just want to make sure this gets it's own folder"

Decision: use a dedicated local checkout for WAP_AS so its DuckDB run history, generated artifacts, dependencies, and benchmark work remain separate from other PIQITT branches/checkouts.

### First backend-path run

The UI discovered all five regression HL7 files and created a run successfully, but the run ended `FAILED` with zero processed messages.

The run log identified the cause:

```text
FileNotFoundError: [Errno 2] No such file or directory: 'ref\\loinc.csv'
```

### Reference-file clarification

The local `loinc.csv` used for development was sourced informally from material found online. It is not large, curated, or claimed to represent the complete LOINC terminology.

This is an important interpretation constraint for PIQITT terminology-membership results.

### Second backend-path run

After the local LOINC reference file was placed at the configured path, the same regression folder completed successfully.

---

# 1. What the first failed run proved

The first failure happened before message processing, but several WAP_AS components still worked correctly:

- the backend folder path resolved
- all five supported files were discovered
- a durable run ID was created
- file-level records were created
- the failure was logged
- the run status was persisted
- the failed run appeared under **Recent Runs** in Streamlit

The problem was not HL7 parsing, PIQI scoring, DuckDB, or folder ingestion. It was a missing local evaluator dependency.

This exposed a useful deployment assumption:

> `ref/` is gitignored, so a clean clone does not contain the local terminology/configuration files used by another checkout.

---

# 2. Successful smoke test

Run ID:

```text
run-19b0cd86-1499-4dc9-ab42-da89f70167ae
```

Input:

```text
C:\Users\spooky\medilacra\output\test_regression
```

Run summary:

| Metric | Result |
|---|---:|
| Status | COMPLETE |
| Files | 5 |
| Messages | 1,000 |
| Mean PIQI | 77.14907 |
| Critical failures | 0 |
| Elapsed seconds | 4.658 |

Per-file results:

| File | Type | Messages | Mean PIQI | Critical fails | Seconds |
|---|---|---:|---:|---:|---:|
| `ADT_20260818_104011.hl7` | ADT^A01 | 200 | 88.24 | 0 | 0.362 |
| `DFT_20260818_104011.hl7` | DFT^P03 | 200 | 66.67 | 0 | 0.107 |
| `ORM_20260818_104011.hl7` | ORM^O01 | 200 | 100.00 | 0 | 0.044 |
| `ORU_20260818_104011.hl7` | ORU^R01 | 200 | 34.12 | 0 | 0.978 |
| `ORU_LABS_20260818_104011.hl7` | ORU^R01 | 200 | 96.72 | 0 | 0.441 |

---

# 3. Semantic equivalence

The backend-path results reproduce the known PIQI scores from the existing small-run workflow:

```text
ADT       88.24
DFT       66.67
ORM      100.00
ORU       34.12
ORU_LABS  96.72
```

This supports the central WAP_AS design requirement:

> **Changing ingestion/execution infrastructure did not change PIQI evaluation semantics for the regression dataset.**

That means the scale layer can now be tested independently from the scoring layer.

---

# 4. Reference-data caveat

The current local LOINC CSV is a development convenience, not a terminology authority.

Known limitations:

- small local coverage
- informally sourced online
- no claim of completeness
- no claim that the file represents an official current LOINC distribution
- provenance/version metadata has not yet been formalized in PIQITT

Therefore:

> A terminology-membership failure can reflect missing local reference coverage rather than a semantically invalid real-world code.

This is particularly important when interpreting `Concept_IsValidMember` results.

WAP_AS run provenance should eventually include explicit terminology/reference identifiers, versions, hashes, or other metadata sufficient to reproduce the exact evaluation context.

---

# 5. Follow-up cleanup identified

## Reference-file preflight

Before evaluator execution, validate configured files such as:

```text
ref/loinc.csv
ref/cpt.csv
ref/plausibility.yaml
```

A missing dependency should be reported as a run/configuration problem before creating the impression that each discovered HL7 file independently failed.

Suggested message:

```text
LOINC reference not found: ref\loinc.csv
```

This is a usability improvement, not a blocker for the scale benchmark.

## Quarantine queue

Still deferred.

Current behavior remains:

```text
file fails
  ↓
log failure
  ↓
mark file FAILED
  ↓
continue run
```

A future quarantine/retry design can build on the existing run/file provenance.

---

# 6. Next benchmark

The next test should use WAP_AS Backend path against the large MediLacra benchmark, especially the inputs that exceeded the Streamlit upload path:

- DFT approximately 200 MB
- ORU approximately 600 MB

The next benchmark is intended to answer a different question than the smoke test:

> **Once the browser upload ceiling is removed, where does the actual PIQITT backend begin to bend?**

Potential limits to observe:

- filesystem read throughput
- message-boundary streaming
- HL7 → FHIR conversion
- PIQI evaluation cost
- DuckDB checkpoint overhead
- NDJSON artifact growth
- memory use
- Streamlit progress/rendering behavior
- total runtime

The regression smoke test is complete. WAP_AS is ready for the scale test.
