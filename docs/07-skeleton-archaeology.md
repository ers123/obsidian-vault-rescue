# 07 — Reading skeleton paths to reconstruct vault history

> The skeletons in `_SKELETONS/` aren't just placeholders. The
> set of paths they cover, and the gaps between them, encode a
> surprising amount of history about your vault — including
> reorganizations you'd partly forgotten about.

`extract_obsidian_indexeddb.py` walks every `<vaultId>-cache`
database in your IndexedDB and unions their inventories. That
union is, in effect, **the trail of every file Obsidian has ever
indexed in this vault, across every reorganization**, with
mtimes that tell you when each path last existed.

## What the path set tells you

Group the skeleton paths by parent directory and sort by mtime.
Three patterns matter:

1. **Two parallel paths for "the same" file** — usually means
   you renamed or moved it. The older one has an earlier mtime
   and lives at the old path; the newer one has a later mtime
   and lives at the new path.

2. **A folder appears with a single mtime cluster around one
   day** — usually means you created or restructured that
   folder in one session. Useful for placing skeletons in a
   timeline.

3. **A folder splits into a parent and an `_Archive/`
   subfolder** — usually means you did a "cleanup" pass: kept
   recent files at the parent, moved older ones to `_Archive/`.

## A real example from my own recovery

When I joined the cache databases, I noticed this:

```
2026-03-16T23:12:00  ⚙️ 05-System/Templates/Quick Note.md         103B
2026-03-16T23:12:02  ⚙️ 05-System/Templates/Reference.md           146B
2026-03-16T23:12:03  ⚙️ 05-System/Templates/Question.md            128B
2026-03-16T23:12:04  ⚙️ 05-System/Templates/Project.md             134B
...
2026-01-22T16:57:18  ⚙️ 05-System/Templates/_Archive/memo_template.md     113B
2026-01-22T16:57:18  ⚙️ 05-System/Templates/_Archive/Reading Notes.md     105B
2026-01-22T16:57:18  ⚙️ 05-System/Templates/_Archive/H- Main.md           47B
2026-01-22T16:57:18  ⚙️ 05-System/Templates/_Archive/R- Books.md          218B
... (15 files, all archived in the same minute) ...
2025-09-16T15:51:55  ⚙️ 05-System/Templates/_Archive/Client Project Template.md  3704B
```

Three things became obvious from that pattern alone:

1. **2025-09-16**: I'd done an earlier cleanup pass and
   archived `Client Project Template.md`, `Business Framework
   Template.md`, and the older `Tag System Guide.md`.
2. **2026-01-22**: I'd archived the rest of the old templates
   in one batch — every "_Archive" file with that exact second
   was bulk-moved together.
3. **2026-03-16**: I'd designed a new minimal template system
   from scratch — five short files (Quick Note, Reference,
   Question, Project, Tag System Guide) all created within
   ~5 seconds of each other.

None of this was in any single recovered file. It was visible
only in the *pattern* of paths and timestamps across the cache
union.

## Why this matters for recovery

Once you can see the timeline, you can decide what to actually
restore vs. what was deliberately retired. In my case, the
default behavior of "merge skeletons into the vault" would have
brought back 15 templates I'd already chosen to archive. Instead
I:

- Restored the `_Archive/` structure, keeping the archived
  templates for reference.
- Created placeholder files for the new top-level templates
  (whose bodies were lost), so the new system was visible in
  the vault structure even if I had to rewrite the bodies.
- Gave Claude Desktop's Project Instructions the new system,
  not the old one, so future notes wouldn't accidentally use
  the retired templates.

## How to do this for your own recovery

Pull the path inventory from your `_FULL_FILE_LISTING.tsv` and
group by folder. Some quick recipes:

```bash
# Folder activity timeline — most recently changed folders first
awk -F'\t' '{ split($2, parts, "/"); print $1, parts[1] }' _FULL_FILE_LISTING.tsv \
  | sort -u | sort -r | head -40

# All paths in one folder, sorted by mtime
grep -F 'Templates/' _FULL_FILE_LISTING.tsv | sort -r

# Paths that look like they were renamed — same basename in two places
awk -F'\t' '{ n=split($2, p, "/"); print p[n] }' _FULL_FILE_LISTING.tsv \
  | sort | uniq -c | sort -rn | awk '$1 > 1' | head

# Mass-move events — multiple paths with mtimes within 1 second of each other
awk -F'\t' '{print substr($1, 1, 19)}' _FULL_FILE_LISTING.tsv \
  | sort | uniq -c | sort -rn | head
```

The third recipe (basenames appearing in two paths) is the
quickest way to spot files you renamed; the fourth (mtime
clusters) is the quickest way to spot bulk moves.

## What this doesn't tell you

This is path-and-time archaeology. It can't recover bodies, and
it can't tell you why you made a change. But once you see *that*
you reorganized in a particular way, you can usually remember
*why* — and for anyone else inheriting the vault (your future
self after a long break, a teammate, an AI assistant you
configure), encoding that "why" into the new vault structure is
the thing that keeps the reorganization from being undone the
next time.
