"""
ai_chat.py
The chatbot "brain" — uses Gemini's function calling to turn natural
language into real timetable actions.

Get a free API key at https://aistudio.google.com/apikey
Then set it as an environment variable: GEMINI_API_KEY

Install with: pip install google-genai
"""

import os
import json
from datetime import datetime
from google import genai
from google.genai import types

import database as db

MODEL_NAME = "gemini-3.6-flash"
client = genai.Client()

SYSTEM_INSTRUCTION = f"""You are a friendly AI assistant inside a student timetable
planner app. Today's date is {datetime.now().strftime('%Y-%m-%d')}.

You manage three things: the timetable (classes/events), assignments
(with a 0-100 progress score), and exam dates.

When the user mentions a day of the week without a date, figure out the
actual calendar date relative to today.

Always confirm what you did in a short, friendly sentence, e.g.
"Sure! Added English class on Wednesday at 12:30 PM."
When editing or updating something, first find the matching item with
find_events or find_assignments, then act on it — don't guess an id,
always look it up first.

When the user asks what's due, use get_due_now and list the titles
clearly. When they report progress on something, use
update_assignment_progress, congratulate them briefly, and if there's
another assignment still due, mention it as a gentle nudge (like
"Great job! Let's focus on Math now!").

When asked about exams, use get_upcoming_exams and mention the soonest
one(s) clearly.
"""

# ---- Tool (function) declarations Gemini can call ----

tools = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="add_event",
            description="Add a new class/event to the student's timetable.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "e.g. 'English Class'"},
                    "subject": {"type": "string", "description": "e.g. 'English'"},
                    "event_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "start_time": {"type": "string", "description": "HH:MM, 24-hour"},
                    "end_time": {"type": "string", "description": "HH:MM, 24-hour"},
                },
                "required": ["title", "event_date", "start_time", "end_time"],
            },
        ),
        types.FunctionDeclaration(
            name="find_events",
            description="Search existing timetable events by date and/or subject, "
                        "to find the event the user is referring to before editing it.",
            parameters={
                "type": "object",
                "properties": {
                    "event_date": {"type": "string", "description": "YYYY-MM-DD, optional"},
                    "subject": {"type": "string", "description": "optional"},
                },
            },
        ),
        types.FunctionDeclaration(
            name="update_event",
            description="Update an existing event's time, title, or subject. "
                        "Requires the event_id from find_events.",
            parameters={
                "type": "object",
                "properties": {
                    "event_id": {"type": "integer"},
                    "start_time": {"type": "string", "description": "HH:MM, optional"},
                    "end_time": {"type": "string", "description": "HH:MM, optional"},
                    "title": {"type": "string", "description": "optional"},
                },
                "required": ["event_id"],
            },
        ),
        types.FunctionDeclaration(
            name="delete_event",
            description="Remove an event from the timetable. Requires event_id.",
            parameters={
                "type": "object",
                "properties": {"event_id": {"type": "integer"}},
                "required": ["event_id"],
            },
        ),
        types.FunctionDeclaration(
            name="add_assignment",
            description="Add a new assignment/homework item to track.",
            parameters={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "e.g. 'English Notebook Work'"},
                    "subject": {"type": "string"},
                    "due_date": {"type": "string", "description": "YYYY-MM-DD, optional"},
                },
                "required": ["title"],
            },
        ),
        types.FunctionDeclaration(
            name="find_assignments",
            description="Search assignments by subject, to find the one the "
                        "user means before updating its progress.",
            parameters={
                "type": "object",
                "properties": {
                    "subject": {"type": "string", "description": "optional"},
                },
            },
        ),
        types.FunctionDeclaration(
            name="get_due_now",
            description="Get all unfinished assignments due on or before today. "
                        "Use this when the user asks what's due / what homework they have.",
            parameters={
                "type": "object",
                "properties": {
                    "reference_date": {"type": "string", "description": "YYYY-MM-DD, usually today"},
                },
                "required": ["reference_date"],
            },
        ),
        types.FunctionDeclaration(
            name="update_assignment_progress",
            description="Update how far along an assignment is, as a 0-100 percent. "
                        "Requires assignment_id from find_assignments or get_due_now.",
            parameters={
                "type": "object",
                "properties": {
                    "assignment_id": {"type": "integer"},
                    "progress": {"type": "integer", "description": "0 to 100"},
                },
                "required": ["assignment_id", "progress"],
            },
        ),
        types.FunctionDeclaration(
            name="add_exam",
            description="Record an upcoming exam.",
            parameters={
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "exam_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "notes": {"type": "string", "description": "optional"},
                },
                "required": ["subject", "exam_date"],
            },
        ),
        types.FunctionDeclaration(
            name="get_upcoming_exams",
            description="Get all exams on or after a given date, soonest first. "
                        "Use this when the user asks when their exams are.",
            parameters={
                "type": "object",
                "properties": {
                    "reference_date": {"type": "string", "description": "YYYY-MM-DD, usually today"},
                },
                "required": ["reference_date"],
            },
        ),
    ])
]

