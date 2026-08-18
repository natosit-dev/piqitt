from __future__ import annotations

import json
import os
import traceback
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter
from typing import Any, Callable, Dict, Iterator, List, Optional
from uuid import uuid4

from scripts.fhir_convert_backend import convert_message_to_bundle
from scripts.piqi_eval import (
    PIQIEvaluator,
    load_cpt_codes_from_csv,
    load_loinc_codes_from_csv,
    load_plausibility_yaml,
)
from scripts.run_repo import RunRepository

SUPPORTED_SUFFIXES = {".hl7", ".txt"}
ProgressCallback = Callable[[Dict[str, Any]], None]


@dataclass(frozen=True)
class EvaluationConfig:
    sam_library_path: str = "piqi_sam_library.yaml"
    clinical_profile_path: str = "profiles/profile_clinical_minimal.yaml"
    claims_profile_path: str = "profiles/profile_claims_minimal.yaml"
    loinc_csv: str = "ref/loinc.csv"
    cpt_csv: str = "ref/cpt.csv"
    plausibility_yaml: str = "ref/plausibility.yaml"
    profile_name: str = "AUTO"

    def snapshot(self) -> Dict[str, Any]:
        return asdict(self)


def discover_input_files(input_path: str | Path) -> List[Path]:
    """Resolve one supported file or supported files directly inside a folder."""
    path = Path(input_path).expanduser()
    if not path.exists():
        raise FileNotFoundError(f"Input path does not exist: {path}")

    if path.is_file():
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            raise ValueError(f"Unsupported input file type: {path.suffix or '<none>'}")
        return [path]

    if not path.is_dir():
        raise ValueError(f"Input path is not a file or directory: {path}")

    files = sorted(
        p for p in path.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES
    )
    if not files:
        raise ValueError(f"No .hl7 or .txt files found in: {path}")
    return files


def iter_hl7_messages(file_path: str | Path) -> Iterator[str]:
    """
    Stream HL7 messages without loading the whole file into memory.

    Python universal-newline handling treats CR, LF, and CRLF as line boundaries.
    A message is emitted when the next MSH| segment begins.
    """
    path = Path(file_path)
    buffer: List[str] = []
    seen_msh = False

    with path.open("r", encoding="utf-8", errors="ignore", newline=None) as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\r\n")
            if not line:
                continue
            if not seen_msh:
                line = line.lstrip("\ufeff")

            if line.startswith("MSH|"):
                if seen_msh and buffer:
                    yield "\n".join(buffer)
                    buffer = []
                seen_msh = True

            if seen_msh:
                buffer.append(line)

    if seen_msh and buffer:
        yield "\n".join(buffer)


def _choose_profile(bundle: Dict[str, Any], requested: str) -> str:
    if requested and requested.upper() != "AUTO":
        return requested
    resource_types = {
        entry.get("resource", {}).get("resourceType")
        for entry in bundle.get("entry", [])
    }
    return "Claims-Minimal" if "Claim" in resource_types else "Clinical-Minimal"


def build_evaluator(config: EvaluationConfig) -> PIQIEvaluator:
    loinc_codes = load_loinc_codes_from_csv(config.loinc_csv) if config.loinc_csv else set()
    cpt_codes = load_cpt_codes_from_csv(config.cpt_csv) if config.cpt_csv else set()
    plausibility_cfg = load_plausibility_yaml(config.plausibility_yaml)
    return PIQIEvaluator(
        sam_library_path=config.sam_library_path,
        profile_paths=[config.clinical_profile_path, config.claims_profile_path],
        loinc_codes=loinc_codes,
        cpt_codes=cpt_codes,
        plausibility_cfg=plausibility_cfg,
    )


def _new_run_id() -> str:
    return f"run-{uuid4()}"


def _emit(callback: Optional[ProgressCallback], **payload: Any) -> None:
    if callback is not None:
        callback(payload)


def _finding_rows(counter: Counter) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for (profile, step_id, sam, dimension, status), count in sorted(counter.items()):
        rows.append(
            {
                "profile": profile,
                "step_id": step_id,
                "sam": sam,
                "dimension": dimension,
                "status": status,
                "finding_count": count,
            }
        )
    return rows


