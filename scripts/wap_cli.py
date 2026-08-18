from __future__ import annotations

import argparse
import json

from scripts.wap_runner import EvaluationConfig, run_piqitt


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run PIQITT against a local HL7 file or folder without browser upload."
    )
    parser.add_argument("--input", required=True, help="Local .hl7/.txt file or folder")
    parser.add_argument(
        "--profile",
        default="AUTO",
        choices=["AUTO", "Clinical-Minimal", "Claims-Minimal"],
    )
    parser.add_argument("--db", default="data/piqitt_runs.duckdb", help="DuckDB run repository")
    parser.add_argument("--output-root", default="runs", help="Directory for run artifacts")
    parser.add_argument("--sam-library", default="piqi_sam_library.yaml")
    parser.add_argument("--clinical-profile", default="profiles/profile_clinical_minimal.yaml")
    parser.add_argument("--claims-profile", default="profiles/profile_claims_minimal.yaml")
    parser.add_argument("--loinc", default="ref/loinc.csv")
    parser.add_argument("--cpt", default="ref/cpt.csv")
    parser.add_argument("--plausibility", default="ref/plausibility.yaml")
    parser.add_argument("--progress-every", type=int, default=1000)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = EvaluationConfig(
        sam_library_path=args.sam_library,
        clinical_profile_path=args.clinical_profile,
        claims_profile_path=args.claims_profile,
        loinc_csv=args.loinc,
        cpt_csv=args.cpt,
        plausibility_yaml=args.plausibility,
        profile_name=args.profile,
    )

    def progress(event):
        kind = event.get("event")
        if kind == "file_started":
            print(f"[{event['file_number']}/{event['file_count']}] {event['file_name']} ...")
        elif kind == "progress":
            print(
                f"  {event['file_name']}: {event['file_message_count']:,} messages "
                f"(run {event['run_message_count']:,})"
            )
        elif kind == "file_complete":
            print(
                f"  COMPLETE {event['file_name']}: {event['message_count']:,} messages, "
                f"PIQI {event['mean_piqi']:.2f}"
            )
        elif kind == "file_failed":
            print(f"  FAILED {event['file_name']}: {event['error_message']}")

    summary = run_piqitt(
        args.input,
        config=config,
        db_path=args.db,
        output_root=args.output_root,
        progress_callback=progress,
        progress_every=args.progress_every,
    )
    print(json.dumps(summary, indent=2, default=str))
    return 0 if summary["status"] == "COMPLETE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
