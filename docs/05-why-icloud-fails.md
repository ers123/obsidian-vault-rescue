# 05 — Why iCloud's Documents sync fails this way (and why Apple won't fix it)

This isn't a bug report. It's an attempt to explain why a particular
loss pattern — vault disappears, no Trash, no warning, multiple
devices "agree" the files are gone — is *expected behavior* under
iCloud's design, and why expecting Apple to change it is unrealistic.

## The architectural choice

iCloud Drive is built on the assumption that **the cloud is the
source of truth** and the local Mac is a cache. Most of Apple's
storage product strategy since "Optimize Mac Storage" landed has
reinforced this:

- "Optimize Mac Storage" replaces local files with placeholders,
  re-downloading on access.
- "Desktop & Documents Folders" promotes those two specific local
  directories to be cloud-primary as well.
- Continuity / Universal Clipboard / Handoff all assume a single
  logical user state across devices, with the cloud arbitrating.

Once you accept "cloud is authoritative," **last write wins** becomes
the natural conflict-resolution rule. A delete is just another write.
If iCloud believes the latest authoritative state of a file is
"deleted," it will propagate that to every cache (every Mac, every
iPad). The fact that one of those caches recently held a different
version is — by design — irrelevant.

## Why this is incompatible with how people actually use it

People use `~/Documents/` for things they consider their own:
manuscripts, vaults, databases, project work. They don't think of
Documents as a *cache*. They think of it as **the place their stuff
is**.

When Apple's storage layer treats it as a cache, two mental models
collide:

- User: "iCloud is my backup."
- Apple: "iCloud is your primary; the local Mac is the backup."

The two are operationally opposite. A "delete from this device"
flow makes sense in Apple's model (we're just evicting the cache;
the truth still lives upstream). It is catastrophic in the user's
model (the only copy of the truth just got erased).

## Why Apple won't fix it

Three reasons, in increasing depth:

1. **It's not a bug.** Every individual behavior — sign-out merge,
   delete propagation, last-write-wins — does what its design says
   it does. No internal "this is broken" exists for Apple to fix.
   The problem is at the *interface between* features, not within
   any one of them.

2. **The fix would be expensive and visible.** Making the local copy
   authoritative again would require either (a) abandoning "Optimize
   Mac Storage," which Apple has promoted as a flagship space-saver,
   or (b) building a far more sophisticated reconciliation system
   that treats user-content directories differently from app data.
   Both would mean admitting the current design has a category of
   user it can't serve.

3. **The blast radius is small.** Most iCloud users keep a few photos
   and Word documents in Documents. They don't notice when a sync
   incident loses a 50KB markdown note among 12,000 files. The users
   most affected are power users with structured local-first
   workflows — Obsidian, Logseq, code projects — and those users are
   already moving to mechanisms that don't rely on iCloud Drive
   (Obsidian Sync, Git, Syncthing). Apple's incentive to invest in
   improving iCloud Drive for them is shrinking, not growing.

## What this means for you

- **Don't argue with the design.** Stop putting your authoritative
  data inside iCloud Documents. Apple isn't going to redesign iCloud
  Drive to make that safe.
- **Treat Apple's tooling as one component, not the system.**
  Time Machine is excellent. iCloud Recently Deleted is fine. iCloud
  Data Recovery is a useful second pool. None of them are the answer
  on their own.
- **The app layer is where recovery lives.** When the file system
  has lost data, the apps that *worked with* the file system —
  Obsidian, Chrome, Claude Code — often haven't yet. That's the
  whole premise of this repo.

## A note on tone

Apple's documentation and support flows do not acknowledge this
pattern of loss. Forum posts asking about it usually get redirected
to "do you have a Time Machine backup?" If you've gone through it,
that response feels gaslighting. It's not — it's the only answer
Apple's design lets a support agent give. The data is gone from
Apple's perspective, because Apple's perspective only sees what's
in the cloud right now.

The recovery work in this repo is not Apple-blessed. It is
post-incident forensics on application caches that happen to outlive
the file system event Apple considers final. Use it accordingly.
