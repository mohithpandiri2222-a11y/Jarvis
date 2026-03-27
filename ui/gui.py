# ============================================================
# JARVIS — GUI Module (ui/gui.py)
# ============================================================
# Premium dark-themed tkinter interface with:
#   - Scrollable chat log (user + Jarvis messages)
#   - Status indicator (Listening, Thinking, Speaking, Ready)
#   - Schedule panel on the right
#   - Mute toggle button
#   - Runs the agent loop in a background thread
# ============================================================

import sys
import threading
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, font as tkfont

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.schedule import get_schedule, get_schedule_summary
from data.reminders import get_reminders
from core.tts import set_muted, is_muted

# -- Cross-platform font selection ---------------------------------
_FONT_SANS = "Segoe UI" if sys.platform == "win32" else "Helvetica"
_FONT_MONO = "Consolas" if sys.platform == "win32" else "Courier"

# ═══════════════════════════════════════════════════════════════
# COLOUR PALETTE — Premium Dark Theme
# ═══════════════════════════════════════════════════════════════
COLORS = {
    "bg_dark":        "#0a0a0f",       # Main background (near black)
    "bg_panel":       "#111118",       # Panel background
    "bg_chat":        "#0d0d14",       # Chat area background
    "bg_input":       "#16161f",       # Input area background
    "accent_blue":    "#3b82f6",       # Primary accent (bright blue)
    "accent_cyan":    "#06b6d4",       # Secondary accent (cyan)
    "accent_green":   "#10b981",       # Status: ready / success
    "accent_yellow":  "#f59e0b",       # Status: thinking
    "accent_red":     "#ef4444",       # Status: error / muted
    "accent_purple":  "#8b5cf6",       # Status: speaking
    "accent_orange":  "#f97316",       # Status: listening
    "text_primary":   "#e2e8f0",       # Main text
    "text_secondary": "#94a3b8",       # Dim text
    "text_jarvis":    "#38bdf8",       # Jarvis message color
    "text_user":      "#a78bfa",       # User message color
    "border":         "#1e293b",       # Borders
    "scrollbar":      "#334155",       # Scrollbar
}

# Status → color mapping
STATUS_COLORS = {
    "Listening...":    COLORS["accent_orange"],
    "Calibrating...":  COLORS["accent_orange"],
    "Transcribing...": COLORS["accent_yellow"],
    "Thinking...":     COLORS["accent_yellow"],
    "Speaking...":     COLORS["accent_purple"],
    "Ready":           COLORS["accent_green"],
    "Starting up...":  COLORS["accent_cyan"],
    "Shutting down...": COLORS["accent_red"],
    "Offline":         COLORS["text_secondary"],
    "Error":           COLORS["accent_red"],
}