# Maps tool names to the real Python functions that execute them
TOOL_DISPATCH = {
    "add_event": lambda **kw: db.add_event(
        title=kw["title"], subject=kw.get("subject", ""),
        event_date=kw["event_date"], start_time=kw["start_time"],
        end_time=kw["end_time"],
    ),
    "find_events": lambda **kw: db.find_events(
        event_date=kw.get("event_date"), subject=kw.get("subject"),
    ),
    "update_event": lambda **kw: db.update_event(
        kw.pop("event_id"), **kw
    ),
    "delete_event": lambda **kw: db.delete_event(kw["event_id"]),
    "add_assignment": lambda **kw: db.add_assignment(
        title=kw["title"], subject=kw.get("subject", ""), due_date=kw.get("due_date", ""),
    ),
    "find_assignments": lambda **kw: db.find_assignments(subject=kw.get("subject")),
    "get_due_now": lambda **kw: db.get_due_now(kw["reference_date"]),
    "update_assignment_progress": lambda **kw: db.update_assignment_progress(
        kw["assignment_id"], kw["progress"],
    ),
    "add_exam": lambda **kw: db.add_exam(
        subject=kw["subject"], exam_date=kw["exam_date"], notes=kw.get("notes", ""),
    ),
    "get_upcoming_exams": lambda **kw: db.get_upcoming_exams(kw["reference_date"]),
}


def chat_with_ai(user_message: str, history: list) -> tuple[str, list]:
    """
    Sends the user's message + conversation history to Gemini, executes any
    tool calls it makes, and returns (reply_text, updated_history).

    Some requests need MULTIPLE steps (e.g. "delete my Chemistry class" needs
    find_events first, THEN delete_event with the id it found) — so this loops
    until Gemini responds with plain text instead of another tool call.

    `history` is a list of google.genai `Content` objects — pass the same
    list back in on the next call so context ("change it to 1pm") works.
    """
    history.append(types.Content(role="user", parts=[types.Part(text=user_message)]))

    MAX_STEPS = 6  # safety limit so a confused AI can't loop forever
    for _ in range(MAX_STEPS):
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=history,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=tools,
            ),
        )

        candidate = response.candidates[0]
        history.append(candidate.content)

        function_calls = [
            part.function_call for part in candidate.content.parts if part.function_call
        ]

        if not function_calls:
            # No more tool calls — this is the final, plain-text reply
            text_parts = [p.text for p in candidate.content.parts if p.text]
            reply_text = " ".join(text_parts) if text_parts else \
                "Done!"  # fallback if the model replied with no text at all
            return reply_text, history

        # Run every requested tool call, then feed the results back in
        tool_response_parts = []
        for call in function_calls:
            fn_name = call.name
            fn_args = dict(call.args)
            try:
                result = TOOL_DISPATCH[fn_name](**fn_args)
            except Exception as e:
                result = {"error": str(e)}

            tool_response_parts.append(
                types.Part.from_function_response(
                    name=fn_name, response={"result": result}
                )
            )

        history.append(types.Content(role="user", parts=tool_response_parts))
        # Loop again — Gemini now sees the tool result and decides whether
        # it needs another tool call (e.g. delete after find) or can reply.

    return "Sorry, that got a bit complicated — could you try rephrasing?", history