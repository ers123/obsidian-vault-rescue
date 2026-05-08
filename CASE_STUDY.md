# Case study: 1,500 Obsidian notes, gone in a merge dialog

> The incident that produced this repo. Names of vault content are
> redacted; everything else is verbatim.

## The setup, briefly

I'd been an Obsidian user for ~3 years. My vault lived at
`~/Documents/Obsidian/` and I had iCloud "Desktop & Documents
Folders" sync turned on so it would appear on my Mac mini at home.
I hadn't thought hard about what that combination meant; the vault
"just worked" across both machines.

I had a Time Machine drive plugged in occasionally. The most recent
backup turned out to be **three months stale**.

I'd been doing significant work in the vault between February and
late April: a major folder reorganization (an explicit move from a
PARA-style structure to a Projects/Library/Incubator/Wiki layout), a
new `🧠 06-Wiki/` folder modeled after Karpathy's LLM Wiki for
tracking AI coding tools, a steady accumulation of web clippings.

## The incident

The day before, Universal Control between my MacBook Air and Mac
mini had been flaky. I'd done a couple of iCloud sign-out / sign-in
cycles trying to nudge it back into working. One of those flows
showed a "merge" dialog about iCloud Drive. I clicked through it
without reading carefully.

The next morning my `~/Documents/` was empty except for a fresh
`.localized` file. The vault folder was gone from both Macs. iCloud
Drive's "Recently Deleted" showed nothing. iCloud Data Recovery at
`icloud.com/recovery` showed nothing. Time Machine's most recent
backup was from February.

## The first hour: stop, then look

What I did right, more out of luck than discipline:

- I didn't reinstall Obsidian. (Its IndexedDB cache turned out to
  hold the most recent week of edits.)
- I didn't sign out of iCloud again.
- Once I realized the Mac mini might still have a local copy, I
  killed its sync daemons (`bird`, `cloudd`, `fileproviderd`) in a
  loop and physically disconnected its Wi-Fi as soon as I got home.

What I almost did wrong, and would warn anyone else against:

- I almost ran Disk Drill against my main APFS volume. APFS plus
  iCloud-mediated deletion produces no recoverable file system blocks
  to scan; Disk Drill would have wasted hours and possibly written
  recovery data to the same volume.
- I almost emptied the Trash on the Mac mini "to free space and try
  again." Obsidian uses per-vault `.trash` folders that are *not* the
  system Trash, so this would have been mostly cosmetic — but I'd
  have been in the wrong frame of mind for everything that followed.

## The recovery, in order

### Apple's own pools — empty

iCloud Recently Deleted: empty. iCloud Data Recovery
(`icloud.com/recovery/`): empty. Time Machine: latest backup
2026-02-09. Local APFS snapshots: one from 2026-02-09 only.

This was the moment of genuine despair. Apple's documented recovery
paths all either had nothing or a 3-month gap.

### Time Machine, despite the gap

I restored the Feb 9 baseline anyway. It gave me 1,092 markdown files
with full bodies — the entire vault as it stood three months earlier.
It was missing every edit, every new note, every folder restructure,
every recent web clipping. But it was a foundation.

Restored to a sandbox path (`~/Documents/Obsidian/`) initially. I'd
later move it to `~/Obsidian/` — see prevention notes.

### Obsidian's IndexedDB, the surprise

Obsidian's app data lives at
`~/Library/Application Support/obsidian/`. Inside `IndexedDB/` is a
Chromium LevelDB that Obsidian uses for its own state.

Two things in there turned out to be invaluable:

1. **`<vaultId>-backup` / `backups` store**: Obsidian's auto-backup
   feature captures recent file edits as `{path, ts, data}` records.
   For me this gave **34 files with their full April 28–29 content**,
   including every web clipping I'd done in the last week.

2. **`<vaultId>-cache` / `metadata` store**: Per-file frontmatter,
   headings, list-item structure for **1,156 files**. No body text,
   but enough scaffolding to recognize what every file was about.

Joining the cache `file` store (path → hash) with the cache
`metadata` store (hash → parsed structure) produced a complete
inventory: 1,575 files, with mtime, size, hash, and structural
outline.

This is what `extract_obsidian_indexeddb.py` does.

The IndexedDB extraction by itself accounts for most of what I now
think of as "the recoverable layer Apple doesn't tell you about."

### Claude Code conversation logs

I'd been collaborating with Claude Code on the vault, particularly
on the new `🧠 06-Wiki/` folder. Every Write/Edit tool call that
Claude makes is preserved in JSONL session logs at
`~/.claude/projects/.../*.jsonl`.

