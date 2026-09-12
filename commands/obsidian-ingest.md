---
description: Ingest a source into the vault - the vault rewrites itself around new knowledge. Every ingest updates entities, rewrites stale claims, synthesizes new concepts, and resolves contradictions.
category: research
triggers_en: ["ingest this source", "add this article", "import this", "absorb this"]
triggers_es: ["haz una ingesta de esta fuente", "añade este artículo", "importa esto", "absorbe esto"]
---

Use the obsidian-second-brain skill. Execute `/obsidian-ingest $ARGUMENTS`:

The argument is a URL, file path, or pasted text. If no argument, ask what to ingest.

1. Read `_CLAUDE.md` first if it exists in the vault root

2. Classify the source type before reading the full content:
   - **Article/blog post** - extract key claims, people, tools, concepts
   - **PDF/document** - extract structure, findings, recommendations
   - **Transcript (meeting/podcast)** - extract speakers, decisions, action items, quotes
   - **YouTube video** - pull metadata, description, and transcript (see step 3 for method)
   - **Audio file** (.m4a, .mp3, .wav, .ogg, .webm) - transcribe, identify speakers, extract decisions/tasks/promises
   - **Image/screenshot** (.png, .jpg, .jpeg, .webp) - read/OCR the image, extract text and context
   - **Raw text** - classify by content (opinion, technical, narrative) and extract accordingly

3. Read or fetch the full source content:

   **For YouTube URLs** - try methods in this order (use the first one that works):

   **Method A - `yt-dlp` (best, works in Claude Code / terminal):**
   ```bash
   which yt-dlp || brew install yt-dlp
   yt-dlp --skip-download --print title --print description --print duration_string --print view_count --print like_count --print upload_date --print channel "URL"
   yt-dlp --write-auto-sub --sub-lang en --skip-download -o "/tmp/%(id)s" "URL"
   ```

   **Method B - YouTube MCP tools (works in Claude Desktop if configured):**
   Check if YouTube MCP tools are available. If so, use them.

   **Method C - oEmbed fallback (works everywhere, limited data):**
   Fetch `https://www.youtube.com/oembed?url=URL&format=json` - gives title and channel only. Ask user to paste description for full ingest.

   **For audio files** (.m4a, .mp3, .wav, .ogg, .webm):
   ```bash
   # Transcribe with Whisper (install if missing)
   which whisper || pip install openai-whisper
   whisper "path/to/audio.m4a" --model base --output_format txt --output_dir /tmp
   ```
   If `whisper` can't be installed, ask the user to paste the transcript.
   After transcription: identify speakers if possible, extract decisions, action items, promises, and who said what.
   Save the transcript to `raw/transcripts/`.

   **For images/screenshots** (.png, .jpg, .jpeg, .webp):
   Claude can read images directly. Analyze the image for:
   - Text content (OCR) - extract all readable text
   - UI screenshots - describe what's shown, extract data from tables/forms/dashboards
   - Whiteboard/diagram photos - describe the structure and extract concepts
   - Chat screenshots - extract messages, people, decisions
   Save the image description to `raw/articles/` as a markdown summary with context.

   **For articles** - use WebFetch to pull the page content
   **For PDFs** - read the file directly
   **For pasted text** - use as-is

4. Extract and organize:
   - **Entities**: people mentioned, companies, tools, projects
   - **Concepts**: key ideas, frameworks, methodologies
   - **Claims**: specific assertions with supporting evidence
   - **Action items**: anything actionable for the user
   - **Quotes**: notable quotes worth preserving

5. Save the raw source to `raw/` (immutable - never modify after saving):
   - Create `raw/articles/YYYY-MM-DD - Source Title.md` (or transcripts/, pdfs/, videos/)
   - Frontmatter: `type: source`, `date`, `tags: [source, <type>]`, `source_url`, `source_type`, `content_hash`, `ai-first: true` (the raw-source schema in `references/ai-first-rules.md`; the body stays verbatim - preamble not required)