class JarvisGUI:
    """
    Premium dark-themed tkinter GUI for JARVIS.

    Usage:
        gui = JarvisGUI()
        gui.run()  # Blocks — starts mainloop
    """

    def __init__(self):
        # ── Root Window ──────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S. — Voice AI Assistant")
        self.root.geometry("1100x700")
        self.root.minsize(900, 550)
        self.root.configure(bg=COLORS["bg_dark"])

        # Try to set icon (optional)
        try:
            self.root.iconbitmap(default='')
        except Exception:
            pass

        # -- Custom Fonts (cross-platform) -------------------------
        self._font_title = tkfont.Font(family=_FONT_SANS, size=18, weight="bold")
        self._font_status = tkfont.Font(family=_FONT_SANS, size=12, weight="bold")
        self._font_chat = tkfont.Font(family=_FONT_MONO, size=11)
        self._font_schedule = tkfont.Font(family=_FONT_SANS, size=10)
        self._font_button = tkfont.Font(family=_FONT_SANS, size=10, weight="bold")
        self._font_label = tkfont.Font(family=_FONT_SANS, size=9)

        # ── Agent reference ──────────────────────────────────
        self._agent = None
        self._agent_thread = None

        # -- Build the UI ------------------------------------------
        self._build_header()
        self._build_main_area()
        self._build_footer()

        # -- Handle window close -----------------------------------
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # -- Auto-refresh schedule every 30 seconds ----------------
        self._auto_refresh_schedule()

    # ═══════════════════════════════════════════════════════════
    # UI CONSTRUCTION
    # ═══════════════════════════════════════════════════════════

    def _build_header(self):
        """Top bar with title and status."""
        header = tk.Frame(self.root, bg=COLORS["bg_panel"], height=70)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        # Left: Title
        title_frame = tk.Frame(header, bg=COLORS["bg_panel"])
        title_frame.pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(
            title_frame,
            text="J.A.R.V.I.S.",
            font=self._font_title,
            fg=COLORS["accent_blue"],
            bg=COLORS["bg_panel"],
        ).pack(side=tk.LEFT)

        tk.Label(
            title_frame,
            text="  Just A Rather Very Intelligent System",
            font=self._font_label,
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_panel"],
        ).pack(side=tk.LEFT, padx=(10, 0), pady=(5, 0))

        # Right: Status indicator
        status_frame = tk.Frame(header, bg=COLORS["bg_panel"])
        status_frame.pack(side=tk.RIGHT, padx=20, pady=10)

        self._status_dot = tk.Label(
            status_frame,
            text="●",
            font=tkfont.Font(size=14),
            fg=COLORS["accent_green"],
            bg=COLORS["bg_panel"],
        )
        self._status_dot.pack(side=tk.LEFT, padx=(0, 8))

        self._status_label = tk.Label(
            status_frame,
            text="Ready",
            font=self._font_status,
            fg=COLORS["accent_green"],
            bg=COLORS["bg_panel"],
        )
        self._status_label.pack(side=tk.LEFT)

    def _build_main_area(self):
        """Main content area: chat log (left) + schedule panel (right)."""
        main = tk.Frame(self.root, bg=COLORS["bg_dark"])
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 0))

        # ── Left: Chat Log ───────────────────────────────────
        chat_frame = tk.Frame(main, bg=COLORS["bg_chat"], bd=1,
                              highlightbackground=COLORS["border"],
                              highlightthickness=1)
        chat_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

        # Chat header
        chat_header = tk.Frame(chat_frame, bg=COLORS["bg_panel"], height=35)
        chat_header.pack(fill=tk.X)
        chat_header.pack_propagate(False)
        tk.Label(
            chat_header, text="  CONVERSATION LOG",
            font=self._font_label, fg=COLORS["text_secondary"],
            bg=COLORS["bg_panel"],
        ).pack(side=tk.LEFT, padx=10, pady=5)

        # Scrollable chat area
        self._chat_text = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=self._font_chat,
            bg=COLORS["bg_chat"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            selectbackground=COLORS["accent_blue"],
            borderwidth=0,
            highlightthickness=0,
            padx=15,
            pady=10,
            state=tk.DISABLED,
            cursor="arrow",
        )
        self._chat_text.pack(fill=tk.BOTH, expand=True)

        # Configure chat text tags for colored messages
        self._chat_text.tag_configure(
            "jarvis", foreground=COLORS["text_jarvis"],
            font=tkfont.Font(family=_FONT_MONO, size=11, weight="bold"),
        )
        self._chat_text.tag_configure(
            "user", foreground=COLORS["text_user"],
            font=tkfont.Font(family=_FONT_MONO, size=11),
        )
        self._chat_text.tag_configure(
            "system", foreground=COLORS["text_secondary"],
            font=tkfont.Font(family=_FONT_MONO, size=10, slant="italic"),
        )
        self._chat_text.tag_configure(
            "timestamp", foreground=COLORS["text_secondary"],
            font=tkfont.Font(family=_FONT_MONO, size=9),
        )

        # ── Right: Schedule Panel ────────────────────────────
        schedule_frame = tk.Frame(main, bg=COLORS["bg_panel"], width=280, bd=1,
                                  highlightbackground=COLORS["border"],
                                  highlightthickness=1)
        schedule_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        schedule_frame.pack_propagate(False)

        # Schedule header
        sched_header = tk.Frame(schedule_frame, bg=COLORS["bg_panel"], height=35)
        sched_header.pack(fill=tk.X)
        sched_header.pack_propagate(False)
        tk.Label(
            sched_header, text="  WEEKLY SCHEDULE",
            font=self._font_label, fg=COLORS["text_secondary"],
            bg=COLORS["bg_panel"],
        ).pack(side=tk.LEFT, padx=10, pady=5)

        # Schedule content
        self._schedule_text = tk.Text(
            schedule_frame,
            wrap=tk.WORD,
            font=self._font_schedule,
            bg=COLORS["bg_panel"],
            fg=COLORS["text_primary"],
            borderwidth=0,
            highlightthickness=0,
            padx=12,
            pady=8,
            state=tk.DISABLED,
            cursor="arrow",
        )
        self._schedule_text.pack(fill=tk.BOTH, expand=True)

        self._schedule_text.tag_configure(
            "day", foreground=COLORS["accent_cyan"],
            font=tkfont.Font(family=_FONT_SANS, size=10, weight="bold"),
        )
        self._schedule_text.tag_configure(
            "today", foreground=COLORS["accent_yellow"],
            font=tkfont.Font(family=_FONT_SANS, size=10, weight="bold"),
        )
        self._schedule_text.tag_configure(
            "event", foreground=COLORS["text_primary"],
        )
        self._schedule_text.tag_configure(
            "free", foreground=COLORS["accent_green"],
        )
        self._schedule_text.tag_configure(
            "time", foreground=COLORS["text_secondary"],
            font=tkfont.Font(family=_FONT_SANS, size=9),
        )

        # Populate schedule
        self._refresh_schedule()

    def _build_footer(self):
        """Bottom bar with mute button and info."""
        footer = tk.Frame(self.root, bg=COLORS["bg_panel"], height=50)
        footer.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        footer.pack_propagate(False)

        # Mute button
        self._mute_btn = tk.Button(
            footer,
            text="🔊 Audio ON",
            font=self._font_button,
            bg=COLORS["accent_blue"],
            fg="#ffffff",
            activebackground=COLORS["accent_cyan"],
            activeforeground="#ffffff",
            borderwidth=0,
            padx=20,
            pady=5,
            cursor="hand2",
            command=self._toggle_mute,
        )
        self._mute_btn.pack(side=tk.LEFT, padx=20, pady=8)

        # Info label
        tk.Label(
            footer,
            text='Say "exit" or "goodbye" to stop  |  Voice: Murf Falcon TTS + GPT-4o',
            font=self._font_label,
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_panel"],
        ).pack(side=tk.RIGHT, padx=20, pady=8)

    # ═══════════════════════════════════════════════════════════
    # UI UPDATE METHODS (thread-safe via root.after)
    # ═══════════════════════════════════════════════════════════

    def update_status(self, status: str) -> None:
        """Thread-safe status update."""
        def _update():
            color = STATUS_COLORS.get(status, COLORS["text_primary"])
            self._status_label.configure(text=status, fg=color)
            self._status_dot.configure(fg=color)
        self.root.after(0, _update)

    def add_message(self, role: str, text: str) -> None:
        """
        Thread-safe: adds a message to the chat log.

        Args:
            role: "user", "jarvis", or "system"
            text: The message text.
        """
        def _update():
            self._chat_text.configure(state=tk.NORMAL)

            timestamp = datetime.now().strftime("%I:%M %p")

            if role == "user":
                prefix = f"\n[{timestamp}]  You:\n"
                self._chat_text.insert(tk.END, prefix, "timestamp")
                self._chat_text.insert(tk.END, f"  {text}\n", "user")
            elif role == "jarvis":
                prefix = f"\n[{timestamp}]  JARVIS:\n"
                self._chat_text.insert(tk.END, prefix, "timestamp")
                self._chat_text.insert(tk.END, f"  {text}\n", "jarvis")
            else:
                self._chat_text.insert(tk.END, f"\n  {text}\n", "system")

            self._chat_text.configure(state=tk.DISABLED)
            self._chat_text.see(tk.END)

        self.root.after(0, _update)

    def _refresh_schedule(self) -> None:
        """Refreshes the schedule panel with current data. Highlights today."""
        self._schedule_text.configure(state=tk.NORMAL)
        self._schedule_text.delete("1.0", tk.END)

        schedule = get_schedule()
        today = datetime.now().strftime("%A")  # "Monday", "Tuesday" etc.

        # Sort by day order
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
                     "Friday", "Saturday", "Sunday"]
        schedule_sorted = sorted(schedule, key=lambda x: (
            day_order.index(x["day"]) if x["day"] in day_order else 7
        ))

        current_day = ""
        for entry in schedule_sorted:
            if entry["day"] != current_day:
                current_day = entry["day"]
                # Highlight today's day header in yellow
                day_tag = "today" if current_day == today else "day"
                self._schedule_text.insert(tk.END, f"\n{current_day}\n", day_tag)

            time_str = f"  {entry['time']:>8}  "
            self._schedule_text.insert(tk.END, time_str, "time")

            tag = "free" if entry["event"].lower() == "free" else "event"
            self._schedule_text.insert(tk.END, f"{entry['event']}\n", tag)

        # Show reminders if any
        reminders = get_reminders()
        if reminders:
            self._schedule_text.insert(tk.END, "\n\nREMINDERS\n", "today")
            for r in reminders:
                self._schedule_text.insert(tk.END,
                    f"  {r['time']:>8}  ", "time")
                self._schedule_text.insert(tk.END,
                    f"{r['task']} ({r['date']})\n", "event")

        self._schedule_text.configure(state=tk.DISABLED)

    def _auto_refresh_schedule(self) -> None:
        """Auto-refreshes the schedule panel every 30 seconds."""
        self._refresh_schedule()
        self.root.after(30000, self._auto_refresh_schedule)

    def _toggle_mute(self) -> None:
        """Toggles audio mute/unmute. Single source of truth in tts.py."""
        muted = not is_muted()
        set_muted(muted)

        if muted:
            self._mute_btn.configure(
                text="MUTED",
                bg=COLORS["accent_red"],
            )
        else:
            self._mute_btn.configure(
                text="Audio ON",
                bg=COLORS["accent_blue"],
            )

    def _on_close(self) -> None:
        """Handle window close cleanly without hanging."""
        if self._agent:
            self._agent.stop()
        # Small delay so the agent thread can exit the blocking listen() call
        self.root.after(200, self.root.destroy)

    # ═══════════════════════════════════════════════════════════
    # AGENT INTEGRATION
    # ═══════════════════════════════════════════════════════════

    def start_agent(self) -> None:
        """
        Creates and starts the JARVIS agent in a background thread.
        The agent uses this GUI's update methods as callbacks.
        """
        from core.agent import JarvisAgent

        self._agent = JarvisAgent(
            status_callback=self.update_status,
            message_callback=self.add_message,
        )

        self._agent_thread = threading.Thread(
            target=self._agent.run,
            daemon=True,
            name="JarvisAgentThread",
        )
        self._agent_thread.start()

        # Add system message to chat
        self.add_message("system",
                         "JARVIS initializing... Agent thread started.")

    def run(self) -> None:
        """
        Starts the GUI mainloop. This is BLOCKING.
        Call start_agent() before or after this as needed.
        """
        # Start agent in background after a short delay
        # (gives the GUI time to render first)
        self.root.after(500, self.start_agent)
        self.root.mainloop()


# ── Self-test / Standalone ───────────────────────────────────
if __name__ == "__main__":
    print("[GUI] Starting JARVIS GUI in standalone mode...")
    gui = JarvisGUI()
    gui.run()
