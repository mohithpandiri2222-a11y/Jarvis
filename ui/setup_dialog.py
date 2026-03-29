# ============================================================
# JARVIS — Setup Dialog (ui/setup_dialog.py)
# ============================================================
# Premium dark-themed tkinter dialog shown on first launch.
# Lets the user pick their LLM provider (OpenAI / Claude / Gemini)
# and enter their API key. Saves to .env via config.save_to_env().
# ============================================================

import sys
import tkinter as tk
from tkinter import font as tkfont, messagebox
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ═══════════════════════════════════════════════════════════════
# COLOUR PALETTE — Matching the main GUI theme
# ═══════════════════════════════════════════════════════════════
COLORS = {
    "bg_dark":        "#0a0a0f",
    "bg_panel":       "#111118",
    "bg_card":        "#16161f",
    "bg_input":       "#1c1c28",
    "bg_input_focus": "#22223a",
    "accent_blue":    "#3b82f6",
    "accent_cyan":    "#06b6d4",
    "accent_green":   "#10b981",
    "accent_purple":  "#8b5cf6",
    "accent_orange":  "#f97316",
    "accent_red":     "#ef4444",
    "text_primary":   "#e2e8f0",
    "text_secondary": "#94a3b8",
    "text_dim":       "#64748b",
    "border":         "#1e293b",
    "border_focus":   "#3b82f6",
    "white":          "#ffffff",
}

# Provider info
PROVIDERS = {
    "openai": {
        "name": "OpenAI",
        "model": "GPT-4o",
        "color": "#10b981",
        "desc": "Powered by GPT-4o — fast, smart, great all-rounder",
        "url": "https://platform.openai.com/api-keys",
        "prefix": "sk-",
    },
    "claude": {
        "name": "Anthropic Claude",
        "model": "Claude Sonnet",
        "color": "#f97316",
        "desc": "Powered by Claude — excellent reasoning and nuance",
        "url": "https://console.anthropic.com/settings/keys",
        "prefix": "sk-ant-",
    },
    "gemini": {
        "name": "Google Gemini",
        "model": "Gemini 2.0 Flash",
        "color": "#3b82f6",
        "desc": "Powered by Gemini — Google's frontier model, fast",
        "url": "https://aistudio.google.com/apikey",
        "prefix": "AI",
    },
}

# Cross-platform font
_FONT_SANS = "Segoe UI" if sys.platform == "win32" else "Helvetica"


