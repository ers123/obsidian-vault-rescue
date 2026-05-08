# 02 — Recovery paths, in priority order

Each row recovers a different *layer* of your vault. Run as many as
you can; their results compose.

| # | Source | Recovers | Effort | Notes |
|---|--------|----------|--------|-------|
| 1 | **Time Machine** | Full bodies up to last backup | Low | The richest single source if your drive is current. May be weeks/months stale. |
| 2 | **iCloud Recently Deleted** | Files trashed in 30-day window | Low | Empty if your incident bypassed Trash (sign-out merges often do). |
| 3 | **iCloud Data Recovery** (`icloud.com/recovery`) | Files Apple has retained server-side | Low | Different pool from Recently Deleted. Sometimes one is empty and the other isn't. |
| 4 | **Obsidian IndexedDB `*-backup`** | Recent edited files, full content | Medium | Run `extract_obsidian_indexeddb.py`. Captures Obsidian's auto-backup snapshots. Often has the last week. |
| 5 | **Obsidian IndexedDB `*-cache/metadata`** | Frontmatter + headings (skeletons) for *every* file in vault | Medium | Same script. Won't recover bodies, but tells you what existed. |
| 6 | **Claude Code logs** | Files written via Claude | Medium | `extract_claude_logs.py`. Surprisingly rich if you used the agent. |
| 7 | **Chrome history** | URLs you were researching | Low | `extract_chrome_history.py`. Doesn't recover notes — recovers *context* to rebuild them. |
| 8 | **Web Clipper extension storage** | Recent clip URLs + titles + target paths | Low | `extract_web_clipper.py`. Tells you exactly what you most recently clipped. |
| 9 | **AI chat URLs** (from Chrome history) | Full content of conversations | Manual | ChatGPT/Claude/Gemini conversations live on the providers' servers — re-visit each URL. |

## The merge order that worked for me

1. Restore Time Machine to a sandbox folder, **not** to the original
   vault path. e.g. `~/vault-tm-restore/`. This gives you the baseline.
2. Run `scripts/recover.py --output ~/vault-recovered/`. This produces
   a parallel tree containing IndexedDB and Claude-log recoveries.
3. Move the Time Machine restore to your final vault location:

   ```bash
   mv ~/vault-tm-restore ~/Obsidian
   ```

4. Overlay the cache recoveries on top, **newer mtimes win**:

   ```bash
   rsync -av --update \
     --exclude='_SKELETONS/' \
     --exclude='_REFERENCES/' \
     --exclude='_FROM_CLAUDE_LOGS/' \
     --exclude='_*.tsv' \
     --exclude='_*.txt' \
     ~/vault-recovered/ ~/Obsidian/
   ```

5. Overlay the Claude-log recoveries, only filling in gaps:

   ```bash
   rsync -av --ignore-existing \
     ~/vault-recovered/_FROM_CLAUDE_LOGS/ ~/Obsidian/
   ```

6. Keep the metadata bundle outside the vault for reference:

   ```bash
   mkdir -p ~/vault-recovery-references
   mv ~/vault-recovered/_SKELETONS         ~/vault-recovery-references/
   mv ~/vault-recovered/_REFERENCES        ~/vault-recovery-references/
   mv ~/vault-recovered/_FULL_FILE_LISTING.tsv ~/vault-recovery-references/
   mv ~/vault-recovered/_RECOVERY_MANIFEST.txt ~/vault-recovery-references/
   ```

You now have a vault that's the union of every source, with the
newest available version of each file, plus a separate references
bundle for files you can only see the outline of.

## Critical detail: where you put the vault

**Do not put the merged vault back into `~/Documents/`** if that's
where the loss happened. iCloud "Desktop & Documents Folders" sync
will replay the same incident if conditions repeat. Use `~/Obsidian/`
or any other home-directory subfolder. See
[`04-prevention.md`](04-prevention.md).

## What "skeleton" recoveries are useful for

A skeleton is a `.md` file that has the original frontmatter (YAML
properties), the heading hierarchy, and a count of how many list items
existed — but no body text. Example:

```markdown
---
type: reference
created: 2026-04-10
tags:
  - ai
  - ai/tools
---

<!-- SKELETON ONLY: body text not recoverable from cache. -->
<!-- mtime: 2026-04-10T11:42:07  size: 924B  hash: 99894dd4 -->

# Andrej Karpathy

## Relevance to This Wiki

## Related

<!-- 2 list items existed but text not in cache -->
```

Useful because:

- You know the file existed and where in the structure.
- Frontmatter often holds the most critical metadata (tags, dates,
  links).
- Heading text alone often anchors enough memory that you can rewrite
  the body in 5 minutes instead of from scratch.
- Internal `[[wikilinks]]` from other notes still resolve to the
  skeleton, so cross-references survive.

Treat skeletons as scaffolding, not as recovered files. Either
rewrite them when you next encounter the topic, or leave them alone
if the body wasn't important.