I scanned every log for tool calls targeting paths containing
"Obsidian." This produced **23 files with full content**: the entire
Wiki structure (entities, concepts, sources), 8 MOC files I'd asked
Claude to draft, two notes from a Harvard AI Native lecture series.

This is what `extract_claude_logs.py` does.

If you collaborate with an AI agent on your vault, **its session
logs are an underrated recovery source.**

### Chrome history and the Web Clipper extension

When notes are gone, what you were *researching* is often nearly as
useful as the notes themselves. Chrome's history database
(`~/Library/Application Support/Google/Chrome/Default/History`) is a
SQLite file you can query directly.

A 3-month window produced:

- **357 visits** to content sites I clip from regularly (Substack,
  Every, LinkedIn Pulse, PromptKit, Coursera).
- **1,215 YouTube videos** watched — most linked to or referenced
  in lost notes.
- **348 ChatGPT / Claude / NotebookLM conversation URLs**. The full
  content of every one of those conversations still lives on the
  providers' servers. Visiting each URL gives me back the source
  material for the corresponding lost note, often verbatim.

Separately, the Obsidian Web Clipper Chrome extension stores recent
clip history (URL + title + target path + datetime) in its
LevelDB-backed extension storage. This gave me the *exact* four web
clippings I'd done on April 28–29: titles, URLs, target paths,
timestamps. Three of them I'd already recovered from IndexedDB; the
fourth I could re-clip.

This is what `extract_chrome_history.py` and `extract_web_clipper.py`
do.

## The merge

I ended up with three layers:

1. **Time Machine** (Feb 9): full bodies for 1,092 files, but stale.
2. **IndexedDB recovery**: full bodies for 34 April files plus
   skeletons (frontmatter + headings) for 1,156 more.
3. **Claude Code logs**: full bodies for 23 files concentrated in
   the Wiki and MOCs.

Merge order, from base outward:

1. Time Machine restore is the base.
2. IndexedDB full-content recoveries overlay (newer mtimes win).
3. Claude Code recoveries fill in remaining gaps without overriding.
4. Skeletons and references stay outside the vault as scaffolding.

Final state:

- **1,148 markdown files** in the vault — about 99% of structure
  recovered.
- Full content for everything as of Feb 9, plus every late-April
  edit Obsidian had cached, plus every file Claude had worked on.
- A reference bundle outside the vault containing 1,156 skeleton
  outlines and 4.4 MB of Chrome history (357 content-site visits,
  348 AI chat URLs, 1,215 YouTube videos) for re-creating any
  February–April note that didn't survive otherwise.
- The vault moved out of `~/Documents/` and into `~/Obsidian/`,
  where iCloud "Desktop & Documents Folders" can no longer reach
  it.

## What this incident cost vs. what it was worth

Time: about 7 hours, including dead ends.
Files irrecoverably lost: dozens of notes whose only edits between
Feb 9 and April 22 were direct edits I made in Obsidian, never
touched by Claude, never web-clipped, and never in the auto-backup
window.
Lessons: more than I'd have gotten from a year of writing.

Most of the work that *survived* did so for reasons I hadn't
deliberately set up:

- Obsidian's auto-backup happened to include my final week.
- I happened to be using Claude Code for the most ambitious recent
  project (the Wiki).
- I happened to have done my research through a Chrome profile that
  retained history.

If any one of those had been different, the recovery rate would
have dropped significantly. **The lesson isn't "be smart about
recovery." The lesson is "have your authoritative data in a place
where recovery isn't this fragile."**

See [`docs/04-prevention.md`](docs/04-prevention.md) for the rules
I wish past me had followed.

## What I'd want from Apple, and don't expect to get

A "preserve a local copy of everything in `~/Documents/` before
applying any iCloud-originated deletion" toggle would prevent this
loss pattern entirely, at the cost of some disk space. It would be
a five-line product change. It will not happen. See
[`docs/05-why-icloud-fails.md`](docs/05-why-icloud-fails.md).

## What I'd want from Obsidian, and might actually get

The auto-backup feature is currently scoped narrowly enough that
most files don't get full-content snapshots. A more aggressive
default — say, "the last edited body of every file, kept for 30
days" — would have made the IndexedDB recovery layer dramatically
richer in this case. Worth a feature request.

## And, finally

If you're reading this in panic right now: start with
[`docs/01-diagnosis.md`](docs/01-diagnosis.md), don't reinstall
anything, and accept that you'll probably get back more than you
think.
