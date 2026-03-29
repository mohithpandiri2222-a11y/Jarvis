"""
================================================================================
JARVIS — Reminders Store (data/reminders.py)
================================================================================
The Ephemeral Memory Bank for Short-Term Tasks.

This module provides an ID-trackable store for reminders set by voice.
Unlike the Schedule (which is time-rigid), Reminders are flexible tasks 
associated with a time and date.

Logic:
1. Auto-incrementing IDs for easy voice-deletion ("Delete reminder number 2").
2. JSON-serializable output for AI context injection.
================================================================================
"""

from typing import List, Dict, Optional

# Global sensory storage
_reminders: List[Dict] = []
_id_counter: int = 1


def add_reminder(task: str, time: str, date: str = "today") -> Dict:
    """
    Registers a new task into the assistant's memory.
    
    Args:
        task: Description of the duty.
        time: Human-relative or specific time.
        date: Day reference.
    """
    global _id_counter
    
    entry = {
        "id": _id_counter,
        "task": task.strip(),
        "time": time.strip(),
        "date": date.strip(),
    }
    
    _reminders.append(entry)
    _id_counter += 1
    
    print(f"[DATA] Neural Write: Set Reminder #{entry['id']} for {task}.")
    return entry


def get_reminders() -> List[Dict]:
    """Returns the current active task list."""
    return _reminders.copy()


def purge_reminder(id_to_delete: int) -> bool:
    """
    Locates and removes a task by its ID number.
    Used when the user says "Jarvis, delete reminder two."
    """
    global _reminders
    initial = len(_reminders)
    _reminders = [r for r in _reminders if r["id"] != id_to_delete]
    
    success = len(_reminders) < initial
    if success: print(f"[DATA] Neural Write: Purged Record #{id_to_delete}.")
    return success


def clear_system_memory() -> None:
    """Resets the entire reminder store."""
    global _reminders, _id_counter
    _reminders = []
    _id_counter = 1


def get_text_summary() -> str:
    """Returns a bulleted list for the GUI or Terminal logs."""
    if not _reminders: return " (No pending tasks detected)"
    return "\n".join([f"• #{r['id']} {r['task']} @ {r['time']}" for r in _reminders])


if __name__ == "__main__":
    add_reminder("Execute Neural Patch", "18:00")
    print(get_text_summary())
