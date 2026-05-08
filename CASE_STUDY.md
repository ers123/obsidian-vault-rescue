# Case study: 1,500 Obsidian notes, gone in a merge dialog

The incident that produced this repo. Vault content names are
redacted; everything else is verbatim.

A note up front: I am not a developer. I run an Obsidian vault
because I take a lot of notes, and I use AI assistants daily
for work that would otherwise need code. The recovery described
below was done over about seven hours of working through the
problem with Claude. I didn't write the scripts in this repo
from scratch — Claude did, while I described what I needed,
checked outputs, and made the judgement calls about what to try
next. If that combination is also you, this story is the most
useful version of it I can give you.

## The setup, briefly

I'd been an Obsidian user for about three years. My vault lived
at `~/Documents/Obsidian/` and I had iCloud "Desktop & Documents
Folders" sync turned on so it would also appear on my Mac mini
at home. I hadn't thought hard about what that combination
meant; the vault "just worked" across both machines.

I had a Time Machine drive plugged in occasionally. The most
recent backup turned out to be three months stale.

Between February and late April I'd done significant work in
the vault: a major folder reorganization (an explicit move from
a PARA-style layout to a Projects/Library/Incubator/Wiki
layout), a new `06-Wiki` folder modeled after Andrej Karpathy's
LLM Wiki for tracking AI coding tools, a steady accumulation of
web clippings.

## The incident

The day before, Universal Control between my MacBook Air and
Mac mini had been flaky. I'd done a couple of iCloud sign-out /
sign-in cycles trying to nudge it back into working. One of
those flows showed a "merge" dialog about iCloud Drive. I
clicked through it without reading carefully.

The next morning my `~/Documents/` was empty except for a
fresh `.localized` file. The vault folder was gone from both
Macs. iCloud Drive's "Recently Deleted" showed nothing. iCloud
Data Recovery at `icloud.com/recovery` showed nothing. Time
Machine's most recent backup was from February.

## The first hour: stop, then look

What I did right, more out of luck than discipline:

- I didn't reinstall Obsidian. (Its IndexedDB cache turned out
  to hold the most recent week of edits.)
- I didn't sign out of iCloud again.
- Once I realized my Mac mini might still have a local copy, I
  killed its sync daemons in a loop and physically disconnected
  its Wi-Fi as soon as I got home.

What I almost did wrong, and would warn anyone else against:

- I almost ran Disk Drill against my main APFS volume. I learned
  later (talking it through) that APFS plus iCloud-mediated
  deletion produces no recoverable file system blocks to scan;
  Disk Drill would have wasted hours and possibly written
  recovery data to the same volume.
- I almost emptied the Trash on the Mac mini "to free space and
  try again." Obsidian uses per-vault `.trash` folders that are
  not the system Trash, so this would have been mostly cosmetic
  — but I'd have been in the wrong frame of mind for everything
  that followed.

## The recovery, in order

### Apple's own pools — empty

iCloud Recently Deleted: empty. iCloud Data Recovery
(`icloud.com/recovery/`): empty. Time Machine: latest backup
2026-02-09. Local APFS snapshots: one from 2026-02-09 only.

This was the moment of genuine despair. Apple's documented
recovery paths all either had nothing or a three-month gap.

### Time Machine, despite the gap

I restored the February 9 baseline anyway. It gave me 1,092
markdown files with full bodies — the entire vault as it stood
three months earlier. It was missing every edit, every new note,
every folder restructure, every recent web clipping. But it was
a foundation.

I restored to a sandbox path at first. I'd later move it to
`~/Obsidian/` — see prevention notes.

### Obsidian's IndexedDB, the surprise

Obsidian's app data lives at
`~/Library/Application Support/obsidian/`. Inside `IndexedDB/`
is a Chromium LevelDB that Obsidian uses for its own state. I
didn't know any of this going in; this was Claude walking me
through what an Electron app's storage looks like and what we
might find in it.

Two things in there turned out to be invaluable:

1. The `<vaultId>-backup` / `backups` store. Obsidian's
   auto-backup feature captures recent file edits as
   `{path, ts, data}` records. For me this gave back 34 files
   with their full April 28–29 content, including every web
   clipping I'd done in the last week.

2. The `<vaultId>-cache` / `metadata` store. Per-file
   frontmatter, headings, list-item structure for 1,156 files.
   No body text, but enough scaffolding to recognize what every
   file was about.

Joining the cache `file` store (path → hash) with the cache
`metadata` store (hash → parsed structure) produced a complete
inventory: 2,711 files, with mtime, size, hash, and structural
outline.

This is what `extract_obsidian_indexeddb.py` does. The script
in this repo is the cleaned-up version of what we ended up with
after a few iterations of "try this — that fails because…  —
try this instead."

The IndexedDB extraction by itself accounts for most of what I
now think of as "the recoverable layer Apple doesn't tell you
about."

### Claude Code conversation logs

I'd been collaborating with Claude Code on the vault, particularly
on the new `06-Wiki` folder. Claude pointed out partway through
the recovery that every Write/Edit tool call it makes is preserved
in JSONL session logs at `~/.claude/projects/.../*.jsonl`. I'd
never thought about those files existing.

Scanning every log for tool calls targeting paths containing
"Obsidian" produced 23 files with full content: the entire Wiki
structure (entities, concepts, sources), 8 MOC files I'd asked
Claude to draft earlier in April, two notes from a Harvard AI
Native lecture series.

