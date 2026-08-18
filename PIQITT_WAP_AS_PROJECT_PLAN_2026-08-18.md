# PIQITT WAP_AS Project Plan
## Write-Audit-Public at Scale

**Branch:** `WAP_AS`  
**Repository:** `natosit-dev/piqitt`  
**Date:** 2026-08-18  
**Status:** Initial project plan  
**Purpose:** Extend the working PIQITT implementation so large HL7 workloads can be evaluated on the backend without being constrained by Streamlit upload limits, while preserving durable run history in a lightweight DuckDB repository.

---

# Prompt History

This plan grew directly out of the MediLacra → PIQITT stress test.

### 1. Initial stress-test intent

> "Ok, now I'm going to stress test PIQITT - drop the giant HL7 files I created with the connection branch into the UI and see what it does"

The first question was deliberately simple: **what happens when PIQITT receives much larger synthetic HL7 workloads than the UI was originally built around?**

### 2. Initial batch

MediLacra generated:

- 100 patients
- 200 encounters
- 1,000 observations
- 400 transactions
- 200 ADT messages
- 200 ORU messages
- 200 DFT messages
- 200 ORM lab messages
- 200 ORU lab messages

PIQITT successfully processed the first uploaded ADT and ORU workloads. The results exposed specific terminology/conformance behaviors rather than general parser failure.

### 3. Increased load

> "Increased the load size"

A later PIQITT run evaluated 10,000 messages:

| Message family | Count | Mean PIQI | Mean critical failures |
|---|---:|---:|---:|
| ADT | 2,000 | 88.24 | 0.00 |
| DFT | 2,000 | 66.67 | 0.00 |
| ORM | 2,000 | 100.00 | 0.00 |
| ORU | 2,000 | 34.11 | 0.00 |
| ORU_LABS | 2,000 | 96.72 | 0.00 |

The important result was not merely the absolute score. The message families showed stable, repeatable behavior at larger volume.

### 4. Million-scale MediLacra benchmark

> "I'm gonna go run an errand. Just dropped the 1m benchmark into piqitt :)"

The complete MediLacra benchmark produced files too large to submit through the current Streamlit UI.

The subset that fit through the upload interface contained:

- 117,648 ADT messages
- 117,648 ORM messages
- 117,648 ORU_LABS messages
- **352,944 total evaluated messages**

PIQI results remained identical to the smaller comparable run:

| Message family | 10k benchmark | Large benchmark |
|---|---:|---:|
| ADT | 88.24 | 88.24 |
| ORM | 100.00 | 100.00 |
| ORU_LABS | 96.72 | 96.72 |

Mean critical failures remained `0.00`.

### 5. The actual scale boundary

> "Yeah, I didn't drop all the messages in. ORU 600MB and just reports. DFT was 200MB. So I dropped them both as the streamlit max file size is 200MB"

This clarified the limiting component.

The large benchmark did **not** establish that PIQITT itself could not process the remaining workload.

It established that the **Streamlit upload interface became the gate before PIQITT could receive the workload**.

### 6. Architectural decision

> "I think we need to just have the option to point to an input folder, the work can happen on the backend. We should also have a small duckDB data repo for run info, I think?"

This became the basis of WAP_AS.

### 7. Branch decision

> "Let's take the current branch we have working and copy it to a new branch. Let's call it... WAP_AS (write-audit-public at scale)"

The `WAP_AS` branch exists to preserve the working PIQITT baseline while adding scale-oriented ingestion, execution, and audit infrastructure.

---

# 1. Why WAP_AS Exists

PIQITT already performs the important work:

```text
HL7 v2
  ↓
FHIR
  ↓
PIQI evaluation
  ↓
scorecard / detailed result
```

The scale test showed that this core path can evaluate hundreds of thousands of messages while preserving stable scoring behavior.

The immediate problem is therefore **not the scoring engine**.

The problem is the shape of the entry point.

Today, the practical path is approximately:

```text
User
  ↓
Browser
  ↓
Streamlit upload widget
  ↓
large file loaded through UI
  ↓
PIQITT backend
```

At small and medium scale this is convenient.

At hundreds of megabytes it becomes silly.

A 600 MB ORU file should not need to travel through a browser widget merely so a Python backend can read a file that is already sitting on the same machine.

WAP_AS changes the execution boundary:

```text
User
  ↓
Streamlit control surface
  ↓
run request
  ↓
backend runner
  ↓
local input folder
  ↓
message stream
  ↓
existing PIQITT conversion + evaluation
  ↓
results + DuckDB run metadata
```

The UI tells PIQITT **what to run**.

The backend does the work.

---

