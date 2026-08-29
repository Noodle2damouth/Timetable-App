# Project brief: AI Timetable Planner (paste this to Claude to continue the project)

Copy everything below this line into a new Claude conversation, and upload
the current project files (database.py, ai_chat.py, app.py, requirements.txt)
along with it.

---

I'm working on a group school assignment (10th grade level) building an AI
timetable planner in **Python only**. Please act as my coding assistant to
continue building it. Here's the full context:

## Core concept
A chatbot window (the main feature) that manages a student's timetable and
schoolwork through natural conversation, with contextual awareness (it
remembers what was just discussed). A secondary Kanban board page lets
students drag and drop tasks without AI.

## Tech stack (please stick to this — it's what the rest of the team is using)
- **Python 3.10+**
- **Streamlit** for the GUI (chat window + calendar view + Kanban page)
- **Google Gemini API** (`google-genai` package), model `gemini-3.6-flash`,
  with **function calling** — this is how the chatbot turns natural
  language into real actions. Do NOT try to build custom NLU/intent
  parsing from scratch; use Gemini's tool-use feature instead, it's
  simpler and more reliable. Note: Google retires Gemini models
  periodically — if `gemini-3.6-flash` stops working, check
  https://ai.google.dev/gemini-api/docs/changelog for the current name.
  Google is also pushing a newer "Interactions API" for new projects, but
  we're deliberately staying on `generateContent` (what's used here) since
  Google still calls it fully supported and the recommended path for
  stable deployments — migrating would add real restructuring work for no
  benefit at our project's scale. Don't switch mid-project.
- **SQLite** (`sqlite3`, built into Python) for all data storage
- **pdfplumber** for reading uploaded PDF chapters (planned, Week 3)
- **streamlit-calendar** for the Google-Calendar-style timetable view
- **streamlit-sortables** for the Kanban board (built, Week 2)

## The 5 target behaviors (from the original assignment spec)
1. **Add/edit/delete timetable events via chat**, with contextual awareness:
   > User: "I have English Class on Wednesday, 12:30 PM"
   > AI: "Sure! Let me add that to your timetable!"
   > User: "Actually, change it to 1:00 PM"
   > AI: "Moved it to 1:00 PM!"
2. **Assignment tracking**: user asks what's due, AI lists it; user reports
   progress (e.g. "mark English Notebook Work 75% done"), AI acknowledges
   and nudges toward the next task.
3. **Exam dates + AI-generated mindmaps**: AI knows upcoming exam dates, and
   can generate a mindmap for a specific syllabus chapter based on the
   student's grade/syllabus (collected at onboarding).
4. **PDF upload → quiz → auto-grading**: student uploads a chapter PDF, asks
   to be quizzed, AI asks questions and scores the result (e.g. 90/100).
5. **Kanban board** (non-AI): drag-and-drop task management page.

## Current status (Weeks 1-2 of 4 — COMPLETE and confirmed working end-to-end)
Files already built, tested, AND confirmed working against a live API key:
- `database.py` — SQLite schema + CRUD for `timetable_events` (core
  feature), `assignments` (title, subject, due_date, progress 0-100), and
  `exams` (subject, exam_date, notes). Also has a `subject_colors` table
  that permanently assigns each subject a distinct, consistent color from
  a 10-color palette (no more duplicate/dull colors).
- `ai_chat.py` — Gemini function-calling loop (model `gemini-3.6-flash`)
  with 10 tools: `add_event`, `find_events`, `update_event`,
  `delete_event`, `add_assignment`, `find_assignments`, `get_due_now`,
  `update_assignment_progress`, `add_exam`, `get_upcoming_exams`. The chat
  loop runs in a `MAX_STEPS`-bounded cycle so it can chain multi-step
  requests correctly — e.g. "delete my Chemistry class" requires
  find_events THEN delete_event, and a single-round version of this used
  to silently fail with "None" replies. Fixed and confirmed working.
- `app.py` — Streamlit app with three parts: a chat column, a
  Google-Calendar-style weekly view (`streamlit_calendar`, styled with
  rounded corners via custom CSS), and a Kanban board tab
  (`streamlit_sortables`) that drags assignments between Not
  started/In progress/Done and syncs progress back to the database.
  Custom CSS throughout for a more modern look (rounded chat bubbles,
  rounded buttons, soft shadows).
- `.gitignore` — excludes `.env`, `timetable.db`, `__pycache__/` from
  version control so API keys and personal data don't get committed.
- Project is now on GitHub via GitHub Desktop (no command line used).

## What's next (Weeks 3-4 — NOT yet built)
- **Week 3**: Onboarding form (grade + syllabus text/file, stored in a new
  `students` or `syllabus` table). A `get_syllabus_topic` tool so the AI can
  find the right chapter. Mindmap generation (ask Gemini for structured
  JSON representing nodes/branches, then render it — could use Streamlit's
  `graphviz_chart` or a simple custom layout). PDF upload with `pdfplumber`,
  then a quiz flow: AI generates questions from extracted text, takes
  answers, and scores them.
- **Week 4**: Full testing pass across all 5 examples above. Error handling
  for ambiguous AI responses. Documentation last.

## Conventions to follow
- Keep the timetable as the primary, most-polished feature — it's the
  assignment's main focus.
- Every new AI capability = a new tool function in `ai_chat.py` (Gemini
  function declaration) + a matching plain Python function in `database.py`.
  Don't blend chat logic and database logic in the same file.
- Test each new database function standalone (like a quick `python3 -c`
  script) before wiring it into the AI chat loop — makes bugs much easier
  to isolate.
- If a chat request could need more than one tool call in sequence (find
  then act), make sure the calling loop in `chat_with_ai` can handle
  multiple rounds — don't assume one tool call per user message.
- Keep it achievable for a 10th-grade skill level: avoid needlessly
  clever/obscure Python, prefer clear function names and simple control flow.

Please review the uploaded files first, then help me continue with [tell
Claude which week/feature you're picking up].