"""
================================================================================
JARVIS — Graphical User Interface (ui/gui.py)
================================================================================
A Premium, Dark-Themed Tkinter Dashboard for the AI Assistant.

Features:
1. Threaded Execution: The Voice Agent runs in a background daemon thread, 
   preventing the GUI from freezing during API requests.
2. Real-time Log: Color-coded chat history with timestamps.
3. Live Schedule: Sidebar that automatically refreshes to show current events.
4. Dynamic Status: Visual indicators for Listening, Thinking, and Speaking.
5. Audio Control: Master mute toggle directly linked to the TTS engine.
================================================================================
"""

import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, font as tkfont
from pathlib import Path

# Path-safety shim
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.schedule import get_schedule
from data.reminders import get_reminders
from core.tts import set_muted, is_muted

# ------------------------------------------------------------------------------
# THEME CONFIGURATION (Aesthetics)
# ------------------------------------------------------------------------------
_FONT_SANS = "Segoe UI" if sys.platform == "win32" else "Helvetica"
_FONT_MONO = "Consolas" if sys.platform == "win32" else "Courier"

COLORS = {
    "bg_dark":        "#0a0a0f",   # Background: Deep Space
    "bg_panel":       "#111118",   # Panels: Midnight Blue
    "bg_chat":        "#0d0d14",   # Chat Box: Dark Obsidian
    "accent_blue":    "#3b82f6",   # Primary UI: Electric Blue
    "accent_cyan":    "#06b6d4",   # Sub-UI: Laser Cyan
    "accent_green":   "#10b981",   # Success: Emerald
    "accent_yellow":  "#f59e0b",   # Thinking: Amber
    "accent_red":     "#ef4444",   # Warning: Scarlet
    "accent_purple":  "#8b5cf6",   # Active: Neon Violet
    "accent_orange":  "#f97316",   # Active: Plasma Orange
    "text_primary":   "#e2e8f0",   # High-contrast slate
    "text_secondary": "#94a3b8",   # Low-contrast slate
    "text_jarvis":    "#38bdf8",   # Jarvis Bubble: Sky Blue
    "text_user":      "#a78bfa",   # User Bubble: Lavender
    "border":         "#1e293b",   # Subtle separators
}

# Mapping cognitive states to UI colors
STATUS_MAP = {
    "Listening...":    COLORS["accent_orange"],
    "Calibrating...":  COLORS["accent_orange"],
    "Transcribing...": COLORS["accent_yellow"],
    "Thinking...":     COLORS["accent_yellow"],
    "Speaking...":     COLORS["accent_purple"],
    "Ready":           COLORS["accent_green"],
    "Online":          COLORS["accent_green"],
    "Starting up...":  COLORS["accent_cyan"],
    "Shutting down...": COLORS["accent_red"],
    "Offline":         COLORS["text_secondary"],
    "Error":           COLORS["accent_red"],
}


