#!/usr/bin/env python3
"""
Top-level orchestrator: run every recovery source in the right order
and merge results into a single output directory.

This script is read-only. It never touches your live vault, your
Obsidian app data, your Chrome profile, or your Claude Code logs.
It only reads from them and writes recovered files to --output.

Usage:
    python recover.py --output ~/vault-recovered
    python recover.py --output ~/vault-recovered \\
                      --since 2026-02-09 --until 2026-05-08
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def run(cmd: list[str]) -> int:
    print(f"\n$ {' '.join(cmd)}")
    return subprocess.call(cmd)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, required=True, help="Recovery output directory"
    )
    parser.add_argument(
        "--vault-marker",
        default="Obsidian",
        help="Path segment that identifies your vault in absolute paths",
    )
    parser.add_argument(
        "--since",
        default=(date.today() - timedelta(days=120)).isoformat(),
        help="Chrome history start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--until",
        default=date.today().isoformat(),
        help="Chrome history end date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--skip", action="append", default=[],
        choices=["indexeddb", "claude-logs", "chrome-history", "web-clipper"],
        help="Skip a specific source (can be passed multiple times)",
    )
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    py = sys.executable
    failures: list[str] = []

    if "indexeddb" not in args.skip:
        rc = run(
            [
                py, str(SCRIPT_DIR / "extract_obsidian_indexeddb.py"),
                "--output", str(args.output),
            ]
        )
        if rc != 0:
            failures.append("indexeddb")

    if "claude-logs" not in args.skip:
        rc = run(
            [
                py, str(SCRIPT_DIR / "extract_claude_logs.py"),
                "--vault-marker", args.vault_marker,
                "--output", str(args.output / "_FROM_CLAUDE_LOGS"),
            ]
        )
        if rc != 0:
            failures.append("claude-logs")

    if "chrome-history" not in args.skip:
        rc = run(
            [
                py, str(SCRIPT_DIR / "extract_chrome_history.py"),
                "--start", args.since,
                "--end", args.until,
                "--output", str(args.output / "_REFERENCES"),
            ]
        )
        if rc != 0:
            failures.append("chrome-history")

    if "web-clipper" not in args.skip:
        rc = run(
            [
                py, str(SCRIPT_DIR / "extract_web_clipper.py"),
                "--output", str(args.output / "_REFERENCES" / "web_clipper_history.json"),
            ]
        )
        if rc != 0:
            failures.append("web-clipper")

    print()
    print("=" * 60)
    print(f"📁 Output: {args.output}")
    if failures:
        print(f"⚠️  Some sources failed: {', '.join(failures)}")
        print("   Check the messages above; partial recovery is normal.")
    else:
        print("✅ All sources completed.")
    print()
    print("Next steps:")
    print(f"  1. Review {args.output}/ for full-content recoveries")
    print(f"  2. Read {args.output}/_FULL_FILE_LISTING.tsv to see what existed")
    print(f"  3. Use {args.output}/_REFERENCES/ to retrace your research")
    print(f"  4. See docs/02-recovery-paths.md for how to merge with Time Machine")


if __name__ == "__main__":
    main()
