"""Checklist and routines, saved as a JSON file on your computer."""

import json
import uuid
from datetime import date, datetime

from . import config

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _load() -> dict:
    if not config.DATA_FILE.exists():
        return {"tasks": [], "routines": []}
    with open(config.DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("tasks", [])
    data.setdefault("routines", [])
    return data


def _save(data: dict) -> None:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = config.DATA_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    tmp.replace(config.DATA_FILE)


def _new_id() -> str:
    return uuid.uuid4().hex[:6]


def _find(items: list[dict], item_id: str) -> dict:
    for item in items:
        if item["id"] == item_id:
            return item
    raise ValueError(f"Nothing found with id {item_id}")


# ---- Checklist --------------------------------------------------------------

def add_task(title: str, due: str | None = None) -> dict:
    if due:
        datetime.fromisoformat(due)  # raises ValueError if the format is wrong
    data = _load()
    task = {
        "id": _new_id(),
        "title": title,
        "due": due,
        "done": False,
        "created": datetime.now().isoformat(timespec="minutes"),
        "reminded": False,
    }
    data["tasks"].append(task)
    _save(data)
    return task


def list_tasks(include_done: bool = False) -> list[dict]:
    tasks = _load()["tasks"]
    return [t for t in tasks if include_done or not t["done"]]


def complete_task(task_id: str) -> dict:
    data = _load()
    task = _find(data["tasks"], task_id)
    task["done"] = True
    _save(data)
    return task


def delete_task(task_id: str) -> dict:
    data = _load()
    task = _find(data["tasks"], task_id)
    data["tasks"].remove(task)
    _save(data)
    return task


# ---- Routines ---------------------------------------------------------------

def _parse_days(days: list[str] | None) -> list[str]:
    """Accepts day names ("mon", "Tuesday"), "daily", "weekdays" or "weekends"."""
    if not days:
        return list(DAYS)
    chosen = set()
    for d in days:
        word = d.strip().lower()
        if word in ("daily", "everyday", "every day"):
            chosen.update(DAYS)
        elif word == "weekdays":
            chosen.update(DAYS[:5])
        elif word == "weekends":
            chosen.update(DAYS[5:])
        elif word[:3] in DAYS:
            chosen.add(word[:3])
        else:
            raise ValueError(f"Unknown day: {d}. Use mon..sun, daily, weekdays or weekends.")
    return [d for d in DAYS if d in chosen]


def add_routine(title: str, time: str, days: list[str] | None = None) -> dict:
    datetime.strptime(time, "%H:%M")  # raises ValueError if the format is wrong
    data = _load()
    routine = {
        "id": _new_id(),
        "title": title,
        "time": time,
        "days": _parse_days(days),
        "last_reminded": None,
    }
    data["routines"].append(routine)
    _save(data)
    return routine


def list_routines() -> list[dict]:
    return _load()["routines"]


def delete_routine(routine_id: str) -> dict:
    data = _load()
    routine = _find(data["routines"], routine_id)
    data["routines"].remove(routine)
    _save(data)
    return routine


def routines_for(day: date) -> list[dict]:
    key = DAYS[day.weekday()]
    return sorted((r for r in list_routines() if key in r["days"]), key=lambda r: r["time"])


# ---- Used by the reminder loop ---------------------------------------------

ROUTINE_WINDOW_MINUTES = 30  # don't fire a routine that was missed by more than this


def due_reminders(now: datetime) -> list[str]:
    """Return reminder messages that are due now, and mark them as sent."""
    data = _load()
    messages = []
    today = now.date().isoformat()
    weekday = DAYS[now.weekday()]

    for r in data["routines"]:
        hour, minute = map(int, r["time"].split(":"))
        start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        minutes_late = (now - start).total_seconds() / 60
        if (
            weekday in r["days"]
            and 0 <= minutes_late <= ROUTINE_WINDOW_MINUTES
            and r.get("last_reminded") != today
        ):
            r["last_reminded"] = today
            messages.append(f"Routine: {r['title']} ({r['time']})")

    for t in data["tasks"]:
        if t["done"] or t.get("reminded") or not t.get("due"):
            continue
        if datetime.fromisoformat(t["due"]) <= now:
            t["reminded"] = True
            messages.append(f"Task due: {t['title']}")

    if messages:
        _save(data)
    return messages