# 2. Nat-Style Explanation

Current PIQITT makes you carry the boxes through the front office.

That is fine when there are three boxes.

It is stupid when a truck shows up.

The fix is not to build a larger front door.

The fix is:

> Tell the warehouse where the truck is parked.

The input folder is the truck.

The backend runner unloads it.

PIQITT evaluates what is inside.

DuckDB keeps the shipping manifest:

- what showed up
- when we started
- which files were processed
- how many messages were inside
- what PIQITT found
- whether anything blew up
- how long it took
- where the detailed output lives

Streamlit remains useful, but it becomes the **dashboard/control panel**, not the conveyor belt.

---

# 3. Fancy Style Translation

| Nat-style language | Fancy systems language |
|---|---|
| Don't carry giant files through the UI | Decouple the control plane from the data plane |
| Point PIQITT at the folder | Filesystem-backed batch ingestion |
| Read one message at a time | Streaming / iterator-based processing |
| Don't load the whole stupid thing into RAM | Bounded-memory execution |
| Keep a little database of what happened | Persistent execution metadata repository |
| Remember each run | Run provenance / execution lineage |
| Keep the big detailed crap outside DuckDB | Separate metadata persistence from result artifacts |
| UI tells backend what to do | Thin orchestration layer |
| One backend path for UI and command line | Shared execution service / single execution primitive |
| Know exactly where a run died | File-level checkpoints and failure localization |
| Compare today's run to yesterday's | Longitudinal benchmark observability |
| We solve the problem once | Reusable execution infrastructure |

---

# 4. Project Purpose

WAP_AS should allow PIQITT to evaluate HL7 corpora that are larger than the practical Streamlit upload limit without changing the semantics of PIQI evaluation.

The project should add:

1. Folder-based backend input.
2. A shared backend runner independent of Streamlit.
3. Incremental file/message processing.
4. A small DuckDB operational repository.
5. Durable run identifiers.
6. File-level and run-level summaries.
7. Result artifact tracking.
8. Progress/status information that Streamlit can display.
9. A path to command-line execution using the same runner.
10. Benchmark history for repeated MediLacra and Connectathon testing.

The project should **not** become a distributed processing platform.

This is local-scale infrastructure for running PIQITT properly.

---

# 5. Existing PIQITT Components to Preserve

The current repository already has a useful separation of responsibilities.

## Streamlit UI

Current role:

- accept uploaded `.hl7` / `.txt` files
- select profile/configuration
- trigger conversion and PIQI evaluation
- display results
- export output

WAP_AS should preserve this workflow for small interactive work.

## HL7 → FHIR conversion

Existing backend:

`./scripts/fhir_convert_backend.py`

Current responsibilities include:

- split multi-message HL7 payloads
- parse HL7
- construct simplified FHIR resources
- build FHIR Bundles
- detect supported message families

WAP_AS should call this existing conversion logic rather than duplicate it.

## PIQI evaluation

Existing backend:

`./scripts/piqi_eval.py`

Current responsibilities include:

- load SAM definitions
- load evaluation profiles
- load reference/value-set data
- evaluate FHIR Bundles
- calculate PIQI scores
- record step-level details
- count critical failures

WAP_AS should preserve this evaluator as the semantic authority.

## Profiles and reference data

Existing configuration should continue to drive evaluation.

The scale layer should not quietly invent new scoring behavior.

---

# 6. Core Definitions

## Input Source

A location from which PIQITT obtains HL7 data.

Initial types:

- uploaded file
- local file
- local folder

Future sources may exist, but WAP_AS does not need them yet.

---

## Run

One explicit invocation of PIQITT evaluation over one input source using one resolved configuration.

A run answers:

> What did PIQITT evaluate, under what configuration, when, and what happened?

A run has one stable `run_id`.

---

## Run File

One physical input file discovered during a run.

A run file records:

- path
- size
- detected message type(s)
- processing status
- message count
- start/end timestamps
- summary PIQI metrics
- error information when applicable

---

## Message

One HL7 message extracted from an input file.

Messages should be processed incrementally.

A 600 MB file is therefore not conceptually one giant PIQITT object.

It is:

```text
file
  ↓
message
message
message
message
...
```

---

## Finding

The result of one PIQI/SAM evaluation outcome.

Detailed per-message findings may remain in external result artifacts.

DuckDB initially needs the useful aggregate shape, not every giant JSON object.

---

## Finding Aggregate

A count of repeated PIQI outcomes grouped by useful dimensions such as:

- run
- file
- profile
- step ID
- dimension
- status
- SAM

Example:

```text
run_123
ORU_BIG.hl7
OBS-2
Conformity.InvalidMember
FAIL
563821 occurrences
```

