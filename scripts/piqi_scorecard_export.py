#!/usr/bin/env python3
import argparse, json, os, glob, csv
from collections import defaultdict

def _iter_rows(results_dir: str):
    for path in glob.glob(os.path.join(results_dir, "*.json")):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            yield data
        elif isinstance(data, list):
            for r in data:
                yield r

def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return None

def main():
    ap = argparse.ArgumentParser(description="Export PIQI summary scorecards (CSV + Markdown).")
    ap.add_argument("--results", required=True, help="Directory with *.piqi.json")
    ap.add_argument("--csv", default="piqi_summary.csv", help="Output CSV")
    ap.add_argument("--md", default="piqi_summary.md", help="Output Markdown")
    args = ap.parse_args()

    agg = defaultdict(lambda: {"n":0, "sum":0.0, "crit_sum":0.0})
    total = 0

    for row in _iter_rows(args.results):
        total += 1
        prof = row.get("profile") or "Unknown"
        idx = _safe_float(row.get("piqiIndex"))
        crit = _safe_float(row.get("criticalFailureCount")) or 0.0
        if idx is not None:
            agg[prof]["n"] += 1
            agg[prof]["sum"] += idx
            agg[prof]["crit_sum"] += crit

    # CSV
    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["profile", "count", "mean_piqi", "mean_critical_fails"])
        for prof, s in sorted(agg.items()):
            n = s["n"] or 1
            w.writerow([prof, s["n"], round(s["sum"]/n, 2), round(s["crit_sum"]/n, 2)])

    # Markdown
    lines = []
    lines.append(f"# PIQI Summary\n")
    lines.append(f"Total messages: **{total}**\n")
    lines.append("| Profile | Count | Mean PIQI | Mean Critical Fails |")
    lines.append("|---|---:|---:|---:|")
    for prof, s in sorted(agg.items()):
        n = s["n"] or 1
        lines.append(f"| {prof} | {s['n']} | {round(s['sum']/n,2)} | {round(s['crit_sum']/n,2)} |")
    with open(args.md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {args.csv} and {args.md}")

if __name__ == "__main__":
    main()
