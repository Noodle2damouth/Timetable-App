# Project brief: AI Timetable Planner (paste this to Claude to continue the project)

Copy everything below this line into a new Claude conversation, and upload
the current project files along with it.

---

I'm working on a group school assignment (10th grade level) building an AI
timetable planner in **Python only**. Please act as my coding assistant to
continue building/maintaining it. Here's the full context:

## Core concept
A chatbot (floating chat bubble, visible on every screen) that manages a
student's timetable and schoolwork through natural conversation, with
contextual awareness. A Kanban board offers a non-AI, drag-and-drop
alternative for the same assignment data.

## Tech stack (please stick to this)
- **Python 3.10+**
- **Streamlit** for the GUI
- **Google Gemini API** (`google-genai` package), model `gemini-3.6-flash`,
  with **function calling**. Do NOT build custom NLU from scratch. Note:
  Google retires Gemini models periodically — check
  https://ai.google.dev/gemini-api/docs/changelog if `gemini-3.6-flash`
  stops working. We're deliberately staying on `generateContent` rather
  than Google's newer "Interactions API" — both are supported, but
  migrating adds real work for no benefit at this project's scale.
- **SQLite** (`sqlite3`, built into Python) for all data storage
- **streamlit-calendar** for the Google-Calendar-style timetable view
- **streamlit-sortables** for the Kanban board
- **pdfplumber** for reading uploaded syllabus PDFs (syllabus upload only
  — see "deliberately not built" below)

## The behaviors this app actually supports (final scope)
1. **Add/edit/delete timetable events via chat**, with contextual awareness.
2. **Assignment tracking**: what's due, progress updates with nudges
   toward the next task.
3. **Exam dates + AI-generated mindmaps**: exam lookup, and mindmap
   generation for any uploaded syllabus chapter, rendered as a colored
   branching outline card (not a Graphviz node-diagram — that needs a
   system-level Graphviz install, which we deliberately avoided).
4. **Kanban board** (non-AI): drag-and-drop task management, with live
   counts and a manual add-task form.

## Deliberately NOT built
- **PDF upload → quiz → auto-grading** was scoped out entirely — it was
  judged too complex for the project's timeline relative to its value.
  Don't add this back in without discussing scope first.

## Current status: COMPLETE and confirmed working end-to-end
All of the following has been built, tested, and confirmed working:

- `database.py` — timetable, assignments, exams, student profile, and
  syllabus chapters, plus a persistent `subject_colors` table (distinct,
  consistent color per subject). Includes a lightweight in-place migration
  pattern (`_ensure_column`-style ALTER TABLE checks) so schema changes
  don't break an existing local `timetable.db`.
- `syllabus_parser.py` — splits an uploaded syllabus into chapters
  automatically via a "Chapter N" / "Unit N" heading regex, with a
  single-chapter fallback if no headings are found.
- `ai_chat.py` — Gemini function-calling loop (model `gemini-3.6-flash`,
  `MAX_STEPS`-bounded so multi-step requests like "find then delete" work
  correctly) with tools covering timetable, assignments, exams, and
  mindmap generation. `chat_with_ai` returns a 3-tuple
  `(reply_text, history, mindmap_or_None)` — the mindmap generator makes
  a SEPARATE Gemini call using structured JSON output mode
  (`response_mime_type="application/json"`) rather than parsing free text.
- `app.py` — three-screen flow (onboarding → tutorial → main app, gated by
  a `student_profile.tutorial_seen` flag), a floating chat bubble pinned
  bottom-right (via `st.container(key=...)` + CSS `position: fixed`,
  NOT full-width — a full-width version clipped under the sidebar), a
  Kanban board with STATIC column headers (dynamic/count-embedded headers
  broke drag-tracking — see "known constraints" below), and Inter/
  Instrument Serif fonts imported via Google Fonts.
- `.streamlit/config.toml` — sets `primaryColor` under `[theme.light]` AND
  `[theme.dark]` separately. Setting it under a single `[theme]` table
  removes Streamlit's light/dark toggle entirely — don't do that.

## Known constraints (learned the hard way — don't re-break these)
- **Streamlit's CSS variables are unreliable in custom `st.markdown` CSS.**
  Even with the correct `--st-` prefix, backgrounds kept resolving to
  transparent in practice. All custom-styled backgrounds now use hardcoded
  hex colors with a `@media (prefers-color-scheme: dark)` override instead
  of `var(--st-*)`. If you add new custom-styled elements, follow this
  pattern, not the CSS-variable one.
- **The Kanban board renders in an isolated iframe** (that's how
  `streamlit-sortables` works). It cannot see Streamlit's theme variables
  OR the parent page's fonts/CSS at all — it needs its own `@import` for
  fonts and its own hardcoded color + dark-mode-media-query styling,
  passed via the component's `custom_style` parameter. It also can't sync
  to Streamlit's manual light/dark toggle — only to the OS-level
  `prefers-color-scheme`, which is a real limitation of the library.
- **Kanban headers must stay static text** ("TO DO", not "TO DO (2)").
  The component only returns whatever header text it was last given: if
  the header changes between reruns (e.g. because a count changed), the
  returned drag result may not match any known column and the update gets
  silently dropped. Show live counts in a separate `st.markdown` line
  outside the component instead.
- **Fixed-position elements need a bounded width anchored to one side**
  (e.g. `right: 20px`), not `left: 0; width: 100%`. A full-width fixed
  panel overlaps/clips against Streamlit's sidebar.
- **The sidebar hover-to-expand feature is an unsupported hack** (in
  `render_hover_sidebar_script`) that reaches into Streamlit's internal
  DOM via `components.html` + `window.parent.document`. It depends on
  `data-testid` attributes that could change in a future Streamlit
  version — if hover-expand stops working after an update, check this
  function first before assuming something else broke.

## Conventions to follow
- Keep the timetable as the primary, most-polished feature.
- Every new AI capability = a new tool function in `ai_chat.py` (Gemini
  `FunctionDeclaration`) + a matching plain Python function in
  `database.py`. Don't blend chat logic and database logic in the same file.
- Test each new database function standalone (`python3 -c "..."` script)
  before wiring it into the AI chat loop.
- If a chat request could need more than one tool call in sequence, make
  sure `chat_with_ai`'s loop can handle multiple rounds.
- Keep it achievable for a 10th-grade skill level: clear function names,
  simple control flow, avoid clever/obscure Python.
- See `CODE_EXPLAINED.md` for a full plain-language walkthrough before
  making changes, if you're new to this codebase.

Please review the uploaded files (and `CODE_EXPLAINED.md`) first, then
help me with [describe what you need].