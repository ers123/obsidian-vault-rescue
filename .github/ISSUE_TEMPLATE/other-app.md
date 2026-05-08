---
name: Adapt this for another app (Logseq, Notion, Anytype, …)
about: You want to use the same approach for a non-Obsidian Electron app.
title: "[Adapt] "
labels: enhancement
---

## Which app

Logseq / Notion / Anytype / Reflect / other:

## Where its data lives

`~/Library/Application Support/...`:

## What you've already found

- IndexedDB path:
- Database names visible (run a quick `ls` on the leveldb dir or
  use `ccl_chromium_reader` to list `db.database_ids`):
- Object stores that look like content:
- Anything that looks like a path-keyed or hash-keyed store:

## What you've tried

A short description of what you ran and what worked / didn't. PRs
that add a new extractor under `scripts/` for the app are
especially welcome.