class SetupDialog:
    """
    Premium JARVIS setup dialog.

    Usage:
        dialog = SetupDialog()
        result = dialog.run()  # Blocking — returns dict or None

    Returns:
        {"provider": "openai", "api_key": "sk-...", "murf_key": "..."} or None
    """

    def __init__(self):
        self._result = None
        self._selected_provider = tk.StringVar(value="openai")

        # ── Root Window ──────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("J.A.R.V.I.S. — Initial Setup")
        self.root.geometry("620x720")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg_dark"])

        # Center on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 310
        y = (self.root.winfo_screenheight() // 2) - 360
        self.root.geometry(f"620x720+{x}+{y}")

        # Fonts
        self._font_title = tkfont.Font(family=_FONT_SANS, size=22, weight="bold")
        self._font_subtitle = tkfont.Font(family=_FONT_SANS, size=11)
        self._font_heading = tkfont.Font(family=_FONT_SANS, size=13, weight="bold")
        self._font_body = tkfont.Font(family=_FONT_SANS, size=10)
        self._font_small = tkfont.Font(family=_FONT_SANS, size=9)
        self._font_input = tkfont.Font(family="Consolas" if sys.platform == "win32" else "Courier", size=10)
        self._font_button = tkfont.Font(family=_FONT_SANS, size=12, weight="bold")
        self._font_radio = tkfont.Font(family=_FONT_SANS, size=11)

        # Build UI
        self._build_ui()

        # Handle close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        """Builds the complete setup dialog UI."""
        # ── Main scrollable container ────────────────────────
        container = tk.Frame(self.root, bg=COLORS["bg_dark"])
        container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)

        # ── Header ───────────────────────────────────────────
        header = tk.Frame(container, bg=COLORS["bg_dark"])
        header.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            header, text="J.A.R.V.I.S.",
            font=self._font_title,
            fg=COLORS["accent_blue"],
            bg=COLORS["bg_dark"],
        ).pack(anchor="w")

        tk.Label(
            header, text="Welcome, Bro. Let's get you set up.",
            font=self._font_subtitle,
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_dark"],
        ).pack(anchor="w", pady=(2, 0))

        # Separator
        tk.Frame(container, bg=COLORS["border"], height=1).pack(fill=tk.X, pady=(10, 15))

        # ── Provider Selection ───────────────────────────────
        tk.Label(
            container, text="Choose your AI Provider",
            font=self._font_heading,
            fg=COLORS["text_primary"],
            bg=COLORS["bg_dark"],
        ).pack(anchor="w", pady=(0, 8))

        # Provider radio cards
        self._provider_frames = {}
        for pid, info in PROVIDERS.items():
            frame = tk.Frame(
                container, bg=COLORS["bg_card"],
                highlightbackground=COLORS["border"],
                highlightthickness=1,
                cursor="hand2",
            )
            frame.pack(fill=tk.X, pady=3, ipady=8)

            inner = tk.Frame(frame, bg=COLORS["bg_card"])
            inner.pack(fill=tk.X, padx=12, pady=2)

            rb = tk.Radiobutton(
                inner, text=f"  {info['name']}",
                variable=self._selected_provider,
                value=pid,
                font=self._font_radio,
                fg=info["color"],
                bg=COLORS["bg_card"],
                selectcolor=COLORS["bg_dark"],
                activebackground=COLORS["bg_card"],
                activeforeground=info["color"],
                indicatoron=True,
                command=self._on_provider_change,
            )
            rb.pack(side=tk.LEFT)

            model_label = tk.Label(
                inner, text=info["model"],
                font=self._font_small,
                fg=COLORS["text_dim"],
                bg=COLORS["bg_card"],
            )
            model_label.pack(side=tk.RIGHT, padx=(0, 5))

            self._provider_frames[pid] = frame

            # Make the entire frame clickable
            for widget in [frame, inner, model_label]:
                widget.bind("<Button-1>", lambda e, p=pid: self._select_provider(p))

        # Provider description
        self._provider_desc = tk.Label(
            container,
            text=PROVIDERS["openai"]["desc"],
            font=self._font_small,
            fg=COLORS["text_dim"],
            bg=COLORS["bg_dark"],
        )
        self._provider_desc.pack(anchor="w", pady=(5, 10))

        # Separator
        tk.Frame(container, bg=COLORS["border"], height=1).pack(fill=tk.X, pady=(5, 15))

        # ── API Key Input ────────────────────────────────────
        self._key_label = tk.Label(
            container, text="OpenAI API Key",
            font=self._font_heading,
            fg=COLORS["text_primary"],
            bg=COLORS["bg_dark"],
        )
        self._key_label.pack(anchor="w", pady=(0, 5))

        self._key_url_label = tk.Label(
            container,
            text=f"Get yours at: {PROVIDERS['openai']['url']}",
            font=self._font_small,
            fg=COLORS["accent_cyan"],
            bg=COLORS["bg_dark"],
            cursor="hand2",
        )
        self._key_url_label.pack(anchor="w", pady=(0, 8))

        key_frame = tk.Frame(
            container, bg=COLORS["bg_input"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        key_frame.pack(fill=tk.X, ipady=4)

        self._key_entry = tk.Entry(
            key_frame,
            font=self._font_input,
            bg=COLORS["bg_input"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            borderwidth=0,
            highlightthickness=0,
            show="•",
        )
        self._key_entry.pack(fill=tk.X, padx=10, pady=6)

        # Show/hide toggle
        self._show_key = False
        toggle_frame = tk.Frame(container, bg=COLORS["bg_dark"])
        toggle_frame.pack(anchor="w", pady=(4, 0))

        self._toggle_btn = tk.Label(
            toggle_frame, text="👁  Show key",
            font=self._font_small,
            fg=COLORS["text_dim"],
            bg=COLORS["bg_dark"],
            cursor="hand2",
        )
        self._toggle_btn.pack(side=tk.LEFT)
        self._toggle_btn.bind("<Button-1>", self._toggle_key_visibility)

        # Separator
        tk.Frame(container, bg=COLORS["border"], height=1).pack(fill=tk.X, pady=(15, 15))

        # ── Murf TTS Key (Optional) ──────────────────────────
        tk.Label(
            container, text="Murf TTS Key  (optional)",
            font=self._font_heading,
            fg=COLORS["text_primary"],
            bg=COLORS["bg_dark"],
        ).pack(anchor="w", pady=(0, 3))

        tk.Label(
            container,
            text="For premium AI voice. Skip to use free offline voice instead.",
            font=self._font_small,
            fg=COLORS["text_dim"],
            bg=COLORS["bg_dark"],
        ).pack(anchor="w", pady=(0, 8))

        murf_frame = tk.Frame(
            container, bg=COLORS["bg_input"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        murf_frame.pack(fill=tk.X, ipady=4)

        self._murf_entry = tk.Entry(
            murf_frame,
            font=self._font_input,
            bg=COLORS["bg_input"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["text_primary"],
            borderwidth=0,
            highlightthickness=0,
            show="•",
        )
        self._murf_entry.pack(fill=tk.X, padx=10, pady=6)

        # ── Launch Button ────────────────────────────────────
        btn_frame = tk.Frame(container, bg=COLORS["bg_dark"])
        btn_frame.pack(fill=tk.X, pady=(25, 5))

        self._launch_btn = tk.Button(
            btn_frame,
            text="Launch JARVIS",
            font=self._font_button,
            bg=COLORS["accent_blue"],
            fg=COLORS["white"],
            activebackground=COLORS["accent_cyan"],
            activeforeground=COLORS["white"],
            borderwidth=0,
            padx=30,
            pady=10,
            cursor="hand2",
            command=self._on_launch,
        )
        self._launch_btn.pack(fill=tk.X, ipady=2)

        # Hover effect
        self._launch_btn.bind("<Enter>",
            lambda e: self._launch_btn.configure(bg=COLORS["accent_cyan"]))
        self._launch_btn.bind("<Leave>",
            lambda e: self._launch_btn.configure(bg=COLORS["accent_blue"]))

        # Footer
        tk.Label(
            container,
            text="Your keys are stored locally in .env and never sent anywhere except the provider.",
            font=self._font_small,
            fg=COLORS["text_dim"],
            bg=COLORS["bg_dark"],
        ).pack(pady=(8, 0))

        # Highlight the default provider
        self._update_provider_highlight()

    # ═══════════════════════════════════════════════════════════
    # EVENT HANDLERS
    # ═══════════════════════════════════════════════════════════

    def _select_provider(self, provider_id: str):
        """Called when a provider card is clicked."""
        self._selected_provider.set(provider_id)
        self._on_provider_change()

    def _on_provider_change(self):
        """Update UI when provider selection changes."""
        pid = self._selected_provider.get()
        info = PROVIDERS[pid]

        # Update labels
        self._key_label.configure(text=f"{info['name']} API Key")
        self._key_url_label.configure(text=f"Get yours at: {info['url']}")
        self._provider_desc.configure(text=info["desc"])

        # Highlight selected card
        self._update_provider_highlight()

    def _update_provider_highlight(self):
        """Highlight the selected provider card."""
        pid = self._selected_provider.get()
        for key, frame in self._provider_frames.items():
            if key == pid:
                frame.configure(
                    highlightbackground=PROVIDERS[key]["color"],
                    highlightthickness=2,
                )
            else:
                frame.configure(
                    highlightbackground=COLORS["border"],
                    highlightthickness=1,
                )

    def _toggle_key_visibility(self, event=None):
        """Toggle showing/hiding the API key."""
        self._show_key = not self._show_key
        if self._show_key:
            self._key_entry.configure(show="")
            self._toggle_btn.configure(text="🔒  Hide key")
        else:
            self._key_entry.configure(show="•")
            self._toggle_btn.configure(text="👁  Show key")

    def _on_launch(self):
        """Validate and save when Launch is clicked."""
        api_key = self._key_entry.get().strip()
        murf_key = self._murf_entry.get().strip()
        provider = self._selected_provider.get()

        # Validate — API key is required
        if not api_key:
            messagebox.showerror(
                "API Key Required",
                f"Please enter your {PROVIDERS[provider]['name']} API key.\n\n"
                f"Get one at: {PROVIDERS[provider]['url']}",
                parent=self.root,
            )
            return

        # Basic format check
        if len(api_key) < 10:
            messagebox.showerror(
                "Invalid Key",
                "That doesn't look like a valid API key. Please check and try again.",
                parent=self.root,
            )
            return

        # Save to .env
        from config import save_to_env, reload_env
        save_to_env(provider, api_key, murf_key)
        reload_env()

        self._result = {
            "provider": provider,
            "api_key": api_key,
            "murf_key": murf_key,
        }

        self.root.destroy()

    def _on_close(self):
        """User closed the dialog without completing setup."""
        self._result = None
        self.root.destroy()

    # ═══════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════

    def run(self) -> dict | None:
        """
        Shows the setup dialog (blocking).

        Returns:
            Dict with {provider, api_key, murf_key} on success, or None if cancelled.
        """
        self.root.mainloop()
        return self._result


# ── Self-test ────────────────────────────────────────────────
if __name__ == "__main__":
    print("[SETUP] Testing setup dialog standalone...")
    dialog = SetupDialog()
    result = dialog.run()
    if result:
        print(f"  Provider: {result['provider']}")
        print(f"  API Key:  {result['api_key'][:8]}...")
        print(f"  Murf Key: {result['murf_key'][:8] if result['murf_key'] else 'Not set'}...")
    else:
        print("  Setup cancelled.")
