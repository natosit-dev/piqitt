#piqi_regression_diff.py
import argparse, json, os, sys, glob
from typing import Dict, Any, List, Tuple

def _load_results_dir(d: str) -> Dict[str, Dict[str, Any]]:
    """
    Returns dict keyed by a stable key with row dict.
    Key preference: messageId if present, else <file>#<idx>.
    """
    out = {}
    for path in glob.glob(os.path.join(d, "*.json")):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        base = os.path.basename(path)
        for i, row in enumerate(data):
            msg_id = str(row.get("messageId") or "").strip()
            key = msg_id if msg_id else f"{base}#{i+1}"
            out[key] = row
    return out

def main():
    ap = argparse.ArgumentParser(description="Compare PIQI results to a baseline (regression diff).")
    ap.add_argument("--new", required=True, help="Directory with NEW *.piqi.json results")
    ap.add_argument("--baseline", required=True, help="Directory with BASELINE *.piqi.json results")
    ap.add_argument("--threshold", type=float, default=0.1, help="Allowed absolute PIQI index drift (default 0.1)")
    ap.add_argument("--out", default="piqi_regression_diff.json", help="Output JSON report")
    args = ap.parse_args()

    new_map = _load_results_dir(args.new)
    base_map = _load_results_dir(args.baseline)

    report = {"threshold": args.threshold, "drift": [], "missing_in_new": [], "missing_in_baseline": []}

    # find drifts
    for key, base_row in base_map.items():
        if key not in new_map:
            report["missing_in_new"].append(key)
            continue
        new_row = new_map[key]
        nb = base_row.get("piqiIndex")
        nn = new_row.get("piqiIndex")
        if nb is None or nn is None:
            continue
        diff = float(nn) - float(nb)
        if abs(diff) > args.threshold:
            report["drift"].append({
                "key": key,
                "baseline": nb,
                "new": nn,
                "delta": diff
            })

    # anything new that baseline doesn’t have
    for key in new_map.keys():
        if key not in base_map:
            report["missing_in_baseline"].append(key)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Wrote {args.out}")
    if report["drift"] or report["missing_in_new"]:
        sys.exit(1)  # non-zero for CI visibility

if __name__ == "__main__":
    main()