def _write_run_summary(run_dir: Path, summary: Dict[str, Any]) -> tuple[Path, Path]:
    json_path = run_dir / "run_summary.json"
    md_path = run_dir / "run_summary.md"
    json_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    lines = [
        "# PIQITT WAP_AS Run Summary",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Status: **{summary['status']}**",
        f"- Input: `{summary['input_path']}`",
        f"- Files: **{summary['file_count']}**",
        f"- Messages processed: **{summary['message_count']}**",
        f"- Mean PIQI: **{summary['mean_piqi'] if summary['mean_piqi'] is not None else 'n/a'}**",
        f"- Critical failures: **{summary['critical_failure_count']}**",
        f"- Elapsed seconds: **{summary['elapsed_seconds']:.3f}**",
        "",
        "## Files",
        "",
        "| File | Status | Type | Messages | Mean PIQI | Critical Fails | Seconds |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for row in summary["files"]:
        mean = "" if row.get("mean_piqi") is None else f"{row['mean_piqi']:.2f}"
        seconds = "" if row.get("elapsed_seconds") is None else f"{row['elapsed_seconds']:.3f}"
        lines.append(
            f"| {row['file_name']} | {row['status']} | {row.get('detected_message_type') or ''} | "
            f"{row.get('message_count') or 0} | {mean} | {row.get('critical_failure_count') or 0} | "
            f"{seconds} |"
        )
        if row.get("error_message"):
            lines.append(f"\n**{row['file_name']} error:** `{row['error_message']}`\n")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def run_piqitt(
    input_path: str | Path,
    *,
    config: Optional[EvaluationConfig] = None,
    db_path: str | Path = "data/piqitt_runs.duckdb",
    output_root: str | Path = "runs",
    progress_callback: Optional[ProgressCallback] = None,
    progress_every: int = 1000,
    piqitt_version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluate a local file/folder as one durable PIQITT run.

    File failures are isolated: the failed file is logged and marked FAILED, and
    processing continues with the remaining files. If any file fails, the overall
    run is marked FAILED after all discovered files have been attempted.
    """
    config = config or EvaluationConfig()
    files = discover_input_files(input_path)
    input_path_obj = Path(input_path).expanduser()
    input_type = "FILE" if input_path_obj.is_file() else "FOLDER"
    run_id = _new_run_id()
    run_dir = Path(output_root).expanduser() / run_id
    file_output_dir = run_dir / "files"
    log_dir = run_dir / "logs"
    file_output_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "run.log"
    log_path.touch(exist_ok=True)

    run_started = perf_counter()
    run_message_count = 0
    run_piqi_sum = 0.0
    run_critical = 0
    file_summaries: List[Dict[str, Any]] = []
    failed_files = 0
    run_error: Optional[str] = None
    version = piqitt_version or os.getenv("PIQITT_VERSION") or "WAP_AS"

    with RunRepository(db_path) as repo:
        repo.create_run(
            run_id=run_id,
            input_type=input_type,
            input_path=str(input_path_obj),
            profile=config.profile_name,
            file_count=len(files),
            piqitt_version=version,
            config_snapshot=config.snapshot(),
        )

        file_ids: Dict[Path, str] = {}
        for path in files:
            file_id = str(uuid4())
            file_ids[path] = file_id
            repo.register_file(
                run_id=run_id,
                file_id=file_id,
                file_path=str(path),
                file_name=path.name,
                file_size_bytes=path.stat().st_size,
            )

        repo.add_artifact(run_id=run_id, artifact_type="RUN_LOG", artifact_path=log_path)

        try:
            evaluator = build_evaluator(config)
        except Exception as exc:
            run_error = f"Evaluator initialization failed: {type(exc).__name__}: {exc}"
            log_path.write_text(traceback.format_exc(), encoding="utf-8")
            elapsed = perf_counter() - run_started
            repo.finish_run(
                run_id=run_id,
                status="FAILED",
                message_count=0,
                mean_piqi=None,
                critical_failure_count=0,
                elapsed_seconds=elapsed,
                error_message=run_error,
            )
            summary = {
                "run_id": run_id,
                "status": "FAILED",
                "input_type": input_type,
                "input_path": str(input_path_obj),
                "file_count": len(files),
                "message_count": 0,
                "mean_piqi": None,
                "critical_failure_count": 0,
                "elapsed_seconds": elapsed,
                "error_message": run_error,
                "files": repo.files_for_run(run_id),
            }
            json_path, md_path = _write_run_summary(run_dir, summary)
            repo.add_artifact(run_id=run_id, artifact_type="SUMMARY_JSON", artifact_path=json_path)
            repo.add_artifact(run_id=run_id, artifact_type="SUMMARY_MD", artifact_path=md_path)
            _emit(progress_callback, event="run_failed", **summary)
            return summary

        _emit(
            progress_callback,
            event="run_started",
            run_id=run_id,
            file_count=len(files),
            input_path=str(input_path_obj),
        )

        for file_number, path in enumerate(files, start=1):
            file_id = file_ids[path]
            file_started = perf_counter()
            file_message_count = 0
            file_piqi_sum = 0.0
            file_critical = 0
            finding_counts: Counter = Counter()
            message_types: set[str] = set()
            artifact_path = file_output_dir / f"{path.stem}.{file_id[:8]}.piqi.ndjson"

            repo.start_file(run_id=run_id, file_id=file_id)
            _emit(
                progress_callback,
                event="file_started",
                run_id=run_id,
                file_id=file_id,
                file_number=file_number,
                file_count=len(files),
                file_name=path.name,
                file_size_bytes=path.stat().st_size,
            )

            try:
                with artifact_path.open("w", encoding="utf-8") as detail_out:
                    for message_index, message in enumerate(iter_hl7_messages(path), start=1):
                        bundle, message_type = convert_message_to_bundle(message)
                        message_types.add(message_type or "UNKNOWN")
                        profile = _choose_profile(bundle, config.profile_name)
                        result = evaluator.evaluate_bundle(bundle, profile_name=profile)

                        piqi_value = result.get("piqiIndex")
                        if piqi_value is not None:
                            piqi_value = float(piqi_value)
                            file_piqi_sum += piqi_value
                            run_piqi_sum += piqi_value

                        critical = int(result.get("criticalFailureCount") or 0)
                        file_critical += critical
                        run_critical += critical
                        file_message_count += 1
                        run_message_count += 1

                        for detail in result.get("details", []):
                            key = (
                                profile,
                                detail.get("stepId"),
                                detail.get("sam"),
                                detail.get("dimension"),
                                detail.get("status"),
                            )
                            finding_counts[key] += 1

                        record = {
                            "sourceFile": path.name,
                            "messageIndex": message_index,
                            "messageType": message_type,
                            "profile": profile,
                            **result,
                        }
                        detail_out.write(json.dumps(record, separators=(",", ":"), default=str))
                        detail_out.write("\n")

                        if progress_every > 0 and file_message_count % progress_every == 0:
                            file_mean = file_piqi_sum / file_message_count
                            run_mean = run_piqi_sum / run_message_count
                            repo.update_progress(
                                run_id=run_id,
                                file_id=file_id,
                                file_message_count=file_message_count,
                                file_mean_piqi=file_mean,
                                file_critical_failure_count=file_critical,
                                run_message_count=run_message_count,
                                run_mean_piqi=run_mean,
                                run_critical_failure_count=run_critical,
                            )
                            _emit(
                                progress_callback,
                                event="progress",
                                run_id=run_id,
                                file_id=file_id,
                                file_name=path.name,
                                file_number=file_number,
                                file_count=len(files),
                                file_message_count=file_message_count,
                                run_message_count=run_message_count,
                                file_mean_piqi=file_mean,
                                run_mean_piqi=run_mean,
                            )

                if file_message_count == 0:
                    raise ValueError("No HL7 messages beginning with MSH| were found")

                file_elapsed = perf_counter() - file_started
                file_mean = file_piqi_sum / file_message_count
                detected = ",".join(sorted(message_types))
                repo.finish_file(
                    run_id=run_id,
                    file_id=file_id,
                    status="COMPLETE",
                    detected_message_type=detected,
                    message_count=file_message_count,
                    mean_piqi=file_mean,
                    critical_failure_count=file_critical,
                    elapsed_seconds=file_elapsed,
                )
                repo.replace_findings(
                    run_id=run_id,
                    file_id=file_id,
                    rows=_finding_rows(finding_counts),
                )
                repo.add_artifact(
                    run_id=run_id,
                    file_id=file_id,
                    artifact_type="DETAIL_NDJSON",
                    artifact_path=artifact_path,
                )
                file_summary = {
                    "file_id": file_id,
                    "file_name": path.name,
                    "file_path": str(path),
                    "status": "COMPLETE",
                    "detected_message_type": detected,
                    "message_count": file_message_count,
                    "mean_piqi": file_mean,
                    "critical_failure_count": file_critical,
                    "elapsed_seconds": file_elapsed,
                    "error_message": None,
                    "artifact_path": str(artifact_path),
                }
                file_summaries.append(file_summary)
                _emit(progress_callback, event="file_complete", run_id=run_id, **file_summary)

            except Exception as exc:
                failed_files += 1
                file_elapsed = perf_counter() - file_started
                file_mean = (file_piqi_sum / file_message_count) if file_message_count else None
                detected = ",".join(sorted(message_types)) if message_types else None
                error = f"{type(exc).__name__}: {exc}"
                with log_path.open("a", encoding="utf-8") as log:
                    log.write(f"\n--- {path} ---\n")
                    log.write(traceback.format_exc())
                    log.write("\n")

                repo.finish_file(
                    run_id=run_id,
                    file_id=file_id,
                    status="FAILED",
                    detected_message_type=detected,
                    message_count=file_message_count,
                    mean_piqi=file_mean,
                    critical_failure_count=file_critical,
                    elapsed_seconds=file_elapsed,
                    error_message=error,
                )
                repo.replace_findings(
                    run_id=run_id,
                    file_id=file_id,
                    rows=_finding_rows(finding_counts),
                )
                if artifact_path.exists() and artifact_path.stat().st_size:
                    repo.add_artifact(
                        run_id=run_id,
                        file_id=file_id,
                        artifact_type="DETAIL_NDJSON_PARTIAL",
                        artifact_path=artifact_path,
                    )
                file_summary = {
                    "file_id": file_id,
                    "file_name": path.name,
                    "file_path": str(path),
                    "status": "FAILED",
                    "detected_message_type": detected,
                    "message_count": file_message_count,
                    "mean_piqi": file_mean,
                    "critical_failure_count": file_critical,
                    "elapsed_seconds": file_elapsed,
                    "error_message": error,
                    "artifact_path": str(artifact_path) if artifact_path.exists() else None,
                }
                file_summaries.append(file_summary)
                _emit(progress_callback, event="file_failed", run_id=run_id, **file_summary)
                # Deliberately continue to the next discovered file.

        elapsed = perf_counter() - run_started
        run_mean = (run_piqi_sum / run_message_count) if run_message_count else None
        status = "FAILED" if failed_files else "COMPLETE"
        if failed_files:
            run_error = f"{failed_files} file(s) failed; see run_files and run.log"

        repo.finish_run(
            run_id=run_id,
            status=status,
            message_count=run_message_count,
            mean_piqi=run_mean,
            critical_failure_count=run_critical,
            elapsed_seconds=elapsed,
            error_message=run_error,
        )

        summary = {
            "run_id": run_id,
            "status": status,
            "input_type": input_type,
            "input_path": str(input_path_obj),
            "file_count": len(files),
            "message_count": run_message_count,
            "mean_piqi": run_mean,
            "critical_failure_count": run_critical,
            "elapsed_seconds": elapsed,
            "error_message": run_error,
            "files": file_summaries,
        }
        json_path, md_path = _write_run_summary(run_dir, summary)
        repo.add_artifact(run_id=run_id, artifact_type="SUMMARY_JSON", artifact_path=json_path)
        repo.add_artifact(run_id=run_id, artifact_type="SUMMARY_MD", artifact_path=md_path)

    _emit(progress_callback, event="run_complete", **summary)
    return summary
