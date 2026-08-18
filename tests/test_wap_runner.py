from pathlib import Path

import pytest

from scripts.wap_runner import discover_input_files, iter_hl7_messages


def test_iter_hl7_messages_streams_cr_delimited_file(tmp_path: Path):
    path = tmp_path / "sample.hl7"
    path.write_bytes(
        b"MSH|^~\\&|A|FAC|B|FAC|202608181200||ADT^A01|1|P|2.5\r"
        b"PID|1||P1||TEST^ONE\r"
        b"MSH|^~\\&|A|FAC|B|FAC|202608181201||ADT^A01|2|P|2.5\r"
        b"PID|1||P2||TEST^TWO\r"
    )

    messages = list(iter_hl7_messages(path))

    assert len(messages) == 2
    assert messages[0].startswith("MSH|")
    assert "P1" in messages[0]
    assert "P2" in messages[1]


def test_discover_input_files_is_non_recursive_and_sorted(tmp_path: Path):
    (tmp_path / "b.txt").write_text("MSH|x", encoding="utf-8")
    (tmp_path / "a.hl7").write_text("MSH|x", encoding="utf-8")
    (tmp_path / "ignore.json").write_text("{}", encoding="utf-8")
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "nested.hl7").write_text("MSH|x", encoding="utf-8")

    files = discover_input_files(tmp_path)

    assert [path.name for path in files] == ["a.hl7", "b.txt"]


def test_discover_input_files_rejects_empty_folder(tmp_path: Path):
    with pytest.raises(ValueError, match="No .hl7 or .txt files"):
        discover_input_files(tmp_path)
