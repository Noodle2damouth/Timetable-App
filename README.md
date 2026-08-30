# AI Timetable Planner — Project complete (Weeks 1-3)

## What's in this folder
- `database.py` — SQLite storage: timetable events, assignments, exams,
  student profile, syllabus chapters, and a persistent color-per-subject
  table.
- `ai_chat.py` — Gemini function-calling chat brain (model: `gemini-3.6-flash`).
  Turns natural language into real actions: add/edit/delete timetable
  events, track assignments and exams, and generate chapter mindmaps.
- `syllabus_parser.py` — splits an uploaded syllabus (PDF or pasted text)
  into individual chapters automatically, using "Chapter N" / "Unit N"
  style headings.
- `app.py` — Streamlit app: onboarding flow, one-time tutorial, timetable
  (Google-Calendar-style), Kanban board, and a floating chat bubble
  visible from every screen.
- `requirements.txt` — Python packages needed.
- `.streamlit/config.toml` — sets the blue accent color for both light
  and dark mode.
- `.gitignore` — keeps your API key and personal timetable data out of GitHub.
- `CODE_EXPLAINED.md` — a plain-English, section-by-section walkthrough of
  every file, written for the team to actually understand the code (not
  just run it).

## Setup
1. Install Python 3.10+
2. `pip install -r requirements.txt`
3. Get a free Gemini API key: https://aistudio.google.com/apikey
4. Set it as an environment variable (do this every time you open a new terminal):
   - Mac/Linux: `export GEMINI_API_KEY="your_key_here"`
   - Windows (PowerShell): `$env:GEMINI_API_KEY="your_key_here"`
5. Run the app: `streamlit run app.py`

## What works right now (confirmed by testing)
- **Onboarding flow**: first launch asks for your name and grade, then
  lets you upload a syllabus (PDF or pasted text) per subject — chapters
  are split out automatically, no manual typing.
- **One-time tutorial** screen after onboarding, never shown again.
- **Chat** (floating bubble, bottom-right, visible on every screen):
  - Add a class ("I have Math on Friday at 10am")
  - Edit a class with context awareness ("actually make it 11am")
  - Delete a class ("remove my Chemistry class on Tuesday")
  - Ask what's due, report progress ("mark English 75% done")
  - Add and check exam dates
  - Generate a mindmap for any uploaded chapter ("mindmap Chapter 3 of
    Geography") — shown as a colored branching outline card in the chat
- **Timetable**: Google-Calendar-style weekly view, DD/MM/YYYY dates,
  distinct persistent color per subject, rounded modern styling
- **Kanban board**: drag assignment cards between To Do / In Progress /
  Done, live counts, add tasks directly
- Inter font for body text, Instrument Serif for headings throughout
- Light/dark mode toggle (blue accent in both)

## What was deliberately NOT built
- **PDF upload → quiz → auto-grading** (originally planned for Week 3/4)
  was dropped as too complex for the project's scope and timeline. The
  syllabus upload + mindmap features cover the "AI understands my
  syllabus" part of the brief without needing this.

## Notes for the team
- **Model name**: Google retires Gemini models fairly often. We're on
  `gemini-3.6-flash` as of this writing — if you get a "model not found"
  error, check https://ai.google.dev/gemini-api/docs/changelog for the
  current model name and update `MODEL_NAME` in `ai_chat.py`.
- **Interactions API**: Google now recommends a newer "Interactions API"
  for new projects, but `generateContent` (what this project uses) remains
  fully supported and is Google's own recommended path for stable
  deployments. We're deliberately staying on `generateContent` — migrating
  would add real restructuring work for no benefit at our project's scale.
  Don't switch mid-project.
- **"No API key" errors are usually not a code bug** — they almost always
  mean `GEMINI_API_KEY` wasn't set in that terminal session before running
  the app. Set it again and restart the terminal if this happens.
- **Kanban dark mode** follows your operating system's dark mode setting,
  not Streamlit's own toggle — the Kanban board renders in an isolated
  iframe that can't see Streamlit's theme state, which is a real
  limitation of the library, not a bug we can fully close.
- **New to the codebase?** Read `CODE_EXPLAINED.md` first — it walks
  through every file in plain language.
- **Security**: never paste your real `GEMINI_API_KEY` into a chat, commit,
  or group message. Keep it only in your local environment variable or an
  untracked `.env` file (see `.gitignore`). If a key is ever exposed,
  regenerate it immediately at https://aistudio.google.com/apikey