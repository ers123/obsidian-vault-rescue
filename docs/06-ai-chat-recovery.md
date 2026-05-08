# 06 — Recovering content from AI chat history

> The single highest-yield recovery source nobody thinks of:
> the conversations you had with AI assistants while creating
> the lost notes.

If you used ChatGPT, Claude, NotebookLM, Gemini, or Perplexity
while writing or researching the notes that are now gone, those
conversations still exist. They live on the providers' servers,
not on your machine. **Local data loss does not affect them.**

For me, this layer ended up being more valuable than the
IndexedDB extraction, because:

- AI chats hold whole notes in finished form (paste-ready
  markdown), not fragments.
- The biggest, most painful losses are usually documents you
  worked through with an assistant — drafts, prompts, summaries,
  meta-prompts — and those are exactly what AI chats preserve.
- Re-asking is a one-liner: "re-output the markdown for the
  [topic] note we made."

## Step 1 — get your chat URL list

If you ran `scripts/extract_chrome_history.py` (or
`scripts/recover.py`, which calls it), there is already a file at
`<output>/_REFERENCES/ai_chats.tsv` listing every chat URL you
visited in the date window:

```
visited                url                             title
2026-04-29 23:38:38    https://every.to/...           What AI Is Teaching Us About Management
2026-04-28 11:48:25    https://chatgpt.com/c/69f0...  퍼스널 컬러 분석 요청
...
```

For each provider:

```bash
# All ChatGPT chats
grep 'chatgpt.com/c/' _REFERENCES/ai_chats.tsv

# All Claude chats
grep 'claude.ai/chat/' _REFERENCES/ai_chats.tsv

# NotebookLM, Gemini, Perplexity
grep -E 'notebooklm|gemini.google|perplexity' _REFERENCES/ai_chats.tsv
```

If you didn't extract Chrome history, you can also browse chats
directly:

| Provider | Where to find chat history |
|----------|---------------------------|
| ChatGPT  | https://chatgpt.com — left sidebar |
| Claude (web or Desktop app) | https://claude.ai/chats |
| NotebookLM | https://notebooklm.google.com |
| Gemini   | https://gemini.google.com — left sidebar |
| Perplexity | https://www.perplexity.ai/library |

Note for Claude Desktop users specifically: the desktop app and
the web at `claude.ai` share the same conversation store. A chat
you had in Desktop is the same record as the one you'd see in
the web sidebar. Open either way.

## Step 2 — match lost notes to chat URLs

Open `_FULL_FILE_LISTING.tsv` and find the lost notes you most
want back. For each, ask: "did I work on this with an assistant,
and roughly when?"

Quick lookups:

```bash
# Find chats from the day a particular note was last edited
grep '2026-04-29' _REFERENCES/ai_chats.tsv

# Find chats whose title contains a topic keyword from the lost note
grep -i 'karpathy\|wiki' _REFERENCES/ai_chats.tsv
```

The chat title (`Title:` column) is often the most useful
matcher — it's the title the AI generated for the conversation
based on what you asked, which usually overlaps with the note's
topic.

## Step 3 — re-extract content from the chat

Once you've opened a chat, the simplest prompts that work:

> Can you re-output the full markdown for the [note name] we
> wrote together in this conversation? Include frontmatter and
> all sections.

> What was the final version of [topic] you drafted for me?
> Output it as a single markdown block I can paste into
> Obsidian.

> Earlier in this chat I asked you to write [X]. Show me that
> output again, exactly as you wrote it.

If the assistant replies with "I don't see that in our
conversation" — scroll back manually. Some sessions have many
turns and the assistant occasionally loses track of what was
generated very early.

Tips:

- Use a fresh assistant turn rather than asking from inside the
  same continuing context — sometimes context limits cause the
  model to summarize rather than reproduce verbatim. Ask
  explicitly for verbatim re-output.
- For meta-prompts and other "system-prompt-like" content,
  paste the request inside a code block to make the boundary
  unambiguous.
- For long documents, ask for a single artifact rather than
  inline. (Claude on the web has the Artifacts feature; ChatGPT
  has Canvas. Both produce paste-ready text.)

## Step 4 — paste into the vault

Save the recovered content to the appropriate vault location.
For notes that match files in your `_FULL_FILE_LISTING.tsv`,
the path is already known — restore them under the same path so
internal `[[wikilinks]]` from other recovered notes still
resolve.

```bash
# Example: recover a note from Claude chat into the right place
mkdir -p ~/Obsidian/some/folder
pbpaste > "~/Obsidian/some/folder/Note Title.md"
```

(`pbpaste` reads from the macOS clipboard — paste from the chat
into the clipboard first, then run this.)

## What this is good for vs. not

Good for:

- Documents you co-created with an AI: drafts, summaries,
  meta-prompts, structured analyses, code snippets you saved
  as notes.
- Web Clippings whose content was reformatted in a chat before
  saving.
- Research notes where the AI synthesized your raw material
  into a structured note.

Less useful for:

- Notes you typed entirely yourself in the editor without
  showing the AI.
- Personal journal-style entries.
- Daily logs not discussed with the assistant.

For those, the IndexedDB skeleton + the user's memory + the
Chrome history of *what you were reading* is usually the path.

## Privacy note

Recovering content this way means re-loading whatever you
already shared with the provider. Nothing new is exposed; the
data was on their servers from the moment you sent it. But if
you've since deleted some chats from the provider for privacy
reasons, those are not recoverable — and the provider may have
honored the deletion in ways that bypass server backups.

## A practical example

In my own incident, the most valuable chats turned out to be:

- ChatGPT conversations where I'd drafted research summaries
  for specific Substack articles. Re-output: the full
  paste-ready markdown of each one.
- Claude conversations for the LLM Wiki source pages. The
  chat held both the raw transcript I'd fed in and the final
  structured note. Re-asking gave the structured note back
  verbatim.
- NotebookLM notebooks where I'd asked for terminology
  glossaries — those became `🧠 06-Wiki/wiki/concepts/*` notes.

Of the 1,156 file skeletons I had no body for, roughly 80% of
the ones I cared about could be reconstructed by walking 30 or
40 chat URLs and asking each chat's assistant the same kind of
prompt. The other 20% I rewrote from memory using the heading
structure as scaffolding.
