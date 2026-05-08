# 01 — Diagnosis: stop, then look

> If you just lost your vault, the first hour matters more than every
> hour after it. Most of what destroys recoverability happens in
> panic, not in the original incident.

## Stop these immediately

- **Don't reinstall Obsidian.** The Obsidian app's IndexedDB cache holds
  a partial mirror of your vault — recent edits, frontmatter, headings.
  Reinstalling wipes it. This is your single biggest at-risk asset.
- **Don't sign out of iCloud.** You're already in a sync incident.
  Another sign-out can trigger another merge dialog and propagate the
  deletion to your remaining devices.
- **Don't empty the Trash** anywhere. Some apps put deleted files in
  per-vault `.trash` folders rather than the system Trash; they survive
  longer than you expect.
- **Don't run disk-recovery tools yet.** Tools that scan free space
  (Disk Drill, EaseUS, Stellar) can write recovery data back to the
  same disk and overwrite recoverable blocks. Read this whole document
  first.

## Disconnect any second device with the same Apple ID

If you have a Mac mini, MacBook, or iPad signed into the same Apple ID,
and the vault was on iCloud-synced storage, that second device may
still have a local copy that iCloud is *currently propagating the
deletion to*.

**Cut its network access first, ask questions second:**

- Mac: System Settings → Wi-Fi → toggle off. Or pull the Ethernet
  cable. (If you're SSH'd in remotely, killing Wi-Fi over SSH cuts you
  off — better to physically pull the cable or have someone toggle it.)
- iPad / iPhone: Airplane mode.

The instant a sync daemon (`bird`, `cloudd`, `fileproviderd`) on that
device next reaches iCloud, it may receive the "delete" instruction
and apply it to your local copy. Buy yourself time.

If you can SSH into the device and don't want to lose access, you can
keep `bird` and friends dead in a loop until you're ready:

```bash
nohup bash -c 'while true; do
  killall bird cloudd fileproviderd 2>/dev/null
  sleep 3
done' >/dev/null 2>&1 &
disown
```

This is a hack. It buys hours, not days. Use it to get to the device
in person, then disable the network properly.

## Now check, in this order

### 1. iCloud "Recently Deleted"

Open **iCloud Drive** → sidebar → **Recently Deleted**. iCloud keeps
deleted files for 30 days here.

If your incident was a normal iCloud delete, the files will be here.
If they aren't, your incident bypassed Trash — usually a sign-out
merge or a "delete from this device" flow.

### 2. iCloud Data Recovery (separate from Recently Deleted)

Apple runs a *second*, less advertised recovery layer at
**https://www.icloud.com/recovery/**. Sign in with your Apple ID. If
the **"Restore Files"** card shows a count > 0, click it.

This is sometimes empty when "Recently Deleted" is also empty, and
sometimes has files when "Recently Deleted" doesn't. Both worth
checking.

### 3. Time Machine

If your last Time Machine drive plugged into this Mac is reachable,
this is by far the best baseline. Plug it in, then:

```bash
tmutil destinationinfo        # list configured destinations
tmutil listbackups            # all available backups (needs Full Disk Access)
tmutil listlocalsnapshots /   # APFS local snapshots (24-48h, occasional)
```

Don't restore yet. Just verify a backup exists and note the most
recent timestamp. You'll want to restore *after* you've gathered the
volatile sources below, so you can merge cleanly.

### 4. The Obsidian app's cache

This is the source the rest of this repo is built around. While
Obsidian is closed, copy the entire app data directory somewhere safe:

```bash
cp -R ~/Library/Application\ Support/obsidian \
      ~/obsidian-app-snapshot-$(date +%Y%m%d-%H%M)
```

Now no matter what you do next, the cache state at this moment is
preserved. The scripts in this repo never write to the original; this
extra copy is paranoia insurance.

### 5. Browser caches and history

Same idea: while Chrome is open or closed, copy the relevant
directories before doing anything else:

```bash
cp ~/Library/Application\ Support/Google/Chrome/Default/History \
   ~/chrome-history-$(date +%Y%m%d-%H%M).db
cp -R ~/Library/Application\ Support/Google/Chrome/Default/Local\ Extension\ Settings \
      ~/chrome-extensions-$(date +%Y%m%d-%H%M)
```

### 6. Claude Code session logs

If you used Claude Code in or near your vault, every Write/Edit tool
call is preserved in JSONL session logs:

```bash
cp -R ~/.claude/projects \
      ~/claude-projects-$(date +%Y%m%d-%H%M)
```

These can hold full file contents the agent wrote on your behalf.

## Now you can run the scripts

Once those snapshots exist, you have nothing to lose. Run:

```bash
python scripts/recover.py --output ~/vault-recovered
```

Then move on to [`02-recovery-paths.md`](02-recovery-paths.md) to
decide which sources to merge in what order.
