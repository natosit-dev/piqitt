from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.fhir_convert_backend import convert_message_to_bundle, split_messages


def convert_file(input_path: str | Path, message_index: int = 1) -> tuple[dict, str, int]:
    """Convert one 1-based HL7 message from a file into a FHIR Bundle."""
    source = Path(input_path)
    raw = source.read_text(encoding="utf-8", errors="ignore")
    messages = split_messages(raw)
    if not messages:
        raise ValueError(f"No HL7 messages beginning with MSH| found in {source}")
    if message_index < 1 or message_index > len(messages):
        raise IndexError(
            f"message_index {message_index} is outside 1..{len(messages)} for {source}"
        )
    bundle, message_type = convert_message_to_bundle(messages[message_index - 1])
    return bundle, message_type, len(messages)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert one HL7 v2 message to a FHIR Bundle using PIQITT's existing converter."
    )
    parser.add_argument("--input", required=True, help="HL7/.txt input file")
    parser.add_argument("--output", required=True, help="FHIR JSON output file")
    parser.add_argument(
        "--message-index",
        type=int,
        default=1,
        help="1-based message number when the input contains multiple MSH messages (default: 1)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write compact JSON instead of pretty-printed JSON",
    )
    args = parser.parse_args()

    bundle, message_type, message_count = convert_file(args.input, args.message_index)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(bundle, indent=None if args.compact else 2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "input": str(Path(args.input)),
                "output": str(output),
                "message_index": args.message_index,
                "message_count": message_count,
                "message_type": message_type,
                "resource_count": len(bundle.get("entry", [])),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