This is what `extract_claude_logs.py` does.

If you collaborate with an AI agent on your vault, its session
logs are an underrated recovery source. I would never have
guessed they existed without being told.

### Chrome history and the Web Clipper extension

When notes are gone, what you were researching is often nearly
as useful as the notes themselves. Chrome's history database
(`~/Library/Application Support/Google/Chrome/Default/History`)
is a SQLite file you can query directly.

A three-month window produced:

- 357 visits to content sites I clip from regularly (Substack,
  Every, LinkedIn Pulse, PromptKit, Coursera).
- 1,215 YouTube videos watched — most linked to or referenced
  in lost notes.
- 348 ChatGPT / Claude / NotebookLM conversation URLs. The full
  content of every one of those conversations still lives on
  the providers' servers. Re-visiting each URL gives me back
  the source material for the corresponding lost note, often
  verbatim.

Separately, the Obsidian Web Clipper Chrome extension stores
recent clip history (URL + title + target path + datetime) in
its LevelDB-backed extension storage. This gave me the exact
four web clippings I'd done on April 28–29: titles, URLs,
target paths, timestamps. Three of them I'd already recovered
from IndexedDB; the fourth I could re-clip.

This is what `extract_chrome_history.py` and
`extract_web_clipper.py` do.

## The merge

I ended up with three layers:

1. Time Machine (Feb 9): full bodies for 1,092 files, but stale.
2. IndexedDB recovery: full bodies for 34 April files plus
   skeletons (frontmatter + headings) for 1,156 more.
3. Claude Code logs: full bodies for 23 files concentrated in
   the Wiki and MOCs.

Merge order, from base outward:

1. Time Machine restore is the base.
2. IndexedDB full-content recoveries overlay (newer mtimes win).
3. Claude Code recoveries fill in remaining gaps without
   overriding.
4. Skeletons and references stay outside the vault as
   scaffolding.

Final state:

- 1,148 markdown files in the vault — about 99% of structure
  recovered.
- Full content for everything as of February 9, plus every
  late-April edit Obsidian had cached, plus every file Claude
  had worked on.
- A reference bundle outside the vault containing 1,156
  skeleton outlines and 4.4 MB of Chrome history for
  re-creating any February–April note that didn't survive
  otherwise.
- The vault moved out of `~/Documents/` and into `~/Obsidian/`,
  where iCloud "Desktop & Documents Folders" can no longer
  reach it.

## What working with an AI on this actually looked like

I want to be honest about this part because I think it's the
most reproducible thing in the whole story.

I didn't write the Python. I don't really know how to. What I
did was sit at a terminal and describe the problem, run the
commands Claude suggested, paste the output back, and decide
where to push next. When something worked, I asked Claude to
package it. When something didn't, I asked why and what we
should try instead.

The judgement calls were mine: which sources to chase first,
when to stop down a path that wasn't working, when the
recovered files were "good enough" to merge, what to keep
versus discard. Claude's contribution was the technical
literacy I don't have — knowing what an Electron app's storage
layer looks like, knowing about `ccl_chromium_reader` as a
parsing library, knowing how to safely query Chrome's locked
SQLite database, knowing the right shape of `rsync` flags for
each merge step.

That division of labor is exactly what AI assistants are good
at right now, and a lot of recovery situations have the same
shape: an emotional human, a high-stakes problem, a domain
nobody told you about, and a disposable scratch environment to
poke at it. If I can do this, you can do this.

The scripts in this repo are the residue of that work, cleaned
up and packaged so the next person who hits this incident
doesn't have to start from scratch.

## What this incident cost vs. what it was worth

Time: about seven hours, including dead ends.

Files irrecoverably lost: dozens of notes whose only edits
between February 9 and April 22 were direct edits I made in
Obsidian, never touched by Claude, never web-clipped, and
never in the auto-backup window.

Most of the work that survived did so for reasons I hadn't
deliberately set up:

- Obsidian's auto-backup happened to include my final week.
- I happened to be using Claude Code for the most ambitious
  recent project (the Wiki).
- I happened to have done my research through a Chrome profile
  that retained history.

If any one of those had been different, the recovery rate
would have dropped significantly. The lesson isn't "be smart
about recovery." The lesson is "have your authoritative data
in a place where recovery isn't this fragile."

See [`docs/04-prevention.md`](docs/04-prevention.md) for the
rules I wish past me had followed.

## What I'd want from Apple, and don't expect to get

A "preserve a local copy of everything in `~/Documents/`
before applying any iCloud-originated deletion" toggle would
prevent this loss pattern entirely, at the cost of some disk
space. It would be a small product change. It will not happen.
See [`docs/05-why-icloud-fails.md`](docs/05-why-icloud-fails.md).

## What I'd want from Obsidian, and might actually get

The auto-backup feature is currently scoped narrowly enough
that most files don't get full-content snapshots. A more
aggressive default — say, "the last edited body of every file,
kept for 30 days" — would have made the IndexedDB recovery
layer dramatically richer in this case. Worth a feature
request.

## And, finally

If you're reading this in panic right now: start with
[`docs/01-diagnosis.md`](docs/01-diagnosis.md), don't reinstall
anything, and accept that you'll probably get back more than
you think.