6. **REWRITE the vault** - this is the critical step. Don't just create new pages. Rewrite existing ones.

   Read `index.md` first to understand what already exists in the vault. Then spawn parallel subagents:

   - **Entities agent**: for each person/company/tool mentioned:
     - Search the entities folder (resolved per `references/folder-map.md` - wiki-style `wiki/entities/`, Obsidian-style `People/`) for existing page
     - If found: REWRITE the page - merge new info with old, update role/context/interactions, add new links. Don't just append - integrate.
     - If not found: create new entity page with full context
   
   - **Concepts agent**: for each idea/framework/methodology:
     - Search the concepts folder (resolved per `references/folder-map.md` - wiki-style `wiki/concepts/`, Obsidian-style `Ideas/` + `Knowledge/`) for existing or related pages
     - If found: REWRITE - update the concept with new evidence, new examples, new connections. If the new source adds depth, rewrite the whole section.
     - If not found: create new concept page
     - If the ingest reveals a PATTERN across multiple existing concepts: create a new synthesis page that connects them (e.g., "Three sources now mention X - this is a trend, not a one-off")
   
   - **Projects agent**: for each project referenced:
     - Search the projects folder (resolved per `references/folder-map.md` - wiki-style `wiki/projects/`, Obsidian-style `Projects/`) for matching project
     - If found: update with new findings, add to Recent Activity, update Key Decisions if the source contains relevant decisions
   
   - **Contradictions agent**: for each claim in the new source:
     - Search the vault for CONFLICTING claims in existing pages
     - First confirm the conflicting page is about the SAME subject. Two entities that share a name, a person's namesake, or a related-but-different thing (e.g. a resident ID card vs a work-residence permit) are not a contradiction - REJECT the new claim for that page rather than absorbing it. "Related" is not "same".
     - Then decide by evidence strength, never by recency alone (the newer claim is not automatically right):
       - **Clear and directly supported** - the new source explicitly supersedes or negates the old claim, and the source text itself says so (not an inference from it): REWRITE the claim in the body to the updated version, and add a `## Contradictions and updates` section (create it if absent) with one line: old claim, new claim, source, date. Note the change in the page's history section.
       - **Ambiguous, unsettled, or only inferred** - the conflict is real but the new source does not directly settle it: do NOT overwrite the existing claim. Add the conflict to `## Contradictions and updates` only, quoting both claims with their sources and dates, and mark it `unresolved`. The body keeps the existing claim until a source settles it.
     - Never invent, stitch together, or infer information that is not explicitly present in the new source to resolve a conflict. An unresolved contradiction that is recorded is worth more than a resolved one that was guessed.

7. Update structural files:
   - REBUILD `index.md` - don't just append. Regenerate the sections that changed so descriptions stay current with the rewritten pages.
   - Append to the operation log: if `Logs/` exists write `**HH:MM** - ingest | Source Title (type) - X created, Y rewritten, Z contradictions resolved` to `Logs/YYYY-MM-DD.md`; otherwise append `## [YYYY-MM-DD] ingest | Source Title (type) - X created, Y rewritten, Z contradictions resolved` to `log.md`

8. Update today's daily note with:
   - What was ingested
   - What pages were REWRITTEN (not just created - this is the important part)
   - Any contradictions found and how they were resolved - and which were recorded as `unresolved` (these are not failures; they are the honest state)
   - Any new synthesis pages created from emerging patterns

9. Report back:
   - Source title and type
   - **New pages created** (list)
   - **Existing pages rewritten** (list with what changed)
   - **Contradictions resolved** (list with old claim vs new claim) and **contradictions recorded as unresolved** (list, with what evidence would settle each)
   - **Synthesis pages created** (patterns that emerged from this + existing knowledge)

The vault should be DIFFERENT after every ingest - not just bigger. Pages that existed before should be smarter, more connected, and more current. If an ingest only creates new pages and doesn't rewrite anything, it wasn't deep enough.

---

**AI-first rule:** Every note created or updated by this command MUST follow `references/ai-first-rules.md` - `## For future Claude` preamble, rich frontmatter (`type`, `date`, `tags`, `ai-first: true`, plus type-specific fields), recency markers per external claim, mandatory `[[wikilinks]]` for every person/project/concept referenced, sources preserved verbatim with URLs inline, and confidence levels where applicable. The vault is for future-Claude retrieval - not human reading.

**Anti-fabrication:** Search exhaustively before claiming any note, person, or file is absent - false absence is the most common failure mode - and never invent facts, entities, or dates (mark unknowns as `TBD`). See the anti-fabrication and search-completeness hard rules in `references/ai-first-rules.md`.
