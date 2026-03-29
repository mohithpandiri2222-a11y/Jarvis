"""
================================================================================
JARVIS — First-Time Setup Wizard (ui/setup_dialog.py)
================================================================================
The Configuration Gateway for new J.A.R.V.I.S. installations.

This module provides a premium, interactive window that:
1. Guides the user through choosing an AI Provider (Brains).
2. Facilitates secure entry of API keys (OpenAI, Claude, or Gemini).
3. Optionally configures Murf TTS for premium vocal output.
4. Serializes these credentials directly to a local .env file.
================================================================================
"""

import sys
import tkinter as tk
from tkinter import font as tkfont, messagebox
from pathlib import Path

# Path-safety shim
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ------------------------------------------------------------------------------
# THEME & BRANDING (Consistent with Main GUI)
# ------------------------------------------------------------------------------
COLORS = {
    "bg_dark":        "#0a0a0f",   # Cosmic Black
    "bg_panel":       "#111118",   # Deep Space
    "bg_card":        "#16161f",   # Card Surface
    "bg_input":       "#1c1c28",   # Input Field
    "accent_blue":    "#3b82f6",   # Brand Blue
    "accent_cyan":    "#06b6d4",   # Cyber Cyan
    "text_primary":   "#e2e8f0",   # High-contrast White
    "text_secondary": "#94a3b8",   # Muted Slate
    "border":         "#1e293b",   # Steel Grey
}

# ------------------------------------------------------------------------------
# PROVIDER CATALOG
# ------------------------------------------------------------------------------
# These definitions power the radio buttons, descriptions, and dynamic help links.
PROVIDERS = {
    "openai": {
        "name": "OpenAI (GPT-4o)",
        "color": "#10b981", # Emerald
        "desc": "Optimal for general logic, coding, and fast responses.",
        "url": "https://platform.openai.com/api-keys",
    },
    "claude": {
        "name": "Anthropic (Claude 3.7)",
        "color": "#f97316", # Orange
        "desc": "Top-tier reasoning, emotional nuance, and long context.",
        "url": "https://console.anthropic.com/settings/keys",
    },
    "gemini": {
        "name": "Google (Gemini 2.0)",
        "color": "#3b82f6", # Blue
        "desc": "Deep Google Search integration and multimodal agility.",
        "url": "https://aistudio.google.com/apikey",
    },
}

_FONT_SANS = "Segoe UI" if sys.platform == "win32" else "Helvetica"


