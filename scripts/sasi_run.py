from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

try:
    from scripts import fhir_convert_backend as fhir
    from scripts.sasi_analyzer import SaSIAnalyzer
except ImportError:
    import fhir_convert_backend as fhir  # type: ignore
    from sasi_analyzer import SaSIAnalyzer  # type: ignore


def iter_hl7_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    yield from sorted(path.glob("*.hl7"))
    yield from sorted(path.glob("*.txt"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Run SaSI over HL7 files using PIQITT's existing converter.")
    ap.add_argument("input", help="HL7 file or folder containing .hl7/.txt files")
    ap.add_argument("--sam", default="sasi_sam_library.yaml", help="SaSI SAM library YAML")
    ap.add_argument("--profile", default="profiles/profile_sasi_minimal.yaml", help="SaSI profile YAML")
    ap.add_argument("--out", default="sasi_results.ndjson", help="Output NDJSON path")
    ap.add_argument("--include-inventories", action="store_true", help="Include source/target inventories in each result")
    args = ap.parse_args()

    analyzer = SaSIAnalyzer(args.sam, args.profile)
    input_path = Path(args.input)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    message_count = 0
    with out_path.open("w", encoding="utf-8") as out:
        for path in iter_hl7_files(input_path):
            raw = path.read_text(encoding="utf-8", errors="replace")
            for idx, message in enumerate(fhir.split_messages(raw), start=1):
                bundle, msg_type = fhir.convert_message_to_bundle(message)
                result = analyzer.evaluate(
                    message,
                    bundle,
                    message_type=msg_type,
                    source_file=path.name,
                    source_index=idx,
                    include_inventories=args.include_inventories,
                )
                out.write(json.dumps(result, ensure_ascii=False) + "\n")
                message_count += 1

    print(json.dumps({"messages": message_count, "out": str(out_path)}))


if __name__ == "__main__":
    main()
