# 03 — Reverse-engineering Obsidian's IndexedDB cache

This document explains *what* `scripts/extract_obsidian_indexeddb.py`
is doing under the hood — useful if you want to adapt it to a
different app (Logseq, Notion, Anytype, Reflect, …) or extract data
the script doesn't yet surface.

## What Obsidian stores and where

Obsidian is an Electron app, which means its persistent state is
written through Chromium's storage stack — IndexedDB, on top of
LevelDB, on top of plain files.

Path on macOS:

```
~/Library/Application Support/obsidian/
├── IndexedDB/
│   ├── app_obsidian.md_0.indexeddb.leveldb/   ← key/value store
│   └── app_obsidian.md_0.indexeddb.blob/       ← attachment blobs
└── obsidian.json                               ← vault registry
```

There are typically *ten* IndexedDB databases inside that one
LevelDB store, one per Obsidian feature or plugin:

| DB name | What it stores |
|---------|----------------|
| `<vaultId>-cache` / `file` | Every file in the vault: path → `{mtime, size, hash}` |
| `<vaultId>-cache` / `metadata` | Every parsed `.md`: hash → `{frontmatter, headings, sections, listItems, frontmatterLinks, ...}` |
| `<vaultId>-backup` / `backups` | **Auto-backup snapshots: `{path, ts, data}`** ← full body content lives here |
| `dataview/cache/<vaultId>` | Dataview plugin's parsed view |
| `omnisearch/cache/<vaultId>` | Omnisearch index + embed graph |
| `Excalidraw <vaultId>` | Excalidraw plugin state |
| `<vaultId>-webview` | Webview plugin |
| Others (older vault IDs) | Snapshots from previous incarnations of the vault |

The crucial one is **`<vaultId>-backup` / `backups`**. Each record
has `{path, ts, data}` where `data` is the literal `.md` file content.
This is Obsidian's own auto-backup feature — invaluable when the file
on disk is gone.

## How to read it

LevelDB on its own is a binary key/value store. Chromium layers on
its IndexedDB key encoding (database id + object store id + actual
key prefix) and Blink's value serialization (a v8/structured-clone
format, optionally with Snappy compression and external blob refs).

You can't `strings(1)` your way to clean records — the encoding
intermixes header bytes with payload, and large values are serialized
across multiple LevelDB rows.

The cleanest off-the-shelf parser is **`ccl_chromium_reader`**
([cclgroupltd/ccl_chromium_reader](https://github.com/cclgroupltd/ccl_chromium_reader))
— a Python library by CCL Forensics that handles both layers.

Minimal usage:

```python
from ccl_chromium_reader import ccl_chromium_indexeddb

leveldb = "/.../app_obsidian.md_0.indexeddb.leveldb"
blob    = "/.../app_obsidian.md_0.indexeddb.blob"
db = ccl_chromium_indexeddb.WrappedIndexDB(leveldb, blob)

for db_id in db.database_ids:
    database = db[db_id]
    for store_name in database.object_store_names:
        store = database[store_name]
        for record in store.iterate_records(
            bad_deserializer_data_handler=lambda k, v: None
        ):
            print(record.key, record.value)
```

Pass `bad_deserializer_data_handler` so a single un-parseable record
doesn't abort the whole scan. (Without it, one bad record raises and
the iterator yields nothing.)

## Joining files to metadata

The `file` store keys by path, the `metadata` store keys by content
hash. To produce a per-path metadata view, join on the hash:

```python
path_to_file = {}        # path -> {mtime, size, hash}
hash_to_meta = {}        # hash -> {frontmatter, headings, ...}

for db_id in db.database_ids:
    database = db[db_id]
    if not database.name.endswith("-cache"):
        continue
    for r in database["file"].iterate_records(bad_deserializer_data_handler=...):
        path_to_file[str(r.key)] = r.value
    for r in database["metadata"].iterate_records(bad_deserializer_data_handler=...):
        hash_to_meta[str(r.key)] = r.value

for path, info in path_to_file.items():
    meta = hash_to_meta.get(info["hash"])
    if meta:
        print(path, meta["frontmatter"], [h["heading"] for h in meta["headings"]])
```

That's all `extract_obsidian_indexeddb.py --skeletons` is doing.

## What's not in IndexedDB

- **Body text of arbitrary `.md` files.** Only files captured by the
  auto-backup feature have full content. Most files don't.
- **Attachment binary content.** Lives in the `.blob` directory. Some
  tooling exposes those — this repo doesn't yet.
- **Plugin state for plugins that store on disk** (e.g. Smart Composer
  uses its own SQLite). For those, look in the plugin's directory under
  `.obsidian/plugins/<plugin-name>/`.

## Adapting this to other apps

The same approach works for any Electron-based markdown editor:

| App | Path |
|-----|------|
| Logseq | `~/Library/Application Support/Logseq/IndexedDB/` |
| Notion (desktop) | `~/Library/Application Support/Notion/IndexedDB/` |
| Anytype | `~/Library/Application Support/anytype/IndexedDB/` |
| Reflect | `~/Library/Application Support/Reflect/IndexedDB/` |

The structure differs per app, but the parsing approach
(`ccl_chromium_reader` + per-store dump) is identical. PRs welcome.