This preserves operational meaning without requiring DuckDB to duplicate the entire detailed result corpus.

---

## Result Artifact

A durable detailed output produced by a run.

Examples:

- JSON
- NDJSON
- Markdown summary
- future Parquet output

DuckDB records where the artifact is located.

The artifact remains the detailed evidence.

---

## Control Plane

The thing that asks for work to happen.

In WAP_AS:

- Streamlit
- eventually CLI

---

## Data Plane

The machinery that actually touches and processes the large data.

In WAP_AS:

- filesystem reader
- HL7 message iterator
- conversion backend
- PIQI evaluator
- result writer

---

# 7. Inputs

## A. Existing UI File Upload

Keep it.

Purpose:

- demos
- debugging
- Connectathon interaction
- small samples
- rapid inspection

This remains the easiest way to say:

> "What the hell is wrong with these 20 messages?"

---

## B. Backend File Path

Allow PIQITT to process a file that already exists on the machine.

Example:

```text
C:\medilacra\runs\benchmark_1m\ADT_20260817_200158.hl7
```

No browser upload is necessary.

---

## C. Backend Folder Path

Primary WAP_AS feature.

Example:

```text
C:\medilacra\runs\benchmark_1m\
```

PIQITT discovers supported files and processes them as one run.

Initial discovery rules should be intentionally boring:

- `.hl7`
- `.txt`

Optionally recursive later.

Do not build a magical filesystem crawler.

---

## D. Evaluation Configuration

A run must resolve and record its evaluation configuration.

At minimum:

- selected PIQI profile
- SAM library path/version
- relevant reference files
- PIQITT version / commit when available

The purpose is reproducibility.

A score without its evaluation context is weaker evidence.

---

# 8. Proposed Workflow

## User workflow

```text
Open PIQITT
  ↓
Choose input mode
  ├── Upload
  └── Backend path
          ↓
      choose file/folder
          ↓
Choose PIQI profile
          ↓
Start run
          ↓
PIQITT creates run_id
          ↓
Backend discovers files
          ↓
Backend processes messages incrementally
          ↓
Progress updates stored
          ↓
DuckDB receives run/file aggregates
          ↓
Detailed result artifacts written
          ↓
Run marked complete
          ↓
UI displays summary
```

---

# 9. Backend Workflow

The backend should have one execution path regardless of who calls it.

Conceptually:

```python
run_piqitt(
    input_source=...,
    profile=...,
    config=...
)
```

Streamlit calls it.

A CLI can call it.

Tests can call it.

Future automation can call it.

That keeps the UI from becoming architecture.

---

## Step 1 — Create run

Create a UUID or equivalent stable run identifier.

Insert the initial `runs` record with status:

```text
PENDING
```

then:

```text
RUNNING
```

---

## Step 2 — Resolve input

If source is a file:

```text
1 file
```

If source is a folder:

```text
discover supported files
```

Store discovered file records before processing begins.

This provides a known denominator for progress.

---

## Step 3 — Process files sequentially first

Do not introduce concurrency in MVP.

For each file:

1. mark file `RUNNING`
2. open file
3. iterate HL7 messages
4. convert each message to FHIR
5. evaluate Bundle
6. update streaming aggregates
7. write detailed output incrementally
8. finalize file summary
9. mark file `COMPLETE`

If processing fails:

1. preserve completed work
2. record error
3. mark file `FAILED`
4. decide run status from resulting policy

---

## Step 4 — Aggregate without retaining everything

Do not accumulate all scorecards in a Python list.

Maintain counters such as:

```text
message_count
piqi_sum
critical_failure_count
PASS count
FAIL count
SKIP count
finding counts by step/dimension/status
```

Then:

```text
mean PIQI = piqi_sum / message_count
```

Detailed records stream to output.

Operational summaries stream to DuckDB.

---

## Step 5 — Finalize run

Aggregate file results.

Record:

- total messages
- total files
- mean PIQI
- total critical failures
- elapsed time
- output artifact locations
- final status

---

# 10. DuckDB Run Repository

Suggested file:

```text
data/piqitt_runs.duckdb
```

The exact location should remain configurable.

The repository is **not the clinical data warehouse**.

It is PIQITT's memory of its own work.

---

## Table: `runs`

Suggested fields:

```text
run_id
started_at
completed_at
status
input_type
input_path
profile
file_count
message_count
mean_piqi
critical_failure_count
elapsed_seconds
piqitt_version
config_snapshot
error_message
```

---

## Table: `run_files`

Suggested fields:

