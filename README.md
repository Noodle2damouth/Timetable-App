# AI Timetable Planner — Weeks 1-2 (confirmed working)

## What's in this folder
- `database.py` — SQLite storage: timetable events, assignments, exams, and
  a persistent color-per-subject table. Tested and working.
- `ai_chat.py` — Gemini function-calling chat brain (model: `gemini-3.6-flash`).
  Turns messages like "I have English on Wednesday at 12:30" into real
  database actions. Handles multi-step requests (e.g. "delete my Chemistry
  class" — it looks the class up, then deletes it).
- `app.py` — Streamlit app: chat window, Google-Calendar-style weekly view,
  and a Kanban board, with rounded corners and modern styling.
- `requirements.txt` — Python packages needed.
- `.gitignore` — keeps your API key and personal timetable data out of GitHub.

## Setup
1. Install Python 3.10+
2. `pip install -r requirements.txt`
3. Get a free Gemini API key: https://aistudio.google.com/apikey
4. Set it as an environment variable (do this every time you open a new terminal):
   - Mac/Linux: `export GEMINI_API_KEY="your_key_here"`
   - Windows (PowerShell): `$env:GEMINI_API_KEY="your_key_here"`
5. Run the app: `streamlit run app.py`

## What works right now (confirmed by testing)
- Add a class via chat ("I have Math on Friday at 10am")
- Edit a class via chat, with context awareness ("actually make it 11am")
- Delete a class via chat ("remove my Chemistry class on Tuesday")
- View everything on a Google Calendar-style weekly grid, with rounded
  corners and a distinct, consistent color per subject
- Ask what's due, and the AI lists unfinished assignments
- Report progress on an assignment ("mark English 75% done") — AI updates
  it and nudges toward the next task
- Add and track exams, ask "when are my exams" for the soonest ones first
- Kanban board tab: drag assignment cards between Not started / In
  progress / Done, which updates their progress in the database

## What's next (Week 3)
- Onboarding form (grade + syllabus)
- Mindmap generation for a syllabus chapter
- PDF upload → quiz → auto-grading
- See `PROJECT_BRIEF_FOR_CLAUDE.md` for the full roadmap and how to hand this
  off to a teammate or another Claude session.

## Notes for the team
- **Model name**: Google retires Gemini models fairly often. We're on
  `gemini-3.6-flash` as of this writing — if you get a "model not found"
  error, check https://ai.google.dev/gemini-api/docs/changelog for the
  current model name and update `MODEL_NAME` in `ai_chat.py`.
- **Interactions API**: Google now recommends a newer "Interactions API"
  for new projects, but `generateContent` (what this project uses) remains
  fully supported and is Google's own recommended path for stable
  deployments. We're deliberately staying on `generateContent` — migrating
  would mean restructuring the whole request/response format for no real
  benefit at our scale. Don't switch mid-project.
- **"No API key" errors are usually not a code bug** — they almost always
  mean `GEMINI_API_KEY` wasn't set in that terminal session before running
  the app. Set it again and restart the terminal if this happens.
- **Security**: never paste your real `GEMINI_API_KEY` into a chat, commit,
  or group message. Keep it only in your local environment variable or an
  untracked `.env` file (see `.gitignore`). If a key is ever exposed,
  regenerate it immediately at https://aistudio.google.com/apikey
