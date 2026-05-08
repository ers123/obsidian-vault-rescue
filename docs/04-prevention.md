# 04 — Prevention: how to never need this guide

> If you remember nothing else: **don't put your Obsidian vault inside
> `~/Documents/` or `~/Desktop/` if you've ever turned on iCloud's
> "Desktop & Documents Folders" option.** That single rule prevents
> the loss pattern this whole repo exists for.

## The actual mechanism, briefly

When iCloud "Desktop & Documents Folders" sync is on:

- Your local `~/Documents/` is replaced by a *firmlink* to
  `~/Library/Mobile Documents/com~apple~CloudDocs/Documents/`.
- Anything in `~/Documents/` is, from the OS's perspective, **in
  iCloud Drive**, not on your Mac.
- iCloud Drive's consistency model is "last write wins" across
  devices. Sign-out / merge / "delete from this device" flows can
  silently propagate as deletions.
- The deletion does **not** go through Trash. It bypasses
  `~/.Trash/`, bypasses iCloud's "Recently Deleted" in some flows,
  and lands directly as gone.

This isn't a bug. It's a consequence of treating iCloud as authoritative
storage with the local copy as a cache.

## The rules

### 1. Vault location

```
OK:    ~/Obsidian/
OK:    ~/Notes/
OK:    /Volumes/MyExternalSSD/Obsidian/   (if you treat it as primary)

AVOID: ~/Documents/Obsidian/   (if iCloud Documents sync is on)
AVOID: ~/Desktop/Obsidian/
AVOID: ~/Library/Mobile Documents/com~apple~CloudDocs/Obsidian/  (this IS iCloud Drive)
```

### 2. Multi-device sync — choose one, not iCloud

If you use Obsidian on more than one device, pick a sync mechanism
designed for it:

- **Obsidian Sync** ($4–$8/mo). End-to-end encrypted, version
  history (1 year on the higher tier). Knows about Obsidian's
  workspace files, plugin state, etc. The boring correct answer.
- **Git** to a private repo (GitHub / Codeberg / your own).
  Free, full version history, works for plain `.md` notes very well.
  Plugins like *Obsidian Git* automate it. Best if you're already
  comfortable with Git.
- **Syncthing**. Peer-to-peer, no cloud. Good if you have always-on
  devices on the same network.
- **iCloud's *dedicated* Obsidian container**
  (`~/Library/Mobile Documents/iCloud~md~obsidian/`). This is *not*
  the same as iCloud Documents. Obsidian creates this container
  when you enable iCloud sync from inside Obsidian's mobile app. It's
  isolated from the Documents-folder sync incident pattern.

The one combination that bites people is **vault inside `~/Documents/`
with Documents iCloud sync enabled**. That's what we're avoiding.

### 3. Backups that actually exist

The single most useful intervention you can make today:

- **Plug in an external drive and run Time Machine.** Not "I have a
  drive in the drawer." Plugged in, currently doing backups. If the
  drive lives in a drawer, your backup horizon is the date you last
  remembered to plug it in.
- **Configure local APFS snapshots.** macOS will keep 24 hours of
  snapshots automatically when Time Machine is configured, even
  without the drive attached. Verify with `tmutil listlocalsnapshots /`.
- **A second offsite copy** — Backblaze, Arq, rsync to a server.
  This protects against the case where your Mac and your Time
  Machine drive are both lost together (theft, fire, flood).

### 4. Trust no single sync

If your vault matters to you, it should live in *at least two*
places that aren't the same sync system. Examples:

- Obsidian Sync + Time Machine
- Git remote + Time Machine
- Local primary + Backblaze + Git (overkill for most, right for some)

## Quick checklist

Run through this once, today:

- [ ] My Obsidian vault is **outside** `~/Documents/` and `~/Desktop/`.
- [ ] If I have multiple devices, I'm using Obsidian Sync **or** Git
      **or** the dedicated Obsidian iCloud container — **not**
      iCloud Documents sync to share the vault.
- [ ] My Time Machine drive is plugged in right now (or I have an
      always-on equivalent like Backblaze).
- [ ] `tmutil listbackups` shows a backup from within the last week.
- [ ] I know what the iCloud "merge" dialog looks like and I will
      read it slowly the next time it appears, especially during
      sign-out.

## A word on the merge dialog

The dialog that triggers the sign-out incident pattern usually looks
like:

> Do you want to keep a copy of your iCloud Drive files on this Mac?

The choices are roughly:

- **Keep a Copy** — iCloud Drive contents are downloaded to a local
  `iCloud Drive (Archive)` folder before sign-out.
- **Delete from this Mac** — local iCloud Drive contents are removed
  immediately, on the assumption that they remain in the cloud.

If iCloud is in a partially-synced state (incomplete uploads,
"Optimize Mac Storage" placeholders, mid-merge from another device),
"Delete from this Mac" can result in deletions that no other device
sees a copy of.

**Read the dialog. Take a screenshot. Don't click through it
casually.**