```text
run_id
file_id
file_path
file_name
file_size_bytes
status
detected_message_type
message_count
mean_piqi
critical_failure_count
started_at
completed_at
elapsed_seconds
error_message
```

---

## Table: `run_findings`

Suggested fields:

```text
run_id
file_id
profile
step_id
sam
dimension
status
finding_count
```

This is aggregated evidence.

Do not initially store every single message-detail result here.

---

## Table: `run_artifacts`

Suggested fields:

```text
run_id
file_id
artifact_type
artifact_path
created_at
size_bytes
```

Example artifact types:

```text
DETAIL_JSON
DETAIL_NDJSON
SUMMARY_MD
SUMMARY_JSON
```

---

# 11. Suggested Status Model

For runs and files:

```text
PENDING
RUNNING
COMPLETE
FAILED
CANCELLED
```

Potential later state:

```text
COMPLETE_WITH_ERRORS
```

Do not add it until behavior actually requires it.

---

# 12. Output Layout

Suggested output structure:

```text
runs/
└── <run_id>/
    ├── run_summary.md
    ├── run_summary.json
    ├── files/
    │   ├── ADT_....piqi.ndjson
    │   ├── ORM_....piqi.ndjson
    │   └── ORU_....piqi.ndjson
    └── logs/
        └── run.log
```

NDJSON is attractive for large detailed results because records can be written incrementally instead of requiring a gigantic in-memory JSON array.

This should be treated as a design preference to test, not sacred doctrine.

---

# 13. UI Changes

Add an input-mode selector.

Conceptually:

```text
Input mode:
( ) Upload files
( ) Backend file/folder
```

For backend mode:

```text
Input path: [________________________]
```

Then:

```text
[ Start Run ]
```

The UI should display:

- run ID
- status
- discovered files
- current file
- processed message count
- elapsed time
- completed file summaries
- final run summary

The UI should **poll/read run state**, not own the giant workload.

---

# 14. CLI Shape

A minimal CLI should call the same backend runner.

Example:

```bash
python -m piqitt run \
  --input "C:\medilacra\runs\benchmark_1m" \
  --profile Clinical-Minimal
```

Or eventually:

```bash
piqitt run \
  --input ./benchmark_1m \
  --profile Clinical-Minimal
```

CLI polish is not required for the first implementation.

The important architectural rule is:

> Streamlit must not be the only way to execute a run.

---

# 15. Failure Behavior

Scale tooling is useful partly because things fail.

Failures must become data.

For a failed file, preserve:

- run ID
- file path
- file size
- number of successfully processed messages
- failure timestamp
- exception/error summary
- completed result artifact if any

Do not throw away 400,000 successful evaluations because message 400,001 was malformed.

This is one of the main reasons to separate run state from UI state.

---

# 16. MVP Implementation Phases

## Phase 1 — Extract shared runner

Goal:

Move execution orchestration out of Streamlit.

Deliverable:

```text
runner
  ↓
existing converter
  ↓
existing evaluator
```

Success condition:

The current small upload workflow can use the shared runner without changing PIQI results.

---

## Phase 2 — Backend file input

Goal:

Run a local HL7 file without uploading it through Streamlit.

Success condition:

The same file produces equivalent results through upload mode and backend-path mode.

---

## Phase 3 — Folder ingestion

Goal:

Point PIQITT at a directory and evaluate every supported file.

Success condition:

A MediLacra benchmark directory can be evaluated as one logical run.

---

## Phase 4 — Streaming result writing

Goal:

Avoid retaining complete detailed results in memory.

Success condition:

Detailed results are written incrementally while aggregate PIQI calculations remain correct.

---

## Phase 5 — DuckDB run repository

Goal:

Persist run, file, finding, and artifact metadata.

Success condition:

Closing/restarting Streamlit does not erase knowledge of completed runs.

---

## Phase 6 — Run-history UI

Goal:

Use DuckDB to inspect previous executions.

Initial UI:

```text
Recent Runs
Run ID | Date | Input | Files | Messages | PIQI | Status | Runtime
```

Success condition:

The 10k, 352k, and future larger benchmarks can be compared without opening exported Markdown files manually.

---

## Phase 7 — Full large benchmark

Goal:

Process the previously excluded large files, especially:

- ~200 MB DFT
- ~600 MB ORU

Success condition:

The backend receives and evaluates the files without Streamlit upload being involved.

This is the first direct test of whether the evaluator itself has a meaningful scale boundary.

---

# 17. Decision Log

## Decision 001 — Preserve working PIQITT

**Decision:** Create a separate `WAP_AS` branch.

**Reason:** Scale work should not destabilize the known-working interactive implementation.

---

## Decision 002 — Do not solve the upload problem with a bigger upload limit

