"""
================================================================================
JARVIS — Schedule Engine (data/schedule.py)
================================================================================
Local Calendar & Time-Slot Management.

This module provides the interface for Jarvis to:
1. Retrieve the user's weekly agenda.
2. Search for events on specific days.
3. Dynamically inject new events from voice commands.
4. Verify time-slot availability (Conflict Detection).

Currently implemented as a high-performance in-memory list for prototyping.
================================================================================
"""

import json
from typing import List, Dict, Optional

# ------------------------------------------------------------------------------
# THE PERSISTENT DATA SCHEMA
# ------------------------------------------------------------------------------
# In a real-world scenario, this 'database' would be replaced by a 
# Google Calendar or Outlook API connector.
_schedule: List[Dict[str, str]] = [
    {"day": "Monday",    "time": "10:00 AM", "event": "Team Standup"},
    {"day": "Monday",    "time": "03:00 PM", "event": "Project Review"},
    {"day": "Tuesday",   "time": "11:00 AM", "event": "Client Call: Sharma"},
    {"day": "Tuesday",   "time": "04:00 PM", "event": "Free"},
    {"day": "Wednesday", "time": "10:00 AM", "event": "Sprint Planning"},
    {"day": "Wednesday", "time": "02:00 PM", "event": "Free"},
    {"day": "Thursday",  "time": "09:00 AM", "event": "Core Design Review"},
    {"day": "Thursday",  "time": "04:00 PM", "event": "Free"},
    {"day": "Friday",    "time": "03:00 PM", "event": "Free"},
    {"day": "Friday",    "time": "06:00 PM", "event": "Team Social Dinner"},
]


def get_schedule() -> List[Dict[str, str]]:
    """Returns a protected copy of the entire scheduling database."""
    return _schedule.copy()


def get_schedule_for_day(day: str) -> List[Dict[str, str]]:
    """Filters the calendar for events matching a specific day index."""
    query = day.strip().lower()
    return [e for e in _schedule if e["day"].lower() == query]


def add_event(day: str, time: str, event: str) -> Dict[str, str]:
    """
    Appends a new logical event node to the user's agenda.
    
    Args:
        day (str): Human-readable day (e.g., 'Monday').
        time (str): Formatted time (e.g., '05:00 PM').
        event (str): Descriptive text for the activity.
    """
    new_node = {"day": day.strip(), "time": time.strip(), "event": event.strip()}
    _schedule.append(new_node)
    print(f"[DATA] Schedule Write: Added '{event}' on {day} at {time}.")
    return new_node


def remove_event(day: str, time: str) -> bool:
    """
    Locates and purges an event by its exact time-slot.
    
    Returns:
        bool: True if the operation resulted in a deletion.
    """
    global _schedule
    d, t = day.strip().lower(), time.strip().lower()
    
    initial_count = len(_schedule)
    _schedule = [e for e in _schedule if not (e["day"].lower() == d and e["time"].lower() == t)]
    
    success = len(_schedule) < initial_count
    if success: print(f"[DATA] Schedule Write: Removed slot {day} {time}.")
    return success


def check_collision(day: str, time: str) -> Optional[Dict[str, str]]:
    """
    Detects if a requested time slot is preoccupied by a non-'Free' event.
    Essential for Jarvis's 'smart' conflict detection logic.
    """
    d, t = day.strip().lower(), time.strip().lower()
    for entry in _schedule:
        if entry["day"].lower() == d and entry["time"].lower() == t:
            if entry["event"].lower() != "free":
                return entry
    return None


# ------------------------------------------------------------------------------
# CONSOLE UTILITIES
# ------------------------------------------------------------------------------
def get_visual_summary() -> str:
    """Generates a formatted ASCII table of the user's week for logs."""
    output = ["-" * 60, " JARVIS — LOCAL AGENDA SUMMARY", "-" * 60]
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Simple nested loop for day-grouping
    for d in days:
        daily_items = get_schedule_for_day(d)
        if daily_items:
            output.append(f"\n[{d.upper()}]")
            for i in daily_items:
                marker = " [!] " if i["event"].lower() != "free" else " [ ] "
                output.append(f"  {marker} {i['time']:>8} : {i['event']}")
    
    output.append("\n" + "-" * 60)
    return "\n".join(output)


if __name__ == "__main__":
    print(get_visual_summary())
