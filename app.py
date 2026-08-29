"""
app.py
Main Streamlit app: a chat window (primary feature), a Google-Calendar-style
weekly view, and a Kanban board — all styled with rounded corners and a
cleaner, more modern look.

Run with: streamlit run app.py
"""

from datetime import date

import streamlit as st
from streamlit_calendar import calendar
from streamlit_sortables import sort_items

import database as db
from ai_chat import chat_with_ai

st.set_page_config(page_title="AI Timetable Planner", layout="wide")
db.init_db()

# ---------------- Custom styling (rounded corners, modern look) ----------------
st.markdown("""
<style>
    /* Overall page */
    .stApp { background-color: #f7f8fa; }

    /* Headings */
    h1, h2, h3 { font-family: 'Segoe UI', sans-serif; color: #202124; }

    /* Chat message bubbles */
    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 4px 10px;
        margin-bottom: 6px;
        background-color: #ffffff;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }

    /* Chat input box */
    [data-testid="stChatInput"] textarea {
        border-radius: 20px !important;
    }

    /* Buttons */
    .stButton button {
        border-radius: 10px;
        border: none;
        background-color: #4285F4;
        color: white;
        font-weight: 500;
    }
    .stButton button:hover { background-color: #3367D6; color: white; }

    /* Calendar container — round the whole card and its events */
    .fc {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(0,0,0,0.10);
        background-color: #ffffff;
        padding: 8px;
    }
    .fc-event {
        border-radius: 6px !important;
        border: none !important;
        padding: 2px 4px;
        font-size: 0.85em;
    }
    .fc-toolbar-title { font-size: 1.1em !important; }
    .fc-daygrid-day, .fc-timegrid-slot { border-radius: 4px; }

    /* Kanban columns */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px;
    }
</style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []          # Gemini Content objects
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []       # what we show on screen

st.title("AI Timetable Planner")

tab_main, tab_kanban = st.tabs(["Chat + Timetable", "Kanban board"])

# ==================== TAB 1: Chat + Calendar ====================
with tab_main:
    col_chat, col_calendar = st.columns([1, 1.4])

    # ---------------- Chat column (main feature) ----------------
    with col_chat:
        st.subheader("Chat")

        chat_box = st.container(height=480)
        with chat_box:
            for msg in st.session_state.display_messages:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])

        user_input = st.chat_input("Tell me about your classes, or ask to change one...")

        if user_input:
            st.session_state.display_messages.append({"role": "user", "content": user_input})

            reply, updated_history = chat_with_ai(user_input, st.session_state.chat_history)
            st.session_state.chat_history = updated_history
            st.session_state.display_messages.append({"role": "assistant", "content": reply})

            st.rerun()

    # ---------------- Calendar column (Google Calendar style) ----------------
    with col_calendar:
        st.subheader("Your timetable")

        events = db.get_all_events()
        calendar_events = [
            {
                "title": e["title"],
                "start": f"{e['event_date']}T{e['start_time']}:00",
                "end": f"{e['event_date']}T{e['end_time']}:00",
                "color": e["color"],
            }
            for e in events
        ]

        calendar_options = {
            "initialView": "timeGridWeek",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "timeGridDay,timeGridWeek,dayGridMonth",
            },
            "slotMinTime": "07:00:00",
            "slotMaxTime": "20:00:00",
            "height": 550,
        }

        calendar(events=calendar_events, options=calendar_options, key="main_calendar")

        with st.expander("All events (raw list, useful for debugging)"):
            st.table(events)

# ==================== TAB 2: Kanban board ====================
with tab_kanban:
    st.subheader("Assignments board")
    st.caption("Drag cards between columns to update progress. "
               "'Not started' = 0%, 'In progress' = 50%, 'Done' = 100%.")

    assignments = db.find_assignments(include_completed=True)

    def _label(a):
        subj = f" ({a['subject']})" if a['subject'] else ""
        due = f" — due {a['due_date']}" if a['due_date'] else ""
        return f"{a['title']}{subj}{due}"

    not_started = [_label(a) for a in assignments if a["progress"] == 0]
    in_progress = [_label(a) for a in assignments if 0 < a["progress"] < 100]
    done = [_label(a) for a in assignments if a["progress"] == 100]

    label_to_id = {_label(a): a["id"] for a in assignments}

    board = [
        {"header": "Not started", "items": not_started},
        {"header": "In progress", "items": in_progress},
        {"header": "Done", "items": done},
    ]

    new_board = sort_items(board, multi_containers=True, key="kanban_board")

    # Detect moves and write progress back to the database
    column_progress = {"Not started": 0, "In progress": 50, "Done": 100}
    if new_board:
        for column in new_board:
            for item_label in column["items"]:
                assignment_id = label_to_id.get(item_label)
                if assignment_id is None:
                    continue
                new_progress = column_progress[column["header"]]
                current = next((a for a in assignments if a["id"] == assignment_id), None)
                if current and current["progress"] != new_progress:
                    db.update_assignment_progress(assignment_id, new_progress)

    with st.expander("Add a new task manually"):
        with st.form("add_task_form", clear_on_submit=True):
            new_title = st.text_input("Task title")
            new_subject = st.text_input("Subject (optional)")
            new_due = st.date_input("Due date (optional)", value=None)
            submitted = st.form_submit_button("Add task")
            if submitted and new_title:
                due_str = new_due.strftime("%Y-%m-%d") if new_due else ""
                db.add_assignment(new_title, new_subject, due_str)
                st.rerun()