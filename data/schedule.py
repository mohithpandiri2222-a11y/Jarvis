# ============================================================
# JARVIS — Schedule Data Module (data/schedule.py)
# ============================================================
# Mock schedule stored as a Python list of dicts.
# In a future version, this would connect to Google Calendar.
# ============================================================

import json
from typing import List, Dict, Optional

# ── The Mock Schedule ────────────────────────────────────────
# This is the hardcoded schedule for the prototype.
# Each entry has: day, time, event
_schedule: List[Dict[str, str]] = [
    {"day": "Monday",    "time": "10:00 AM", "event": "Team Standup"},
    {"day": "Monday",    "time": "3:00 PM",  "event": "Project Review"},
    {"day": "Tuesday",   "time": "11:00 AM", "event": "Client Call - Sharma"},
    {"day": "Tuesday",   "time": "4:00 PM",  "event": "Free"},
    {"day": "Wednesday", "time": "10:00 AM", "event": "Sprint Planning"},
    {"day": "Wednesday", "time": "2:00 PM",  "event": "Free"},
    {"day": "Thursday",  "time": "9:00 AM",  "event": "Design Review"},
    {"day": "Thursday",  "time": "4:00 PM",  "event": "Free"},
    {"day": "Friday",    "time": "3:00 PM",  "event": "Free"},
    {"day": "Friday",    "time": "6:00 PM",  "event": "Team Dinner"},
]


def get_schedule() -> List[Dict[str, str]]:
    """
    Returns the current schedule as a list of dicts.
    Each dict has keys: 'day', 'time', 'event'.
    """
    return _schedule.copy()


def get_schedule_for_day(day: str) -> List[Dict[str, str]]:
    """
    Returns all schedule entries for a specific day.

    Args:
        day: Day name (e.g., "Monday", "Tuesday")

    Returns:
        List of schedule entries for that day.
    """
    day_lower = day.strip().lower()
    return [
        entry for entry in _schedule
        if entry["day"].lower() == day_lower
    ]


def add_event(day: str, time: str, event: str) -> Dict[str, str]:
    """
    Adds a new event to the schedule.

    Args:
        day: Day of the week (e.g., "Monday")
        time: Time string (e.g., "3:00 PM")
        event: Event description (e.g., "Meeting with John")

    Returns:
        The newly created schedule entry.
    """
    new_entry = {
        "day": day.strip(),
        "time": time.strip(),
        "event": event.strip(),
    }
    _schedule.append(new_entry)
    print(f"[SCHEDULE] Added: {event} on {day} at {time}")
    return new_entry


def remove_event(day: str, time: str) -> bool:
    """
    Removes an event from the schedule by day and time.

    Args:
        day: Day of the week.
        time: Time string.

    Returns:
        True if an event was removed, False if not found.
    """
    global _schedule
    day_lower = day.strip().lower()
    time_lower = time.strip().lower()

    original_length = len(_schedule)
    _schedule = [
        entry for entry in _schedule
        if not (entry["day"].lower() == day_lower and
                entry["time"].lower() == time_lower)
    ]

    removed = len(_schedule) < original_length
    if removed:
        print(f"[SCHEDULE] Removed event on {day} at {time}")
    else:
        print(f"[SCHEDULE] No event found on {day} at {time}")
    return removed


def check_conflict(day: str, time: str) -> Optional[Dict[str, str]]:
    """
    Checks if there's an existing (non-Free) event at the given day and time.

    Args:
        day: Day of the week.
        time: Time string.

    Returns:
        The conflicting event entry, or None if the slot is free.
    """
    day_lower = day.strip().lower()
    time_lower = time.strip().lower()

    for entry in _schedule:
        if (entry["day"].lower() == day_lower and
                entry["time"].lower() == time_lower and
                entry["event"].lower() != "free"):
            return entry
    return None


def get_schedule_summary() -> str:
    """
    Returns a human-readable summary of the schedule.
    Useful for terminal display and debugging.
    """
    lines = ["=" * 45, "  WEEKLY SCHEDULE", "=" * 45]
    current_day = ""

    for entry in sorted(_schedule, key=lambda x: (
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
         "Saturday", "Sunday"].index(x["day"])
        if x["day"] in ["Monday", "Tuesday", "Wednesday", "Thursday",
                         "Friday", "Saturday", "Sunday"] else 7
    )):
        if entry["day"] != current_day:
            current_day = entry["day"]
            lines.append(f"\n  {current_day}:")
        status = "  ✓" if entry["event"].lower() != "free" else "  ○"
        lines.append(f"    {status} {entry['time']:>8}  {entry['event']}")

    lines.append("\n" + "=" * 45)
    return "\n".join(lines)


# ── Self-test ────────────────────────────────────────────────
if __name__ == "__main__":
    print(get_schedule_summary())
    print()

    # Test conflict detection
    conflict = check_conflict("Monday", "3:00 PM")
    if conflict:
        print(f"Conflict found: {conflict['event']} at {conflict['time']}")
    else:
        print("No conflict at Monday 3:00 PM")

    # Test adding
    add_event("Wednesday", "5:00 PM", "Gym Session")
    print(f"\nSchedule now has {len(get_schedule())} entries.")

    # Test JSON output (what goes to GPT-4o)
    print(f"\nJSON:\n{json.dumps(get_schedule(), indent=2)}")