class JarvisGUI:
    """
    Main Window Class.
    Manages the layout, thread orchestration, and real-time data binding.
    """

    def __init__(self):
        # -- Window Initialization --
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S. — Command Center")
        self.root.geometry("1100x700")
        self.root.minsize(900, 550)
        self.root.configure(bg=COLORS["bg_dark"])

        # Typography configuration
        self._font_title = tkfont.Font(family=_FONT_SANS, size=18, weight="bold")
        self._font_status = tkfont.Font(family=_FONT_SANS, size=12, weight="bold")
        self._font_chat = tkfont.Font(family=_FONT_MONO, size=11)
        self._font_schedule = tkfont.Font(family=_FONT_SANS, size=10)
        self._font_button = tkfont.Font(family=_FONT_SANS, size=10, weight="bold")
        self._font_small = tkfont.Font(family=_FONT_SANS, size=9)

        # Background Process Management
        self._agent = None
        self._agent_thread = None

        # Build the Visual Hierarchy
        self._build_header()
        self._build_main_body()
        self._build_footer()

        # Lifecycle Management
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._auto_refresh_loop()

    # --------------------------------------------------------------------------
    # COMPONENT BUILDERS
    # --------------------------------------------------------------------------

    def _build_header(self):
        """Creates the brand bar and high-level status indicator."""
        header = tk.Frame(self.root, bg=COLORS["bg_panel"], height=80)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        # LEFT: Identity
        id_frame = tk.Frame(header, bg=COLORS["bg_panel"])
        id_frame.pack(side=tk.LEFT, padx=30)
        
        tk.Label(id_frame, text="J.A.R.V.I.S.", font=self._font_title, 
                 fg=COLORS["accent_blue"], bg=COLORS["bg_panel"]).pack(side=tk.LEFT)
        tk.Label(id_frame, text=" — Systems Live", font=self._font_small, 
                 fg=COLORS["text_secondary"], bg=COLORS["bg_panel"]).pack(side=tk.LEFT, padx=10, pady=(5,0))

        # RIGHT: Real-time Status Readout
        st_frame = tk.Frame(header, bg=COLORS["bg_panel"])
        st_frame.pack(side=tk.RIGHT, padx=30)

        # The glowing status dot
        self._status_dot = tk.Label(st_frame, text="●", font=tkfont.Font(size=14), 
                                    fg=COLORS["accent_green"], bg=COLORS["bg_panel"])
        self._status_dot.pack(side=tk.LEFT, padx=10)

        self._status_label = tk.Label(st_frame, text="Online", font=self._font_status, 
                                      fg=COLORS["accent_green"], bg=COLORS["bg_panel"])
        self._status_label.pack(side=tk.LEFT)

    def _build_main_body(self):
        """The core layout containing Chat and Schedule panels."""
        body = tk.Frame(self.root, bg=COLORS["bg_dark"])
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # LEFT COLUMN: Interactive Chat Log
        log_frame = tk.Frame(body, bg=COLORS["bg_chat"], bd=1, highlightbackground=COLORS["border"], highlightthickness=1)
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Internal scrollable text widget
        self._chat_display = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, font=self._font_chat, bg=COLORS["bg_chat"],
            fg=COLORS["text_primary"], insertbackground=COLORS["text_primary"], 
            borderwidth=0, padx=20, pady=20, state=tk.DISABLED
        )
        self._chat_display.pack(fill=tk.BOTH, expand=True)

        # Message Styling Tags
        self._chat_display.tag_configure("jarvis", foreground=COLORS["text_jarvis"], 
                                         font=tkfont.Font(family=_FONT_MONO, size=11, weight="bold"))
        self._chat_display.tag_configure("user", foreground=COLORS["text_user"])
        self._chat_display.tag_configure("system", foreground=COLORS["text_secondary"], slant="italic")
        self._chat_display.tag_configure("time", foreground=COLORS["text_secondary"], font=self._font_small)

        # RIGHT COLUMN: Life Management Sidebar
        side_frame = tk.Frame(body, bg=COLORS["bg_panel"], width=300, bd=1, highlightbackground=COLORS["border"], highlightthickness=1)
        side_frame.pack(side=tk.RIGHT, fill=tk.Y)
        side_frame.pack_propagate(False)

        # Sidebar Title
        tk.Label(side_frame, text="   AGENDA OVERVIEW", font=self._font_small, 
                 fg=COLORS["text_secondary"], bg=COLORS["bg_panel"], pady=10).pack(anchor="w")

        self._agenda_view = tk.Text(
            side_frame, wrap=tk.WORD, font=self._font_schedule, bg=COLORS["bg_panel"],
            fg=COLORS["text_primary"], borderwidth=0, padx=15, state=tk.DISABLED
        )
        self._agenda_view.pack(fill=tk.BOTH, expand=True)

        # Agenda Styling Tags
        self._agenda_view.tag_configure("day", foreground=COLORS["accent_cyan"], weight="bold")
        self._agenda_view.tag_configure("today", foreground=COLORS["accent_yellow"], weight="bold")
        self._agenda_view.tag_configure("time", foreground=COLORS["text_secondary"])
        self._agenda_view.tag_configure("free", foreground=COLORS["accent_green"])

    def _build_footer(self):
        """The bottom control bar for hardware override."""
        footer = tk.Frame(self.root, bg=COLORS["bg_panel"], height=60)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        # TOGGLE: Global Audio Mute
        self._audio_btn = tk.Button(
            footer, text="🔊  AUDITORY SENSORS: ON", font=self._font_button,
            bg=COLORS["accent_blue"], fg="white", activebackground=COLORS["accent_cyan"],
            activeforeground="white", borderwidth=0, padx=25, cursor="hand2", 
            command=self._handle_mute_toggle
        )
        self._audio_btn.pack(side=tk.LEFT, padx=30, pady=10)

        # METADATA: Dynamic Provider Information
        try:
            from config import LLM_PROVIDER, PROVIDER_NAMES
            pname = PROVIDER_NAMES.get(LLM_PROVIDER, "Core Logic")
        except: pname = "AI Processor"

        tk.Label(footer, text=f"Active Brain: {pname}  |  Vocal Engine: Murf Falcon", 
                 font=self._font_small, fg=COLORS["text_secondary"], bg=COLORS["bg_panel"]).pack(side=tk.RIGHT, padx=30)

    # --------------------------------------------------------------------------
    # DATA BINDING & REACTION
    # --------------------------------------------------------------------------

    def update_status(self, raw_status: str) -> None:
        """Invoked by the background thread to update UI state."""
        def _apply():
            # Match status to theme color palette
            mapped_color = STATUS_MAP.get(raw_status, COLORS["text_primary"])
            self._status_label.configure(text=raw_status, fg=mapped_color)
            self._status_dot.configure(fg=mapped_color)
        self.root.after(0, _apply)

    def add_chat_message(self, role: str, message: str) -> None:
        """Pushes a new record into the conversation history log."""
        def _apply():
            self._chat_display.configure(state=tk.NORMAL)
            timestamp = datetime.now().strftime("%I:%M %p")
            
            # Header
            header = f"\n[{timestamp}] {'BRO' if role == 'user' else 'JARVIS'}:\n"
            style = "user" if role == "user" else "jarvis"
            
            self._chat_display.insert(tk.END, header, "time")
            self._chat_display.insert(tk.END, f"  {message}\n", style)
            
            self._chat_display.configure(state=tk.DISABLED)
            self._chat_display.see(tk.END) # Auto-scroll
        self.root.after(0, _apply)

    def _refresh_agenda(self):
        """Pulls fresh data from the schedule/reminder modules."""
        self._agenda_view.configure(state=tk.NORMAL)
        self._agenda_view.delete("1.0", tk.END)

        # Current Context
        today_name = datetime.now().strftime("%A")
        schedule_data = get_schedule()
        
        # Rendering Logic
        current_header = ""
        for item in schedule_data:
            if item["day"] != current_header:
                current_header = item["day"]
                # Visual Highlight if it's the current real-world day
                tag = "today" if current_header == today_name else "day"
                self._agenda_view.insert(tk.END, f"\n{current_header.upper()}\n", tag)
            
            self._agenda_view.insert(tk.END, f"  {item['time']:>8}  ", "time")
            status_tag = "free" if item["event"].lower() == "free" else ""
            self._agenda_view.insert(tk.END, f"{item['event']}\n", status_tag)

        # Persisted Reminders Check
        from data.reminders import get_reminders
        rems = get_reminders()
        if rems:
            self._agenda_view.insert(tk.END, "\n\nACTIVE REMINDERS\n", "today")
            for r in rems:
                self._agenda_view.insert(tk.END, f"  {r['time']:>8}  ", "time")
                self._agenda_view.insert(tk.END, f"{r['task']}\n")

        self._agenda_view.configure(state=tk.DISABLED)

    def _auto_refresh_loop(self):
        """Infinite polling loop for data updates (30s interval)."""
        self._refresh_agenda()
        self.root.after(30000, self._auto_refresh_loop)

    def _handle_mute_toggle(self):
        """Synchronizes the UI button state with the core audio logic."""
        new_mute_state = not is_muted()
        set_muted(new_mute_state)
        
        if new_mute_state:
            self._audio_btn.configure(text="🔇  AUDITORY SENSORS: OFF", bg=COLORS["accent_red"])
        else:
            self._audio_btn.configure(text="🔊  AUDITORY SENSORS: ON", bg=COLORS["accent_blue"])

    def _on_close(self):
        """Safe termination sequence."""
        if self._agent: self._agent.stop()
        self.root.after(200, self.root.destroy)

    def _bootstrap_agent(self):
        """Spawns the computational thread."""
        from core.agent import JarvisAgent
        self._agent = JarvisAgent(status_callback=self.update_status, message_callback=self.add_chat_message)
        
        self._agent_thread = threading.Thread(target=self._agent.run, daemon=True)
        self._agent_thread.start()
        self.add_chat_message("system", "Neural Infrastructure Initialized. Agent Online.")

    def run(self):
        """Launches the window. This is the application's blocking finish line."""
        self.root.after(800, self._bootstrap_agent) # Slight delay for smooth visual entry
        self.root.mainloop()


if __name__ == "__main__":
    gui = JarvisGUI()
    gui.run()
