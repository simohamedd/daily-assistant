"""The tools Claude can use, and the code that runs them."""

import json

from . import email_client, store

TOOLS = [
    {
        "name": "list_emails",
        "description": "List the newest emails in a mailbox folder (sender, subject, date, unread flag, id). "
        "Use read_email with an id to see the full message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "count": {"type": "integer", "description": "How many emails, 1-50. Default 10."},
                "unread_only": {"type": "boolean", "description": "Only unread emails. Default false."},
                "folder": {"type": "string", "description": "Mailbox folder. Default INBOX."},
            },
        },
    },
    {
        "name": "search_emails",
        "description": "Find emails whose sender, subject or body contain some text.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Text to look for."},
                "count": {"type": "integer", "description": "Max results, 1-50. Default 10."},
                "folder": {"type": "string", "description": "Mailbox folder. Default INBOX."},
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_email",
        "description": "Read one email in full, by the id from list_emails or search_emails.",
        "input_schema": {
            "type": "object",
            "properties": {
                "email_id": {"type": "string"},
                "folder": {"type": "string", "description": "Mailbox folder. Default INBOX."},
            },
            "required": ["email_id"],
        },
    },
    {
        "name": "add_task",
        "description": "Add an item to the user's checklist, optionally with a due date and time "
        "(they get a desktop reminder when it is due).",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "due": {
                    "type": "string",
                    "description": "Local date-time in ISO format, e.g. 2026-11-18T09:00. Omit if no due time.",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "list_tasks",
        "description": "Show the checklist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_done": {"type": "boolean", "description": "Include finished items. Default false."},
            },
        },
    },
    {
        "name": "complete_task",
        "description": "Tick off a checklist item by id.",
        "input_schema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
    },
    {
        "name": "delete_task",
        "description": "Remove a checklist item by id. Only when the user asks to remove it.",
        "input_schema": {
            "type": "object",
            "properties": {"task_id": {"type": "string"}},
            "required": ["task_id"],
        },
    },
    {
        "name": "add_routine",
        "description": "Add a repeating routine (e.g. 'drink water at 10:00 every day'). "
        "The user gets a desktop reminder at that time on those days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "time": {"type": "string", "description": "24-hour time HH:MM, e.g. 07:30."},
                "days": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": 'Days: any of mon..sun, or ["daily"], ["weekdays"], ["weekends"]. Default daily.',
                },
            },
            "required": ["title", "time"],
        },
    },
    {
        "name": "list_routines",
        "description": "Show all routines.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "delete_routine",
        "description": "Remove a routine by id. Only when the user asks to remove it.",
        "input_schema": {
            "type": "object",
            "properties": {"routine_id": {"type": "string"}},
            "required": ["routine_id"],
        },
    },
]


def _count(value) -> int:
    return max(1, min(int(value or 10), 50))


def _run(name: str, args: dict):
    folder = args.get("folder") or "INBOX"
    if name == "list_emails":
        return email_client.list_emails(_count(args.get("count")), bool(args.get("unread_only")), folder)
    if name == "search_emails":
        return email_client.search_emails(str(args["query"]), _count(args.get("count")), folder)
    if name == "read_email":
        return email_client.read_email(str(args["email_id"]), folder)
    if name == "add_task":
        return store.add_task(str(args["title"]), args.get("due") or None)
    if name == "list_tasks":
        return store.list_tasks(bool(args.get("include_done")))
    if name == "complete_task":
        return store.complete_task(str(args["task_id"]))
    if name == "delete_task":
        return store.delete_task(str(args["task_id"]))
    if name == "add_routine":
        return store.add_routine(str(args["title"]), str(args["time"]), args.get("days"))
    if name == "list_routines":
        return store.list_routines()
    if name == "delete_routine":
        return store.delete_routine(str(args["routine_id"]))
    raise ValueError(f"Unknown tool: {name}")


def run_tool(name: str, args: dict) -> tuple[str, bool]:
    """Run a tool. Returns (result text, is_error)."""
    try:
        result = _run(name, args or {})
        return json.dumps(result, ensure_ascii=False, default=str), False
    except email_client.EmailNotConfigured as e:
        return str(e), True
    except (KeyError, ValueError, TypeError) as e:
        return f"Invalid input: {e}", True
    except Exception as e:  # network / IMAP errors: tell Claude so it can explain
        return f"{type(e).__name__}: {e}", True
