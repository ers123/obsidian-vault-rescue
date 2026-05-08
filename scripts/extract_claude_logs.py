#!/usr/bin/env python3
"""
Extract vault file content from Claude Code conversation logs.

If you used Claude Code (Anthropic's terminal agent) to work in your vault,
every Write/Edit tool call is preserved in JSONL session logs at
    ~/.claude/projects/.../*.jsonl
This script scans every log, finds tool calls that wrote to your vault path,
and reconstructs the latest version of each file.

Usage:
    python extract_claude_logs.py \\
        --logs   ~/.claude/projects \\
        --vault-marker Obsidian \\
        --output ./recovered_from_logs
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--logs",
        type=Path,
        default=Path.home() / ".claude/projects",
        help="Root of Claude Code session logs (default: ~/.claude/projects)",
    )
    parser.add_argument(
        "--vault-marker",
        default="Obsidian",
        help="Path segment that identifies your vault (default: 'Obsidian')",
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Output directory"
    )
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    # Latest Write per (target path)
    writes: dict[str, tuple[str, str]] = {}  # path -> (timestamp, content)
    edits: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    total_logs = 0
    logs_with_writes = 0
    bad_lines = 0

    for log_file in args.logs.rglob("*.jsonl"):
        total_logs += 1
        had_write = False
        try:
            with open(log_file) as f:
                for line in f:
                    try:
                        rec = json.loads(line)
                    except Exception:
                        bad_lines += 1
                        continue
                    msg = rec.get("message", {}) or {}
                    timestamp = rec.get("timestamp", "")
                    content = msg.get("content", [])
                    if isinstance(content, str):
                        content = [{"type": "text", "text": content}]
                    if not isinstance(content, list):
                        continue
                    for c in content:
                        if not isinstance(c, dict):
                            continue
                        if c.get("type") != "tool_use":
                            continue
                        name = c.get("name", "")
                        inp = c.get("input", {}) or {}
                        fp = inp.get("file_path", "")
                        if not fp or args.vault_marker not in fp:
                            continue
                        had_write = True
                        if name == "Write":
                            body = inp.get("content", "")
                            if body and (
                                fp not in writes or timestamp > writes[fp][0]
                            ):
                                writes[fp] = (timestamp, body)
                        elif name == "Edit":
                            edits[fp].append(
                                (
                                    timestamp,
                                    inp.get("old_string", ""),
                                    inp.get("new_string", ""),
                                )
                            )
        except Exception:
            continue
        if had_write:
            logs_with_writes += 1

    print(f"📊 scanned {total_logs} logs ({logs_with_writes} touched the vault)")
    print(f"   bad lines: {bad_lines}")
    print(f"   unique files written: {len(writes)}")
    print(f"   unique files edited:  {len(edits)}")

    # Save Writes (latest version)
    saved = 0
    for fp, (_ts, body) in writes.items():
        parts = Path(fp).parts
        try:
            i = parts.index(args.vault_marker)
            rel = Path(*parts[i + 1 :])
        except ValueError:
            continue
        out = args.output / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        saved += 1

    # Apply Edits sequentially (best-effort) on top of recovered Writes
    applied = 0
    for fp, edit_list in edits.items():
        edit_list.sort()
        parts = Path(fp).parts
        try:
            i = parts.index(args.vault_marker)
            rel = Path(*parts[i + 1 :])
        except ValueError:
            continue
        out = args.output / rel
        if not out.exists():
            continue
        text = out.read_text(encoding="utf-8", errors="replace")
        for _ts, old, new in edit_list:
            if old and old in text:
                text = text.replace(old, new, 1)
                applied += 1
        out.write_text(text, encoding="utf-8")

    print(f"\n✅ saved {saved} files to {args.output}")
    print(f"✅ applied {applied} sequential edits on top")


if __name__ == "__main__":
    main()