class SetupDialog:
    """
    The Setup Orchestrator.
    Handles user interaction, basic validation, and config persistence.
    """

    def __init__(self):
        self._result = None
        self._provider_var = tk.StringVar(value="openai")

        # -- Core Window Configuration --
        self.root = tk.Tk()
        self.root.title("JARVIS — Neural Link Setup")
        self.root.geometry("620x720")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg_dark"])

        # Typography setup
        self._f_title = tkfont.Font(family=_FONT_SANS, size=24, weight="bold")
        self._f_head  = tkfont.Font(family=_FONT_SANS, size=12, weight="bold")
        self._f_body  = tkfont.Font(family=_FONT_SANS, size=10)
        self._f_mono  = tkfont.Font(family="Consolas" if sys.platform == "win32" else "Courier", size=10)

        self._build_interface()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_interface(self):
        """Constructs the visual components of the wizard."""
        main = tk.Frame(self.root, bg=COLORS["bg_dark"])
        main.pack(fill=tk.BOTH, expand=True, padx=40, pady=30)

        # 1. THE HOOK (Title & Motivation)
        tk.Label(main, text="J.A.R.V.I.S.", font=self._f_title, fg=COLORS["accent_blue"], bg=COLORS["bg_dark"]).pack(anchor="w")
        tk.Label(main, text="Neural Infrastructure Configuration Wizard", font=self._f_body, 
                 fg=COLORS["text_secondary"], bg=COLORS["bg_dark"]).pack(anchor="w", pady=(0, 20))

        # 2. SELECT THE BRAIN (Provider Selection)
        tk.Label(main, text="STEP 1: Choose an AI Intelligence Provider", font=self._f_head, 
                 fg=COLORS["text_primary"], bg=COLORS["bg_dark"]).pack(anchor="w", pady=(10, 10))

        self._provider_cards = {}
        for pid, info in PROVIDERS.items():
            card = tk.Frame(main, bg=COLORS["bg_card"], bd=1, highlightbackground=COLORS["border"], highlightthickness=1)
            card.pack(fill=tk.X, pady=4, ipady=5)
            
            rb = tk.Radiobutton(card, text=f"  {info['name']}", variable=self._provider_var, value=pid,
                                font=self._f_body, fg=info["color"], bg=COLORS["bg_card"], 
                                selectcolor=COLORS["bg_dark"], activebackground=COLORS["bg_card"],
                                command=self._on_switch)
            rb.pack(side=tk.LEFT, padx=15)
            self._provider_cards[pid] = card

        self._desc_box = tk.Label(main, text=PROVIDERS["openai"]["desc"], font=self._f_body, 
                                  fg=COLORS["text_secondary"], bg=COLORS["bg_dark"], wraplength=500, justify="left")
        self._desc_box.pack(anchor="w", pady=(5, 15))

        # 3. SECURE THE LINK (API Key)
        tk.Label(main, text="STEP 2: API Credentials", font=self._f_head, 
                 fg=COLORS["text_primary"], bg=COLORS["bg_dark"]).pack(anchor="w", pady=(10, 2))
        
        self._key_link = tk.Label(main, text="Retrieve key from dashboard ↗", font=self._f_body, 
                                  fg=COLORS["accent_cyan"], bg=COLORS["bg_dark"], cursor="hand2")
        self._key_link.pack(anchor="w", pady=(0, 10))

        # The Key Entry Field
        k_frame = tk.Frame(main, bg=COLORS["bg_input"], bd=1, highlightbackground=COLORS["border"], highlightthickness=1)
        k_frame.pack(fill=tk.X, ipady=5)
        self._key_input = tk.Entry(k_frame, font=self._f_mono, bg=COLORS["bg_input"], fg="white", 
                                   insertbackground="white", borderwidth=0, show="●")
        self._key_input.pack(fill=tk.X, padx=10, pady=5)

        # 4. VOCAL CORDS (Optional Murf Key)
        tk.Label(main, text="STEP 3: Premium Vocal Engine (Optional)", font=self._f_head, 
                 fg=COLORS["text_primary"], bg=COLORS["bg_dark"]).pack(anchor="w", pady=(20, 5))
        
        m_frame = tk.Frame(main, bg=COLORS["bg_input"], bd=1, highlightbackground=COLORS["border"], highlightthickness=1)
        m_frame.pack(fill=tk.X, ipady=5)
        self._murf_input = tk.Entry(m_frame, font=self._f_mono, bg=COLORS["bg_input"], fg="white", 
                                    insertbackground="white", borderwidth=0, show="●")
        self._murf_input.pack(fill=tk.X, padx=10, pady=5)

        # 5. INITIALIZE (Submit)
        btn = tk.Button(main, text="INITIALIZE J.A.R.V.I.S.", font=self._f_head, bg=COLORS["accent_blue"], 
                        fg="white", borderwidth=0, pady=12, cursor="hand2", command=self._handle_submit)
        btn.pack(fill=tk.X, pady=(40, 0))

        # Final Update
        self._on_switch()

    def _on_switch(self):
        """Dyanmic UI update when radio selection changes."""
        pid = self._provider_var.get()
        info = PROVIDERS[pid]
        
        # Update description and highlighting
        self._desc_box.configure(text=info["desc"])
        for k, card in self._provider_cards.items():
            card.configure(highlightbackground=info["color"] if k == pid else COLORS["border"])

    def _handle_submit(self):
        """Validates input, writes to disk, and signals the main process."""
        pk = self._key_input.get().strip()
        mk = self._murf_input.get().strip()
        id = self._provider_var.get()

        if not pk:
            messagebox.showwarning("Incomplete Link", f"An API key for {PROVIDERS[id]['name']} is required.")
            return

        # Write to persistence (config.py handles the file logic)
        from config import save_to_env, reload_env
        save_to_env(id, pk, mk)
        reload_env() # Ensure the running process has the new data

        self._result = {"provider": id, "key": pk}
        self.root.destroy()

    def _on_close(self):
        """Called if user dismisses the window."""
        self._result = None
        self.root.destroy()

    def run(self):
        """Shows the dialog and returns the final config dictionary."""
        self.root.mainloop()
        return self._result
