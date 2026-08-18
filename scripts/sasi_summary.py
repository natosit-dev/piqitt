from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List


def read_ndjson(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _merge_counter(target: Counter, values: Dict[str, Any]) -> None:
    for key, value in (values or {}).items():
        try:
            target[key] += int(value)
        except (TypeError, ValueError):
            continue


def _patient_sex_to_fhir(value: Any) -> str | None:
    if value is None:
        return None
    return {
        "M": "male",
        "F": "female",
        "O": "other",
        "U": "unknown",
    }.get(str(value).strip().upper(), str(value).strip().lower() or None)


def _distribution_comparison(source: Counter, target: Counter) -> Dict[str, Any]:
    src_total = sum(source.values())
    tgt_total = sum(target.values())
    categories = sorted(set(source) | set(target))
    rows = []
    max_abs_delta = 0.0
    for category in categories:
        src_count = source.get(category, 0)
        tgt_count = target.get(category, 0)
        src_pct = (100.0 * src_count / src_total) if src_total else 0.0
        tgt_pct = (100.0 * tgt_count / tgt_total) if tgt_total else 0.0
        delta = tgt_pct - src_pct
        max_abs_delta = max(max_abs_delta, abs(delta))
        rows.append({
            "category": category,
            "sourceCount": src_count,
            "targetCount": tgt_count,
            "sourcePct": round(src_pct, 4),
            "targetPct": round(tgt_pct, 4),
            "deltaPercentagePoints": round(delta, 4),
        })
    retention = (100.0 * tgt_total / src_total) if src_total else (100.0 if tgt_total == 0 else None)
    return {
        "sourceTotal": src_total,
        "targetTotal": tgt_total,
        "countDelta": tgt_total - src_total,
        "retentionRatePct": round(retention, 4) if retention is not None else None,
        "maxAbsoluteDeltaPercentagePoints": round(max_abs_delta, 4),
        "categories": rows,
    }


def summarize(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows = list(rows)
    by_sam: Dict[str, Counter] = defaultdict(Counter)
    by_message_type: Dict[str, Counter] = defaultdict(Counter)
    by_dimension: Dict[str, Counter] = defaultdict(Counter)
    source_obs_codes: Counter = Counter()
    target_obs_codes: Counter = Counter()
    source_coded_values: Counter = Counter()
    target_coded_values: Counter = Counter()
    source_message_types: Counter = Counter()
    target_resource_counts: Counter = Counter()
    source_patient_gender: Counter = Counter()
    target_patient_gender: Counter = Counter()

    for row in rows:
        mtype = row.get("messageType") or "UNKNOWN"
        by_message_type[mtype].update({
            "messages": 1,
            "PASS": row.get("passes", 0),
            "FAIL": row.get("fails", 0),
            "SKIP": row.get("skips", 0),
        })
        for detail in row.get("details") or []:
            status = detail.get("status") or "UNKNOWN"
            sam = detail.get("sam") or "UNKNOWN"
            dimension = detail.get("dimension") or "UNKNOWN"
            by_sam[sam][status] += 1
            by_dimension[dimension][status] += 1

        stats = row.get("statistics") or {}
        src = stats.get("source") or {}
        tgt = stats.get("target") or {}
        if src.get("messageType"):
            source_message_types[src["messageType"]] += 1
        src_gender = _patient_sex_to_fhir(src.get("patientSex"))
        if src_gender:
            source_patient_gender[src_gender] += 1
        if tgt.get("patientGender"):
            target_patient_gender[str(tgt["patientGender"]).lower()] += 1
        _merge_counter(source_obs_codes, src.get("observationCodes") or {})
        _merge_counter(target_obs_codes, tgt.get("observationCodes") or {})
        _merge_counter(source_coded_values, src.get("codedObservationValues") or {})
        _merge_counter(target_coded_values, tgt.get("codedObservationValues") or {})
        _merge_counter(target_resource_counts, tgt.get("resourceCounts") or {})

    def counter_table(mapping: Dict[str, Counter]) -> Dict[str, Dict[str, int]]:
        return {key: dict(value) for key, value in sorted(mapping.items())}

    return {
        "messages": len(rows),
        "byMessageType": counter_table(by_message_type),
        "bySAM": counter_table(by_sam),
        "byDimension": counter_table(by_dimension),
        "distributions": {
            "sourceMessageType": dict(source_message_types),
            "sourcePatientGenderCanonical": dict(source_patient_gender),
            "targetPatientGender": dict(target_patient_gender),
            "sourceObservationCodes": dict(source_obs_codes),
            "targetObservationCodes": dict(target_obs_codes),
            "sourceCodedObservationValues": dict(source_coded_values),
            "targetCodedObservationValues": dict(target_coded_values),
            "targetResourceCounts": dict(target_resource_counts),
        },
        "distributionComparisons": {
            "patientGender": _distribution_comparison(source_patient_gender, target_patient_gender),
            "observationCodes": _distribution_comparison(source_obs_codes, target_obs_codes),
            "codedObservationValues": _distribution_comparison(source_coded_values, target_coded_values),
        },
    }


def markdown(summary: Dict[str, Any]) -> str:
    lines: List[str] = ["# SaSI Summary", "", f"Total messages: **{summary.get('messages', 0)}**", ""]

    lines.extend(["## By Message Type", "", "| Message Type | Messages | PASS | FAIL | SKIP |", "|---|---:|---:|---:|---:|"])
    for key, counts in (summary.get("byMessageType") or {}).items():
        lines.append(f"| {key} | {counts.get('messages', 0)} | {counts.get('PASS', 0)} | {counts.get('FAIL', 0)} | {counts.get('SKIP', 0)} |")

    lines.extend(["", "## By SAM", "", "| SAM | PASS | FAIL | SKIP |", "|---|---:|---:|---:|"])
    for key, counts in (summary.get("bySAM") or {}).items():
        lines.append(f"| {key} | {counts.get('PASS', 0)} | {counts.get('FAIL', 0)} | {counts.get('SKIP', 0)} |")

    lines.extend(["", "## By Dimension", "", "| Dimension | PASS | FAIL | SKIP |", "|---|---:|---:|---:|"])
    for key, counts in (summary.get("byDimension") or {}).items():
        lines.append(f"| {key} | {counts.get('PASS', 0)} | {counts.get('FAIL', 0)} | {counts.get('SKIP', 0)} |")

    lines.extend(["", "## Statistical Integrity", ""])
    for name, comparison in (summary.get("distributionComparisons") or {}).items():
        lines.append(f"### {name}")
        lines.append("")
        retention = comparison.get("retentionRatePct")
        retention_text = "n/a" if retention is None else f"{retention:.4f}%"
        lines.append(
            f"Source count: **{comparison.get('sourceTotal', 0)}** · "
            f"Target count: **{comparison.get('targetTotal', 0)}** · "
            f"Retention: **{retention_text}** · "
            f"Max absolute distribution delta: **{comparison.get('maxAbsoluteDeltaPercentagePoints', 0):.4f} percentage points**"
        )
        lines.append("")
        lines.append("| Category | Source Count | Target Count | Source % | Target % | Delta pp |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for row in comparison.get("categories") or []:
            lines.append(
                f"| {row['category']} | {row['sourceCount']} | {row['targetCount']} | "
                f"{row['sourcePct']:.4f} | {row['targetPct']:.4f} | {row['deltaPercentagePoints']:.4f} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description="Summarize SaSI NDJSON results.")
    ap.add_argument("input", help="sasi_results.ndjson")
    ap.add_argument("--json-out", default="sasi_summary.json")
    ap.add_argument("--md-out", default="sasi_summary.md")
    args = ap.parse_args()

    result = summarize(read_ndjson(Path(args.input)))
    Path(args.json_out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    Path(args.md_out).write_text(markdown(result), encoding="utf-8")
    print(json.dumps({"messages": result["messages"], "json": args.json_out, "markdown": args.md_out}))


if __name__ == "__main__":
    main()
