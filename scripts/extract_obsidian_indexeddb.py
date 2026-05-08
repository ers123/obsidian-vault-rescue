#!/usr/bin/env python3
"""
Extract recoverable note content from Obsidian's Chromium IndexedDB cache.

Obsidian caches three useful things in IndexedDB:
  1. Auto-backup snapshots of recently-edited notes (FULL CONTENT)
  2. Per-file metadata (frontmatter, headings, list-item structure)
  3. File inventory (paths, mtimes, sizes, content hashes)

When your vault on disk is gone but the Obsidian app still has its cache,
this script reconstructs as much as it can: full bodies for files in
the backup store, and skeleton outlines (frontmatter + headings) for
everything else.

Usage:
    python extract_obsidian_indexeddb.py \\
        --indexeddb ~/Library/Application\\ Support/obsidian/IndexedDB \\
        --output    ./recovered

Requires: ccl_chromium_reader (https://github.com/cclgroupltd/ccl_chromium_reader)
    pip install git+https://github.com/cclgroupltd/ccl_chromium_reader.git
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from ccl_chromium_reader import ccl_chromium_indexeddb


def find_obsidian_idb(indexeddb_root: Path) -> tuple[Path, Path]:
    """Locate the Obsidian leveldb + blob directories under an IndexedDB root."""
    leveldb = next(indexeddb_root.glob("app_obsidian.md_*.indexeddb.leveldb"), None)
    blob = next(indexeddb_root.glob("app_obsidian.md_*.indexeddb.blob"), None)
    if not leveldb:
        raise FileNotFoundError(
            f"No Obsidian leveldb found under {indexeddb_root}. "
            "Make sure you point at the IndexedDB directory inside "
            "~/Library/Application Support/obsidian/"
        )
    return leveldb, blob


def safe_relative(file_path: str) -> Path | None:
    """Map an Obsidian file path back to a vault-relative Path.

    Obsidian writes absolute paths like
        /Users/<you>/Documents/Obsidian/some/note.md
    We strip everything up to and including the vault root segment so the
    output mirrors the vault structure regardless of where it lived.
    """
    parts = Path(file_path).parts
    for marker in ("Obsidian", "vault", "Vault"):
        if marker in parts:
            i = parts.index(marker)
            return Path(*parts[i + 1 :])
    return None


def extract_backups(db, output_dir: Path) -> tuple[int, int, list[tuple]]:
    """Extract full note bodies from any *-backup database.

    Obsidian's backup feature captures recent edits keyed by path + timestamp.
    There are typically multiple revisions per file; we keep the newest.

    Returns (recovered_count, skipped_bad_records, manifest).
    """
    bad = [0]

    def bad_handler(_key, _raw):
        bad[0] += 1

    recovered = 0
    manifest: list[tuple[str, str, int]] = []
    seen_latest_ts: dict[str, float] = {}

    for db_id in db.database_ids:
        database = db[db_id]
        if "backup" not in database.name.lower():
            continue
        for store_name in database.object_store_names:
            store = database[store_name]
            try:
                for record in store.iterate_records(
                    bad_deserializer_data_handler=bad_handler
                ):
                    val = record.value
                    if not isinstance(val, dict):
                        continue
                    path = val.get("path")
                    ts = val.get("ts")
                    data = val.get("data")
                    if not path or data is None:
                        continue

                    rel = safe_relative(path) or Path(path).name
                    out_path = output_dir / rel

                    # Keep newest revision per logical path
                    prev_ts = seen_latest_ts.get(str(rel))
                    if prev_ts is not None and ts and ts <= prev_ts:
                        continue
                    seen_latest_ts[str(rel)] = ts or 0

                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    out_path.write_text(data, encoding="utf-8")

                    ts_iso = (
                        datetime.fromtimestamp(ts / 1000).isoformat()
                        if ts
                        else "unknown"
                    )
                    manifest.append((ts_iso, str(rel), len(data)))
                    recovered += 1
            except Exception as e:
                print(f"  ⚠️  store '{store_name}' aborted: {e}")

    return recovered, bad[0], manifest


def extract_skeletons(
    db, output_dir: Path, recovered_paths: set[str]
) -> tuple[int, list[tuple]]:
    """Generate skeleton .md (frontmatter + headings) for files we could not
    recover bodies for, by joining each cache database's `file` and
    `metadata` stores.

    `file` store maps path → {mtime, size, hash}.
    `metadata` store maps content hash → {frontmatter, headings, listItems, …}.

    Note: a single LevelDB can hold multiple `<vaultId>-cache` databases —
    one per vault Obsidian has ever opened from this app data dir, including
    older vault ids. We iterate all of them and union their inventories so
    skeletons survive a vault rename or rebuild.
    """
    bad = [0]

    def bad_handler(_key, _raw):
        bad[0] += 1

    listing: list[tuple[str, str, int, str]] = []
    skel_dir = output_dir / "_SKELETONS"
    skel_count = 0

    for db_id in db.database_ids:
        database = db[db_id]
        if not database.name.endswith("-cache"):
            continue
        if "file" not in database.object_store_names:
            continue

        path_to_file: dict[str, dict] = {}
        hash_to_meta: dict[str, dict] = {}

        for r in database["file"].iterate_records(
            bad_deserializer_data_handler=bad_handler
        ):
            if isinstance(r.value, dict):
                # IdbKey __repr__ is "<IdbKey VALUE>" — extract VALUE
                key = str(r.key)
                if key.startswith("<IdbKey "):
                    key = key[len("<IdbKey ") : -1]
                path_to_file[key] = r.value

        if "metadata" in database.object_store_names:
            for r in database["metadata"].iterate_records(
                bad_deserializer_data_handler=bad_handler
            ):
                if isinstance(r.value, dict):
                    key = str(r.key)
                    if key.startswith("<IdbKey "):
                        key = key[len("<IdbKey ") : -1]
                    hash_to_meta[key] = r.value

        for path, finfo in path_to_file.items():
            if not path.endswith(".md"):
                continue
            mtime = finfo.get("mtime", 0)
            size = int(finfo.get("size", 0))
            h = finfo.get("hash", "")
            mt_iso = (
                datetime.fromtimestamp(mtime / 1000).isoformat() if mtime else ""
            )
            listing.append((mt_iso, path, size, h))

            if path in recovered_paths:
                continue

            skel_path = skel_dir / path
            # If multiple cache dbs hold the same path, prefer the one with
            # richer metadata (later iterations can overwrite, which is fine
            # because we re-resolve `meta` and `mtime` from the current db).
            if skel_path.exists():
                continue

            meta = hash_to_meta.get(h)
            skel_path.parent.mkdir(parents=True, exist_ok=True)

            lines: list[str] = []
            if meta:
                fm = meta.get("frontmatter")
                if isinstance(fm, dict) and fm:
                    lines.append("---")
                    for k, v in fm.items():
                        if isinstance(v, list):
                            lines.append(f"{k}:")
                            for item in v:
                                lines.append(f"  - {item}")
                        else:
                            lines.append(f"{k}: {v}")
                    lines.append("---")
                    lines.append("")
                lines.append(
                    "<!-- ⚠️ SKELETON ONLY: body text not recoverable from cache. -->"
                )
                lines.append(
                    f"<!-- mtime: {mt_iso}  size: {size}B  hash: {h[:12]} -->"
                )
                lines.append("")
                for hd in meta.get("headings", []):
                    lvl = hd.get("level", 1)
                    txt = hd.get("heading", "")
                    lines.append(f'{"#" * lvl} {txt}')
                    lines.append("")
                items = meta.get("listItems") or []
                if items:
                    lines.append(
                        f"<!-- {len(items)} list items existed but text not in cache -->"
                    )
            else:
                lines.append("<!-- ⚠️ FILE EXISTED but no metadata cached -->")
                lines.append(f"<!-- mtime: {mt_iso}  size: {size}B -->")

            skel_path.write_text("\n".join(lines), encoding="utf-8")
            skel_count += 1

    return skel_count, listing


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--indexeddb",
        type=Path,
        default=Path.home()
        / "Library/Application Support/obsidian/IndexedDB",
        help="Path to Obsidian IndexedDB directory",
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Output directory"
    )
    args = parser.parse_args()

    leveldb, blob = find_obsidian_idb(args.indexeddb)
    print(f"📂 leveldb: {leveldb}")
    print(f"📂 blob:    {blob}")

    db = ccl_chromium_indexeddb.WrappedIndexDB(leveldb, blob)
    args.output.mkdir(parents=True, exist_ok=True)

    print("\n=== Phase 1: backup store (full bodies) ===")
    recovered, bad, manifest = extract_backups(db, args.output)
    print(f"  ✅ recovered: {recovered} files (deserialization errors: {bad})")

    recovered_paths = {p for _, p, _ in manifest}

    print("\n=== Phase 2: cache + metadata (skeletons) ===")
    skel_count, full_listing = extract_skeletons(
        db, args.output, recovered_paths
    )
    print(f"  ✅ skeletons: {skel_count} files")
    print(f"  📊 inventory: {len(full_listing)} total files in vault")

    # Write manifests
    manifest.sort(reverse=True)
    (args.output / "_RECOVERY_MANIFEST.txt").write_text(
        "Full-content recoveries (newest first)\n"
        + "\n".join(f"{ts}\t{size}\t{path}" for ts, path, size in manifest)
        + "\n"
    )

    full_listing.sort(reverse=True)
    (args.output / "_FULL_FILE_LISTING.tsv").write_text(
        "mtime\tpath\tsize\thash\n"
        + "\n".join(
            "\t".join(str(x) for x in row) for row in full_listing
        )
        + "\n"
    )

    months = Counter(t[:7] for t, _, _ in manifest if t)
    print("\n=== Recovery distribution ===")
    for ym, n in sorted(months.items(), reverse=True)[:10]:
        print(f"  {ym}: {n}")
    print(f"\n📁 Output: {args.output}")


if __name__ == "__main__":
    main()
