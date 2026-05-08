#!/usr/bin/env python3
"""
Extract recent clipping history from the Obsidian Web Clipper Chrome extension.

The Web Clipper stores recent actions (URL, title, target path, timestamp)
in Chrome's Local Extension Settings LevelDB. The store is small but rich:
it's a snapshot of *exactly* what you most recently clipped or were about
to clip — invaluable when those notes themselves are gone.

Usage:
    python extract_web_clipper.py \\
        --extension-storage ~/Library/Application\\ Support/Google/Chrome/Default/Local\\ Extension\\ Settings/cnjifjpddelmedmihgijeibhnjfabmlf \\
        --output ./web_clipper_history.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# Web Clipper extension ID (Chrome Web Store)
DEFAULT_EXTENSION_ID = "cnjifjpddelmedmihgijeibhnjfabmlf"


def extract_strings(path: Path) -> str:
    """Pull printable ASCII/UTF-8 runs from a binary LevelDB file."""
    raw = path.read_bytes()
    # Same heuristic as the `strings` tool: 4+ byte runs of printable bytes.
    return re.sub(rb"[^\x20-\x7e\n]+", b"\n", raw).decode("utf-8", errors="replace")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--extension-storage",
        type=Path,
        default=Path.home()
        / "Library/Application Support/Google/Chrome/Default/Local Extension Settings"
        / DEFAULT_EXTENSION_ID,
        help="Path to the Web Clipper extension's LevelDB directory",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if not args.extension_storage.exists():
        raise SystemExit(
            f"Extension storage not found: {args.extension_storage}\n"
            "Make sure Chrome is installed and the Web Clipper extension was used."
        )

    # Combine .log + .ldb so we catch both compacted and pending writes.
    text_chunks: list[str] = []
    for f in sorted(args.extension_storage.glob("*.log")):
        text_chunks.append(extract_strings(f))
    for f in sorted(args.extension_storage.glob("*.ldb")):
        text_chunks.append(extract_strings(f))

    blob = "\n".join(text_chunks)

    # The history value is a JSON array stored as a Chrome storage value.
    # We pull every history entry by regex; entries look like:
    #   "datetime":"...","path":"...","title":"...","url":"..."
    entries = []
    for m in re.finditer(
        r'"datetime":"([^"]+)","path":"([^"]*)","title":"([^"]+)","url":"([^"]+)"',
        blob,
    ):
        entries.append(
            {
                "datetime": m.group(1),
                "path": m.group(2),
                "title": m.group(3),
                "url": m.group(4),
            }
        )

    # Dedup (LevelDB can hold many overlapping snapshots)
    seen = set()
    unique = []
    for e in entries:
        key = (e["datetime"], e["url"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(e)
    unique.sort(key=lambda e: e["datetime"], reverse=True)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(unique, indent=2, ensure_ascii=False))

    print(f"found {len(unique)} unique clipping history entries")
    for e in unique[:10]:
        print(f"  {e['datetime']}  {e['title'][:60]}  →  {e['url'][:60]}")
    print(f"\nOutput: {args.output}")


if __name__ == "__main__":
    main()
