---
name: My vault is gone — help me recover
about: You're in the middle of a vault loss incident and need guidance.
title: "[Recovery] "
labels: recovery-help
---

**Read first:** before opening this issue, please check
[`docs/01-diagnosis.md`](../../blob/main/docs/01-diagnosis.md) and
make the read-only snapshots it lists. The first hour matters more
than every hour after.

## What happened

A few sentences about the incident. When did you notice the loss?
What were you doing right before? Did you see a "merge" dialog,
sign out of iCloud, change a setting, or run any cleanup?

## What you've already checked

- [ ] iCloud Drive's "Recently Deleted" folder
- [ ] iCloud Data Recovery at https://www.icloud.com/recovery/
- [ ] Time Machine — most recent backup is from when?
- [ ] APFS local snapshots (`tmutil listlocalsnapshots /`)
- [ ] You have NOT reinstalled Obsidian
- [ ] You have NOT signed out of iCloud again
- [ ] If you have a second device with the same Apple ID, it is
      currently OFFLINE (Wi-Fi disabled / Airplane mode)

## Setup details

- macOS version:
- Obsidian version:
- Vault was at: `~/...`
- iCloud "Desktop & Documents Folders" sync:  on / off / not sure
- Multi-device:  yes (which?) / no
- Browser used for clipping (if any):

## What you've tried from this repo

- [ ] Ran `python scripts/recover.py --output ~/...`
- Output of the run (paste here, or attach the printed summary):

```
(paste summary here)
```

## What's still missing

A description of what didn't come back and what you'd most like to
recover. Even partial details help (folder names, dates of last
edit, content type).

---

I'm a single human running this repo and I cannot guarantee a
response time, especially in the first weeks while traffic is
unpredictable. The faster path to a partial recovery is almost
always the docs and scripts here. If you've followed them and are
still stuck, this is the right place to ask.
