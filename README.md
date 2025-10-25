# piqitt
PIQI Transformation Tool (PIQITT): HL7 v2 -> FHIR -> PIQI Scorecard Testing

This is a Python based tool for converting HL7 v2 messages to FHIR bundles. Those bundles are then evaluated using the PIQI (Patient Information Quality Improvement) framework.

**Goals**

1. Standardize data quality checks across sources.  
2. Apply reusable **Simple Assessment Modules (SAMs)** to FHIR resources.  
3. Produce portable **PIQI scorecards** (per message, later per facility/patient).

**Architecture**

fhir_app.py → Streamlit UI
scripts/fhir_convert_backend.py → HL7 → FHIR conversion
scripts/piqi_eval.py → Evaluator + SAMs + scoring
profiles/*.yaml → Evaluation profiles (Clinical/Claims)
ref/plausibility.yaml → Physiologic plausibility ranges (by LOINC)
ref/loinc.csv, ref/cpt.csv → Value sets
piqi_sam_library.yaml → SAM taxonomy + prerequisites

## 1) HL7 → FHIR Conversion (`scripts/fhir_convert_backend.py`)

Converts ADT / ORU / DFT messages into simplified FHIR Bundles.

### Key functions

- `split_messages(text)` – split multi-message HL7 payloads by `MSH|`.  
- `parse_hl7(text)` – normalize and collect segments/fields.  
- `build_patient_from_pid(pid)` – create `Patient`.  
- `build_encounter_from_pv1(pv1, patient_ref)` – create `Encounter`.  
- `build_observation_from_obx(obx, patient_ref, encounter_ref)` – create `Observation` with correct `value[x]` and OBX-6 units.  
- `build_diagnostic_report_from_obr(obr, ..., observation_refs)` – create `DiagnosticReport`.  
- `build_account_from_ft1(ft1, ...)` – map DFT/FT1 to a minimal `Claim`.  
- `convert_message_to_bundle(hl7_msg)` – detect type (`ORU^R01`, `ADT^A01`, `DFT^P03`) and assemble a `Bundle`.

**Notes**

- ADT OBX segments are also mapped to `Observation` (vitals).  
- Units from OBX-6 feed directly into plausibility checks.

## 2) PIQI Evaluation Engine (`scripts/piqi_eval.py`)

### Classes

**`PIQIEvaluator`** – orchestrates configuration and scoring.

Loads:
- **SAM library** (`piqi_sam_library.yaml`)
- **Profiles** (`profiles/*.yaml`)
- **Value sets** (LOINC/CPT)
- **Plausibility config** (`ref/plausibility.yaml`)

Exposes:
- `evaluate_bundle(bundle, profile_name)` → returns a message-level scorecard with per-step details.

**`SAM`** – namespace of validation functions (all `@staticmethod`s`) returning `"PASS"`, `"FAIL"`, `"SKIP"`.

### Core Methods

| Method | Purpose |
|--------|----------|
| `evaluate_bundle()` | Execute a profile over a Bundle; compute PIQI indices. |
| `_deep_get()` | Lightweight JSONPath extractor (`foo.bar*` array fan-out). |
| `_extract_value()` | Observation-aware `value[x]` extraction; else fallback to `_deep_get`. |
| `_value_preview()` | Human-readable preview (e.g., `81.36 mg/dL`). |
| `_load_sam_library()` | Parse SAM YAML into internal lookup. |
| `_load_profiles()` | Load profiles and build ordered steps. |

### Scoring Logic

1. Select target resources (e.g., `Observation`s).  
2. (Optional) run a **condition** SAM.  
3. Extract **value(s)**.  
4. Run **prerequisite** SAM (if any).  
   - `FAIL` → counts in denominator, skip main SAM.  
   - `SKIP` → excluded from denominator.  
5. Run the **main SAM**.  
6. Aggregate:  
   - `numerator` = PASS count  
   - `denominator` = PASS + FAIL  
   - `piqiIndex` = `100 * numerator / denominator`  
   - Track `criticalFailureCount`.

Each step logs `stepId`, `sam`, `status`, `dimension`, `valuePreview`, and optionally `loincCode` and `loincDisplay`.


## 3) Streamlit Front-End (`fhir_app.py`)

### Workflow

1. Upload `.hl7/.txt` files.  
2. Split into messages and convert to FHIR Bundles.  
3. Display parsed summary.  
4. (Optional) Run **PIQI evaluation**.  

Evaluations:
- Choose profile (`Claims-Minimal` or `Clinical-Minimal`)
- Display PIQI Scorecard  
- Export JSON or NDJSON

### Sidebar Parameters

- SAM library path  
- Clinical / Claims profiles  
- LOINC / CPT / Plausibility references  
- Evaluation toggles and export options  

---

## Configuration Files

### SAM Library (`piqi_sam_library.yaml`)

```yaml
sams:
  - mnemonic: Attr_IsPopulated
    dimension: Availability.Unpopulated
    entity_type: SimpleAttribute
  - mnemonic: Observation_UnitAllowed
    dimension: Accuracy.UnitMismatch
    entity_type: Observation
  - mnemonic: Observation_ValueWithinRange
    dimension: Accuracy.Plausibility
    entity_type: Observation
    prerequisite: Observation_UnitAllowed


**How To Run**