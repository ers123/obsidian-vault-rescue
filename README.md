# obsidian-vault-rescue

A forensic playbook and toolkit for recovering Obsidian vaults
lost to iCloud "Desktop & Documents Folders" sync incidents.

If your vault disappeared after iCloud cleanup, an account
sign-out, or a "merge" dialog you didn't fully read — most of it
is probably still recoverable. Just not from where Apple tells
you to look.

This repo packages what worked when I lost my own vault in May
2026: 1,500 markdown notes gone, no warning, no Trash, Time
Machine three months stale. I got back about 99% of the file
structure, full content for the most recent week, and reference
traces for everything I'd been reading. Across seven data
sources nobody documents in one place.

A note before you go further: I'm not a developer. I'm an
Obsidian user who happens to use AI assistants daily, and the
recovery in this repo was the result of seven hours of working
through the problem with Claude. The scripts here are the
cleaned-up version of what we landed on together. If you're in
the same boat — not a coder, vault gone, panicking — that's
exactly who this is for.

## If this just happened to you, read this first

Before anything else, stop these:

1. Don't reinstall Obsidian. Its IndexedDB cache holds your last
   week of edits. Reinstalling wipes it.
2. Don't sign out of iCloud. That can trigger another merge
   dialog and finish the deletion on your other devices.
3. Don't empty the Trash anywhere.
4. If you have a second Mac (or iPad) with the same Apple ID,
   disconnect it from Wi-Fi now. It may still have a local copy
   that iCloud is about to overwrite. Buying minutes here is
   worth everything.

Then read [`docs/01-diagnosis.md`](docs/01-diagnosis.md).

## What this toolkit does

It runs read-only extractors against every place Obsidian,
Chrome, and Claude Code keep traces of your work, then writes
everything to a single `--output` directory you can browse,
merge, and selectively restore from.

| Source | What you get | Script |
|--------|--------------|--------|
| Time Machine / iCloud Data Recovery | Full bodies up to last backup or 30-day window | (manual — see docs) |
| Obsidian IndexedDB `*-backup` | Recent edited files, full content | `scripts/extract_obsidian_indexeddb.py` |
| Obsidian IndexedDB `*-cache/metadata` | Frontmatter and headings for every file in the vault | (same script) |
| Claude Code conversation logs | Every file written or edited via Claude | `scripts/extract_claude_logs.py` |
| Chrome browsing history | URLs you were researching, AI chat URLs (see below) | `scripts/extract_chrome_history.py` |
| Obsidian Web Clipper extension | Recent clipping history (URL, title, target path) | `scripts/extract_web_clipper.py` |
| **AI chat history (ChatGPT, Claude, NotebookLM, …)** | **Whole notes you co-created with an assistant — paste-ready** | manual; URL list comes from Chrome history |

A single orchestrator, `scripts/recover.py`, runs them all.

The last row turned out to be the highest-yield path for me.
Conversations you had with AI assistants while writing notes
live on the providers' servers, untouched by local data loss.
For documents you co-created with an assistant — drafts,
prompts, summaries — you can usually re-extract them verbatim
in one prompt. See [`docs/06-ai-chat-recovery.md`](docs/06-ai-chat-recovery.md).

## Quick start

```bash
git clone https://github.com/ers123/obsidian-vault-rescue
cd obsidian-vault-rescue

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run everything. Read-only — this never touches your live data.
python scripts/recover.py --output ~/vault-recovered
```

The output directory will look something like this (folder names
will be your own vault's structure):

```
~/vault-recovered/
├── 02-Library/                   ← full-content recoveries
├── 05-System/
├── _SKELETONS/                   ← frontmatter + headings for every file
├── _FROM_CLAUDE_LOGS/            ← files written via Claude Code
├── _REFERENCES/
│   ├── all_visits.tsv            ← every URL you visited in the date window
│   ├── content_sites.tsv         ← Substack / Every / Medium / etc.
│   ├── ai_chats.tsv              ← ChatGPT / Claude / Gemini conversation URLs
│   ├── youtube.tsv
│   └── web_clipper_history.json  ← recent clips with titles + URLs
├── _FULL_FILE_LISTING.tsv        ← every file that existed, with mtime + size
└── _RECOVERY_MANIFEST.txt        ← what was fully recovered, newest first
```

## How to merge recoveries with Time Machine

The richest combination is usually:

1. Time Machine — restored to its own folder, gives you full
   bodies for everything that was in the vault at the last
   backup point.
2. `scripts/extract_obsidian_indexeddb.py` — overlay the last
   week of edits (newer mtimes win).
3. `scripts/extract_claude_logs.py` — overlay anything you wrote
   collaboratively with Claude Code.
4. `_SKELETONS/` — keep separately as scaffolding for files
   whose bodies are unrecoverable. Use them to remember
   structure when rewriting.
5. `_REFERENCES/ai_chats.tsv` — re-open the ChatGPT / Claude
   conversations. Their full content lives on the providers'
   servers and is often the best source for notes that were
   synthesizing them.

See [`docs/02-recovery-paths.md`](docs/02-recovery-paths.md) for
the exact merge commands.

## The story behind this

[`CASE_STUDY.md`](CASE_STUDY.md) — what actually happened, what
worked, what didn't, every dead end, and what working through
this with an AI assistant looked like in practice if you're not
a programmer.

## Prevention (read this even if nothing has happened to you)

[`docs/04-prevention.md`](docs/04-prevention.md)

The short version:

- Don't keep your vault inside `~/Documents/` or `~/Desktop/` if
  iCloud "Desktop & Documents Folders" sync is on.
- Use a path outside the iCloud sync zone, e.g. `~/Obsidian/`.
- For multi-device, pay for Obsidian Sync or use a private Git
  repo. Don't sync the vault itself through iCloud.
- Keep an external Time Machine drive plugged in. Most people
  whose backup helped here had a stale one because the drive sat
  in a drawer.

## Why this happens (and why Apple won't fix it)

[`docs/05-why-icloud-fails.md`](docs/05-why-icloud-fails.md) —
analysis of the architectural choices that make this loss
pattern inevitable, and why none of them are bugs Apple would
describe as broken.

## Two recovery techniques you don't see elsewhere

- [`docs/06-ai-chat-recovery.md`](docs/06-ai-chat-recovery.md) —
  using your AI chat history (ChatGPT, Claude, NotebookLM, …)
  as a primary content recovery source. The single most
  surprising thing in my own recovery.
- [`docs/07-skeleton-archaeology.md`](docs/07-skeleton-archaeology.md)
  — reading the set of recovered skeleton paths to reconstruct
  vault history (folder reorganizations, mass moves, template
  redesigns) that no single file by itself records.

## Contributing

If you've recovered a vault using a path this repo doesn't
cover yet, open a PR — especially for non-Obsidian apps that
use Chromium-based local cache (Logseq, Notion, Anytype,
Reflect, …). Most of the extraction logic generalizes.

## License

MIT. Use it, fork it, save someone's vault.

## Disclaimer

This is not data-recovery advice from a professional. It's what
worked for me. Run scripts at your own risk; they're read-only
by design but software has bugs. Always work from a copy of any
cache you don't want to lose.
