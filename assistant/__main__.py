"""Command line: python -m assistant [chat | brief | remind]"""

import argparse
import sys
import time
from datetime import datetime

import anthropic

from . import store
from .agent import Assistant
from .notify import notify

BRIEF_PROMPT = (
    "Give me my daily briefing: a short summary of my unread emails (flag anything urgent "
    "or needing a reply), my open checklist items (overdue first), and today's routines in order."
)

TOOL_LABELS = {
    "list_emails": "checking your inbox",
    "search_emails": "searching your email",
    "read_email": "reading an email",
    "add_task": "adding to your checklist",
    "list_tasks": "looking at your checklist",
    "complete_task": "ticking off a task",
    "delete_task": "removing a task",
    "add_routine": "saving a routine",
    "list_routines": "looking at your routines",
    "delete_routine": "removing a routine",
}


def _show_tool(name, _args):
    print(f"  · {TOOL_LABELS.get(name, name)}...", flush=True)


def _ask(assistant: Assistant, text: str) -> None:
    try:
        print("\n" + assistant.ask(text) + "\n")
    except anthropic.AuthenticationError:
        sys.exit("Your Anthropic API key is missing or wrong. Set ANTHROPIC_API_KEY in your .env file.")
    except anthropic.RateLimitError:
        print("\nToo many requests right now. Wait a moment and try again.\n")
    except anthropic.APIConnectionError:
        print("\nCan't reach the Anthropic API. Check your internet connection.\n")
    except anthropic.APIStatusError as e:
        print(f"\nThe API returned an error ({e.status_code}): {e.message}\n")


def chat() -> None:
    print("Daily Assistant. Ask about your email, checklist or routines. Type 'exit' to quit.\n")
    assistant = Assistant(on_tool=_show_tool)
    while True:
        try:
            text = input("you › ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.lower() in ("exit", "quit", "bye"):
            break
        if text:
            _ask(assistant, text)


def brief() -> None:
    _ask(Assistant(on_tool=_show_tool), BRIEF_PROMPT)


def remind(interval: int = 30) -> None:
    print("Reminders are on. Keep this window open (Ctrl+C to stop).")
    today = store.routines_for(datetime.now().date())
    for r in today:
        print(f"  {r['time']}  {r['title']}")
    if not today:
        print("  No routines today yet. Add some in chat.")
    while True:
        try:
            for message in store.due_reminders(datetime.now()):
                notify("Daily Assistant", message)
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nReminders stopped.")
            return


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m assistant", description="Your AI daily assistant.")
    parser.add_argument(
        "command", nargs="?", default="chat", choices=["chat", "brief", "remind"],
        help="chat (default): talk to the assistant · brief: daily briefing · remind: run reminders",
    )
    args = parser.parse_args()
    {"chat": chat, "brief": brief, "remind": remind}[args.command]()


if __name__ == "__main__":
    main()
