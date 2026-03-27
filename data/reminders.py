# ============================================================
# JARVIS — Reminders Data Module (data/reminders.py)
# ============================================================
# In-memory reminder store with auto-incrementing IDs.
# Data lives only for the current session.
# In a future version, this would use SQLite for persistence.
# ============================================================

import json
from typing import List, Dict, Optional

# ── In-memory store ──────────────────────────────────────────
_reminders: List[Dict] = []
_next_id: int = 1


def add_reminder(task: str, time: str, date: str = "today") -> Dict:
    """
    Adds a new reminder.

    Args:
        task: What to remind about (e.g., "Call Rahul")
        time: When (e.g., "7:00 PM")
        date: Date string (e.g., "today", "tomorrow", "Monday")

    Returns:
        The newly created reminder dict with its assigned ID.
    """
    global _next_id

    reminder = {
        "id": _next_id,
        "task": task.strip(),
        "time": time.strip(),
        "date": date.strip(),
    }

    _reminders.append(reminder)
    _next_id += 1

    print(f"[REMINDERS] Added #{reminder['id']}: {task} at {time} ({date})")
    return reminder


def get_reminders() -> List[Dict]:
    """
    Returns all current reminders as a list of dicts.
    Each dict has keys: 'id', 'task', 'time', 'date'.
    """
    return _reminders.copy()


def get_reminder_by_id(reminder_id: int) -> Optional[Dict]:
    """
    Returns a specific reminder by its ID.

    Args:
        reminder_id: The reminder's unique ID.

    Returns:
        The reminder dict, or None if not found.
    """
    for reminder in _reminders:
        if reminder["id"] == reminder_id:
            return reminder.copy()
    return None


def delete_reminder(reminder_id: int) -> bool:
    """
    Deletes a reminder by its ID.

    Args:
        reminder_id: The reminder's unique ID.

    Returns:
        True if the reminder was deleted, False if not found.
    """
    global _reminders

    original_length = len(_reminders)
    _reminders = [r for r in _reminders if r["id"] != reminder_id]

    deleted = len(_reminders) < original_length
    if deleted:
        print(f"[REMINDERS] Deleted reminder #{reminder_id}")
    else:
        print(f"[REMINDERS] Reminder #{reminder_id} not found")
    return deleted


def clear_reminders() -> int:
    """
    Clears all reminders.

    Returns:
        Number of reminders that were cleared.
    """
    global _reminders, _next_id

    count = len(_reminders)
    _reminders = []
    _next_id = 1

    print(f"[REMINDERS] Cleared all {count} reminders.")
    return count


def get_reminders_count() -> int:
    """Returns the number of active reminders."""
    return len(_reminders)


def get_reminders_summary() -> str:
    """
    Returns a human-readable summary of all reminders.
    Useful for terminal display and debugging.
    """
    if not _reminders:
        return "  No reminders set."

    lines = []
    for r in _reminders:
        lines.append(f"  #{r['id']}  {r['task']:.<30} {r['time']:>8}  ({r['date']})")
    return "\n".join(lines)


# ── Self-test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("  JARVIS Reminders — Test")
    print("=" * 50)

    # Add some test reminders
    add_reminder("Call Rahul", "7:00 PM", "today")
    add_reminder("Submit assignment", "9:00 PM", "today")
    add_reminder("Buy groceries", "10:00 AM", "tomorrow")

    print(f"\n  Total reminders: {get_reminders_count()}")
    print(f"\n{get_reminders_summary()}")

    # Delete one
    print()
    delete_reminder(2)
    print(f"\n  After deletion: {get_reminders_count()} reminders")
    print(f"\n{get_reminders_summary()}")

    # JSON output (what goes to GPT-4o)
    print(f"\n  JSON:\n{json.dumps(get_reminders(), indent=2)}")

    # Clear all
    print()
    clear_reminders()
    print(f"  After clear: {get_reminders_count()} reminders")
