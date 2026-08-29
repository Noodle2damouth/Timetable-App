"""
app.py
Main Streamlit app. First-run flow:
  1. Onboarding screen (name, grade, bulk syllabus upload)
  2. One-time tutorial screen
  3. Main app (chat + timetable + Kanban)

Run with: streamlit run app.py
"""

import streamlit as st
from streamlit_calendar import calendar
from streamlit_sortables import sort_items
from datetime import datetime

import database as db
import syllabus_parser
from ai_chat import chat_with_ai

st.set_page_config(page_title="AI Timetable Planner", layout="wide")
db.init_db()

# ---------------- Custom styling (rounded corners, theme-aware) ----------------
st.markdown("""
<style>
    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 4px 10px;
        margin-bottom: 6px;
        background-color: var(--secondary-background-color);
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    [data-testid="stChatInput"] textarea { border-radius: 20px !important; }
    .stButton button { border-radius: 10px; }
    .fc {
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 1px 4px rgba(0,0,0,0.15);
        background-color: var(--secondary-background-color);
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
    div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; }

    /* Leave room at the bottom so content doesn't hide behind the chat bar */
    .block-container { padding-bottom: 100px !important; }

    /* Floating chat toggle button (shown when chat is closed) */
    .st-key-chat_toggle_btn button {
        position: fixed !important;
        bottom: 20px;
        right: 20px;
        width: 56px;
        height: 56px;
        border-radius: 50% !important;
        font-size: 1.3em;
        z-index: 9999;
        box-shadow: 0 2px 10px rgba(0,0,0,0.25);
    }

    /* Persistent chat panel, pinned to the bottom, visible across all tabs */
    .st-key-chat_panel {
        position: fixed !important;
        bottom: 0;
        left: 0;
        width: 100%;
        z-index: 9998;
        background-color: var(--background-color);
        box-shadow: 0 -4px 16px rgba(0,0,0,0.18);
        padding: 10px 20px 16px 20px;
        border-top-left-radius: 20px;
        border-top-right-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "display_messages" not in st.session_state:
    st.session_state.display_messages = []
if "force_onboarding" not in st.session_state:
    st.session_state.force_onboarding = False
if "just_added_subjects" not in st.session_state:
    st.session_state.just_added_subjects = []  # subjects added this onboarding session
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False


def determine_stage():
    if st.session_state.force_onboarding:
        return "onboarding"
    profile = db.get_student_profile()
    if profile is None:
        return "onboarding"
    if not profile["tutorial_seen"]:
        return "tutorial"
    return "main"


# ==================== SCREEN 1: Onboarding ====================
def render_onboarding():
    st.title("Welcome! Let's get set up")
    st.caption("This only takes a minute, and you can update it any time from the sidebar later.")

    profile = db.get_student_profile()

    with st.form("profile_form"):
        st.subheader("About you")
        name = st.text_input("Your name", value=profile["name"] if profile else "")
        grade_options = [f"{n}th Grade" for n in range(6, 13)]
        default_index = grade_options.index(profile["grade"]) if profile and profile["grade"] in grade_options else 4
        grade = st.selectbox("Your grade", options=grade_options, index=default_index)
        profile_saved = st.form_submit_button("Save")
        if profile_saved and name:
            db.save_student_profile(name, grade)
            st.rerun()

    if not profile:
        return  # need a name/grade saved before showing the syllabus section

    st.divider()
    st.subheader("Upload your syllabus")
    st.caption("Upload a PDF or paste the text for a subject's full syllabus — "
               "chapters are detected and split automatically, no manual typing needed. "
               "Add as many subjects as you like, then hit Finish.")

    with st.form("syllabus_upload_form", clear_on_submit=True):
        subject = st.text_input("Subject", placeholder="e.g. Geography")
        input_method = st.radio("How are you providing it?", ["Upload PDF", "Paste text"], horizontal=True)

        pdf_file = None
        pasted_text = ""
        if input_method == "Upload PDF":
            pdf_file = st.file_uploader("Syllabus PDF", type=["pdf"])
        else:
            pasted_text = st.text_area("Paste the full syllabus text here", height=200)

        upload_submitted = st.form_submit_button("Add this subject")

        if upload_submitted:
            if not subject:
                st.warning("Please enter a subject name.")
            else:
                full_text = ""
                if input_method == "Upload PDF" and pdf_file is not None:
                    with st.spinner("Reading PDF..."):
                        full_text = syllabus_parser.extract_text_from_pdf(pdf_file)
                elif input_method == "Paste text":
                    full_text = pasted_text

                if not full_text.strip():
                    st.warning("That came out empty — try again or paste the text instead.")
                else:
                    chapters = syllabus_parser.split_into_chapters(full_text)
                    db.add_syllabus_chapters_bulk(subject, chapters)
                    st.session_state.just_added_subjects.append((subject, len(chapters)))
                    st.success(f"Added {subject}: {len(chapters)} chapter(s) detected automatically.")

    if st.session_state.just_added_subjects:
        st.write("**Added so far this session:**")
        for subj, count in st.session_state.just_added_subjects:
            st.write(f"📘 {subj} — {count} chapter(s)")

    existing_chapters = db.get_all_syllabus_chapters()
    if existing_chapters:
        with st.expander(f"All syllabus chapters on file ({len(existing_chapters)})"):
            for chap in existing_chapters:
                st.write(f"- {chap['subject']}: {chap['chapter_name']}")

    st.divider()
    col_skip, col_finish = st.columns([1, 1])
    with col_skip:
        if st.button("Skip syllabus for now"):
            st.session_state.force_onboarding = False
            st.rerun()
    with col_finish:
        if st.button("Finish setup", type="primary"):
            st.session_state.force_onboarding = False
            st.session_state.just_added_subjects = []
            st.rerun()


# ==================== SCREEN 2: Tutorial ====================
def render_tutorial():
    st.title("Quick tour")
    st.caption("Just a couple of things to know before you dive in.")

    st.markdown("""
    ### 💬 Chat does most of the work
    Talk to the AI naturally — add classes, move them, check what's due,
    track exam dates, and more. Try things like:
    - *"I have Math on Friday at 10am"*
    - *"What's due right now?"*
    - *"When are my exams?"*

    ### 📅 Your timetable updates automatically
    Every class you add through chat shows up instantly on the
    Google-Calendar-style weekly view, color-coded by subject.

    ### 🗂️ Kanban board for visual planning
    Prefer dragging cards over typing? The Kanban tab lets you move
    assignments between Not Started, In Progress, and Done directly.

    ### ⚙️ You can always come back here
    Use the sidebar to re-open onboarding if you want to add more
    subjects or update your profile later.
    """)

    if st.button("Got it, let's go!", type="primary"):
        db.mark_tutorial_seen()
        st.rerun()


def render_persistent_chat():
    """Floating chat bubble pinned to the bottom of the screen, rendered
    outside the tabs so it stays visible no matter which tab is active."""
    if not st.session_state.chat_open:
        if st.button("💬", key="chat_toggle_btn"):
            st.session_state.chat_open = True
            st.rerun()
        return

    with st.container(key="chat_panel"):
        col_title, col_close = st.columns([6, 1])
        with col_title:
            st.markdown("**💬 Chat**")
        with col_close:
            if st.button("✕", key="chat_close_btn"):
                st.session_state.chat_open = False
                st.rerun()

        chat_box = st.container(height=280)
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


# ==================== SCREEN 3: Main app ====================
def render_main_app():
    with st.sidebar:
        profile = db.get_student_profile()
        if profile:
            st.write(f"👋 **{profile['name']}**, {profile['grade']}")
        if st.button("⚙️ Edit profile / add syllabus"):
            st.session_state.force_onboarding = True
            st.rerun()

    st.title("AI Timetable Planner")

    tab_timetable, tab_kanban = st.tabs(["Timetable", "Kanban board"])

    with tab_timetable:
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
            "locale": "en-gb",  # DD/MM date ordering instead of MM/DD
        }
        calendar(events=calendar_events, options=calendar_options, key="main_calendar")

        with st.expander("All events (raw list, useful for debugging)"):
            display_events = [
                {**e, "event_date": _format_date_display(e["event_date"])}
                for e in events
            ]
            st.table(display_events)

    with tab_kanban:
        render_kanban_tab()

    render_persistent_chat()

def _format_date_display(iso_date: str) -> str:
    """Converts 'YYYY-MM-DD' to 'DD/MM/YYYY' for display. Returns the
    original string unchanged if it isn't a valid ISO date (safer than
    guessing), and '' if empty."""
    if not iso_date:
        return ""
    try:
        parsed = datetime.strptime(iso_date, "%Y-%m-%d")
        return parsed.strftime("%d/%m/%Y")
    except ValueError:
        return iso_date


KANBAN_CARD_STYLE = """
.sortable-component {
    background: transparent !important;
}
.sortable-container {
    background: var(--secondary-background-color) !important;
    border-radius: 16px !important;
    padding: 14px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.12) !important;
}
.sortable-container-header {
    font-weight: 700 !important;
    font-size: 0.85em !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    padding-bottom: 10px !important;
    margin-bottom: 10px !important;
    border-bottom: 3px solid var(--primary-color) !important;
}
.sortable-item {
    background: var(--background-color) !important;
    border-left: 4px solid var(--primary-color) !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
    margin-bottom: 10px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.10) !important;
    white-space: pre-line !important;
    line-height: 1.4 !important;
    font-size: 0.92em !important;
}
"""


def render_kanban_tab():
    st.subheader("Assignments board")
    st.caption("Drag cards between columns to update progress. "
               "'Not started' = 0%, 'In progress' = 50%, 'Done' = 100%.")

    assignments = db.find_assignments(include_completed=True)

    def _label(a):
        subj = f"\n{a['subject']}" if a['subject'] else ""
        due = f"\nDue {_format_date_display(a['due_date'])}" if a['due_date'] else ""
        return f"{a['title']}{subj}{due}"

    not_started = [_label(a) for a in assignments if a["progress"] == 0]
    in_progress = [_label(a) for a in assignments if 0 < a["progress"] < 100]
    done = [_label(a) for a in assignments if a["progress"] == 100]
    label_to_id = {_label(a): a["id"] for a in assignments}

    board = [
        {"header": f"TO DO ({len(not_started)})", "items": not_started},
        {"header": f"IN PROGRESS ({len(in_progress)})", "items": in_progress},
        {"header": f"DONE ({len(done)})", "items": done},
    ]
    new_board = sort_items(
        board, multi_containers=True, direction="vertical",
        custom_style=KANBAN_CARD_STYLE, key="kanban_board",
    )

    # Map the (possibly re-numbered) headers back to plain column names
    header_to_column = {
        f"TO DO ({len(not_started)})": "Not started",
        f"IN PROGRESS ({len(in_progress)})": "In progress",
        f"DONE ({len(done)})": "Done",
    }
    column_progress = {"Not started": 0, "In progress": 50, "Done": 100}

    if new_board:
        for column in new_board:
            column_name = header_to_column.get(column["header"])
            if column_name is None:
                continue
            for item_label in column["items"]:
                assignment_id = label_to_id.get(item_label)
                if assignment_id is None:
                    continue
                new_progress = column_progress[column_name]
                current = next((a for a in assignments if a["id"] == assignment_id), None)
                if current and current["progress"] != new_progress:
                    db.update_assignment_progress(assignment_id, new_progress)

    with st.expander("Add a new task"):
        with st.form("add_task_form", clear_on_submit=True):
            new_title = st.text_input("Task title")
            new_subject = st.text_input("Subject (optional)")
            new_due = st.date_input("Due date (optional)", value=None, format="DD/MM/YYYY")
            submitted = st.form_submit_button("Add task")
            if submitted and new_title:
                due_str = new_due.strftime("%Y-%m-%d") if new_due else ""
                db.add_assignment(new_title, new_subject, due_str)
                st.rerun()


# ==================== Router ====================
stage = determine_stage()
if stage == "onboarding":
    render_onboarding()
elif stage == "tutorial":
    render_tutorial()
else:
    render_main_app()