**Decision:** Add backend file/folder input instead of treating the Streamlit limit as the architecture.

**Reason:** Large local files do not need to pass through the browser.

---

## Decision 003 — Streamlit becomes a control surface

**Decision:** Keep Streamlit for configuration, execution control, progress, and inspection.

**Reason:** The UI is useful. It simply should not be the bulk data transport.

---

## Decision 004 — Create one shared runner

**Decision:** UI, CLI, and future automation should call the same backend execution primitive.

**Reason:** We solve execution once.

---

## Decision 005 — Start sequentially

**Decision:** Process files/messages sequentially in MVP.

**Reason:** First establish correct bounded-memory behavior and provenance. Parallelism would make failure behavior, ordering, resource use, and debugging harder before we know it is necessary.

---

## Decision 006 — Add DuckDB as operational memory

**Decision:** Use a small DuckDB repository for runs, files, aggregate findings, and result artifact references.

**Reason:** PIQITT needs durable knowledge of its own executions.

---

## Decision 007 — Do not stuff all detailed results into DuckDB yet

**Decision:** Keep detailed result records in external artifacts and aggregate operational facts in DuckDB.

**Reason:** The 352,944-message test already demonstrates how quickly per-message detail can explode. The database should help inspect runs, not become another giant result blob.

---

## Decision 008 — Preserve existing evaluation semantics

**Decision:** WAP_AS changes ingestion and execution infrastructure, not PIQI scoring rules.

**Reason:** Scale testing is only interpretable if the evaluator remains semantically stable.

---

## Decision 009 — Large files are streams of messages

**Decision:** Treat file size and message count separately.

**Reason:** A 600 MB ORU file is physically large, but PIQITT's semantic work happens at the message/resource level. The implementation should reflect that grain.

---

## Decision 010 — Failure is an output

**Decision:** Persist partial progress and failure metadata.

**Reason:** At scale, "where did it fail?" is part of the benchmark.

---

# 18. Explicit Non-Goals

WAP_AS MVP is not:

- Spark
- Databricks
- Kafka
- a distributed queue
- a replacement for an interface engine
- a healthcare data lake
- a giant generalized workflow orchestrator
- a rewrite of PIQI
- a rewrite of FHIR conversion
- a reason to introduce concurrency before it is needed
- a reason to turn DuckDB into the source of all detailed evaluation data

If a laptop can do the work, let the laptop do the work.

---

# 19. Expected Results

## Functional

PIQITT should be able to:

- accept a backend file path
- accept a backend folder path
- discover supported HL7 files
- process files without browser upload
- process messages incrementally
- persist run state
- persist file state
- emit detailed result artifacts
- recover completed run history after UI restart

---

## Scale

The immediate target is to evaluate the previously excluded MediLacra files:

- DFT around 200 MB
- ORU around 600 MB

The expected result is **not automatically that they succeed**.

The expected result is that they finally reach the PIQITT backend, allowing us to observe the real limiting component.

Possible outcomes become distinguishable:

```text
filesystem ingest limit
parser limit
FHIR conversion limit
PIQI evaluation limit
memory limit
result-writing limit
UI rendering limit
```

That distinction is the point.

---

## Semantic stability

For equivalent source data and profile configuration, WAP_AS should preserve the PIQI results already observed.

Known reference values from the scale tests include:

```text
ADT       88.24
ORM      100.00
ORU_LABS  96.72
```

A change in ingestion architecture should not change those scores.

If it does, that is a regression or a discovery requiring investigation.

---

## Operational

A completed run should be reconstructable from metadata:

> On this date, PIQITT version X evaluated these files using this profile, processed N messages, produced these artifacts, generated these aggregate findings, took this long, and completed with this status.

That is enough provenance to make benchmark results durable.

---

# 20. First Concrete Build Target

The first useful vertical slice is intentionally small:

```text
Backend folder path
  ↓
discover .hl7 files
  ↓
create run_id
  ↓
process files sequentially
  ↓
process messages incrementally
  ↓
existing HL7 → FHIR converter
  ↓
existing PIQI evaluator
  ↓
write NDJSON details
  ↓
write DuckDB run + file summary
  ↓
display final result in Streamlit
```

No concurrency.

No new scoring logic.

No distributed anything.

No cleverness that does not help us feed the 600 MB ORU into PIQITT.

---

# 21. The Project in One Sentence

**WAP_AS turns PIQITT from a web UI that happens to run data-quality tests into a backend-capable evaluation tool with a web UI sitting on top of it.**

Or, in Nat:

> **Stop shoving the data through the window. Tell PIQITT where the pile is and let it go eat it.**
