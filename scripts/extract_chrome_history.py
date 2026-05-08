#!/usr/bin/env python3
"""
Extract Chrome browsing history during a date window — useful for
reconstructing what notes you were working on or planning to clip.

When notes themselves are gone, the URLs you visited often contain enough
context to rebuild them (re-clip articles, replay AI chats, find videos).

Usage:
    python extract_chrome_history.py \\
        --history ~/Library/Application\\ Support/Google/Chrome/Default/History \\
        --start 2026-02-09 --end 2026-05-01 \\
        --output ./references
"""
from __future__ import annotations

import argparse
import shutil
import sqlite3
import tempfile
from pathlib import Path


CONTENT_SITES = (
    "%substack.com%",
    "%medium.com/%",
    "%every.to%",
    "%linkedin.com/pulse%",
    "%coursera.org%",
    "%paulgraham%",
    "%ycombinator%",
    "%a16z.com%",
    "%simonwillison.net%",
    "%lennysnewsletter%",
    "%lethain%",
    "%benthompson%",
    "%stratechery%",
    "%huggingface.co/blog%",
    "%openai.com/blog%",
    "%anthropic.com/news%",
)
AI_CHAT_SITES = (
    "%chatgpt.com/c/%",
    "%claude.ai/chat/%",
    "%claude.ai/new%",
    "%gemini.google.com%",
    "%perplexity.ai/search%",
    "%notebooklm.google%",
)


def query(db: sqlite3.Connection, sql: str, params=()) -> list[tuple]:
    return db.execute(sql, params).fetchall()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--history",
        type=Path,
        default=Path.home()
        / "Library/Application Support/Google/Chrome/Default/History",
    )
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    if not args.history.exists():
        raise SystemExit(f"History DB not found: {args.history}")

    # Chrome locks the live DB; copy first
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        shutil.copy(args.history, tmp.name)
        db_path = tmp.name

    db = sqlite3.connect(db_path)

    # Convert Chrome's last_visit_time (microseconds since 1601-01-01) to local datetime via SQL
    base = (
        "SELECT datetime(last_visit_time/1000000-11644473600, 'unixepoch', 'localtime') as v, "
        "url, title, visit_count FROM urls "
        "WHERE v BETWEEN ? AND ?"
    )

    def write_tsv(name: str, rows: list[tuple]) -> None:
        path = args.output / name
        with open(path, "w", encoding="utf-8") as f:
            f.write("visited\turl\ttitle\tvisit_count\n")
            for r in rows:
                f.write("\t".join(str(x) for x in r) + "\n")
        print(f"  📝 {name}: {len(rows)} rows")

    # All visits in range
    rows = query(db, base + " ORDER BY last_visit_time DESC", (args.start, args.end))
    write_tsv("all_visits.tsv", rows)

    # Content sites (likely article reading / clipping candidates)
    site_filter = " OR ".join(["url LIKE ?"] * len(CONTENT_SITES))
    rows = query(
        db,
        base + f" AND ({site_filter}) ORDER BY last_visit_time DESC",
        (args.start, args.end, *CONTENT_SITES),
    )
    write_tsv("content_sites.tsv", rows)

    # AI chats (full content stays on the provider's servers — re-visit to recover)
    ai_filter = " OR ".join(["url LIKE ?"] * len(AI_CHAT_SITES))
    rows = query(
        db,
        base + f" AND ({ai_filter}) ORDER BY last_visit_time DESC",
        (args.start, args.end, *AI_CHAT_SITES),
    )
    write_tsv("ai_chats.tsv", rows)

    # YouTube
    rows = query(
        db,
        base + " AND url LIKE '%youtube.com/watch%' ORDER BY last_visit_time DESC",
        (args.start, args.end),
    )
    write_tsv("youtube.tsv", rows)

    # Top domains
    domain_sql = """
        SELECT
            CASE
                WHEN url LIKE 'https://%/%' THEN substr(url, 9, instr(substr(url,9), '/')-1)
                WHEN url LIKE 'http://%/%'  THEN substr(url, 8, instr(substr(url,8), '/')-1)
                ELSE url END AS domain,
            count(*) AS cnt
        FROM urls
        WHERE datetime(last_visit_time/1000000-11644473600, 'unixepoch', 'localtime') BETWEEN ? AND ?
        GROUP BY domain
        ORDER BY cnt DESC LIMIT 50
    """
    rows = query(db, domain_sql, (args.start, args.end))
    with open(args.output / "top_domains.tsv", "w", encoding="utf-8") as f:
        f.write("domain\tcount\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    print(f"  📝 top_domains.tsv: {len(rows)} rows")

    db.close()
    print(f"\n📁 Output: {args.output}")


if __name__ == "__main__":
    main()
