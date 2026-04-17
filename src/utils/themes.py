"""
src/utils/themes.py
===================
Theme definitions and ThemeManager for HCBS dark/light mode support.
"""

import json
import os
import tkinter as tk
from tkinter import ttk

# ── Preference file path ───────────────────────────────────────────────────────
_THIS_DIR    = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, '..', '..'))
PREFS_PATH   = os.path.join(_PROJECT_ROOT, 'user_prefs.json')

# ── Theme dictionaries ─────────────────────────────────────────────────────────
DARK_THEME = {
    "name":          "dark",
    "bg_primary":    "#0f172a",
    "bg_secondary":  "#1e293b",
    "bg_card":       "#162032",
    "fg_primary":    "#f8fafc",
    "fg_secondary":  "#94a3b8",
    "accent":        "#1e40af",
    "accent_hover":  "#1e3a8a",
    "border":        "#334155",
    "button_bg":     "#1e293b",
    "button_fg":     "#f8fafc",
    "entry_bg":      "#1e293b",
    "entry_fg":      "#f8fafc",
    "header_bg":     "#1e293b",
    "header_fg":     "#f8fafc",
    "table_bg":      "#0f172a",
    "table_alt_row": "#162032",
    "table_fg":      "#f8fafc",
    "success":       "#16a34a",
    "error":         "#dc2626",
    "warning":       "#f59e0b",
}

LIGHT_THEME = {
    "name":          "light",
    "bg_primary":    "#f1f5f9",
    "bg_secondary":  "#e2e8f0",
    "bg_card":       "#ffffff",
    "fg_primary":    "#0f172a",
    "fg_secondary":  "#475569",
    "accent":        "#1e40af",
    "accent_hover":  "#1e3a8a",
    "border":        "#cbd5e1",
    "button_bg":     "#e2e8f0",
    "button_fg":     "#0f172a",
    "entry_bg":      "#ffffff",
    "entry_fg":      "#0f172a",
    "header_bg":     "#e2e8f0",
    "header_fg":     "#0f172a",
    "table_bg":      "#f8fafc",
    "table_alt_row": "#e2e8f0",
    "table_fg":      "#0f172a",
    "success":       "#16a34a",
    "error":         "#dc2626",
    "warning":       "#d97706",
}

THEMES = {"dark": DARK_THEME, "light": LIGHT_THEME}


class ThemeManager:
    """
    Manages light/dark theming for the application.
    Persists user preference to user_prefs.json.
    """

    _current: str = "dark"   # global current theme name

    @classmethod
    def current_theme(cls) -> dict:
        return THEMES.get(cls._current, DARK_THEME)

    @classmethod
    def load_user_preference(cls, username: str) -> str:
        """Load saved theme preference ('dark' or 'light') for the given username."""
        try:
            if os.path.exists(PREFS_PATH):
                with open(PREFS_PATH, "r", encoding="utf-8") as f:
                    prefs = json.load(f)
                return prefs.get(username, {}).get("theme", "dark")
        except Exception:
            pass
        return "dark"

    @classmethod
    def save_user_preference(cls, username: str, theme_name: str) -> None:
        """Persist theme preference for the given username."""
        prefs = {}
        try:
            if os.path.exists(PREFS_PATH):
                with open(PREFS_PATH, "r", encoding="utf-8") as f:
                    prefs = json.load(f)
        except Exception:
            pass
        prefs.setdefault(username, {})["theme"] = theme_name
        try:
            with open(PREFS_PATH, "w", encoding="utf-8") as f:
                json.dump(prefs, f, indent=2)
        except Exception as e:
            print(f"[ThemeManager] Could not save preferences: {e}")

    @classmethod
    def apply_theme(cls, root_widget: tk.Widget, theme: dict) -> None:
        """
        Recursively walk all widgets from root_widget and apply colours
        from the given theme dict. Handles standard Tkinter and ttk widgets.
        """
        cls._current = theme["name"]
        cls._apply_ttk_styles(theme)
        cls._walk_and_apply(root_widget, theme)

    @classmethod
    def toggle_theme(cls, root_widget: tk.Widget, username: str = "") -> dict:
        """Switch between dark and light, persist preference, return new theme."""
        new_name  = "light" if cls._current == "dark" else "dark"
        new_theme = THEMES[new_name]
        cls.apply_theme(root_widget, new_theme)
        if username:
            cls.save_user_preference(username, new_name)
        return new_theme

    # ── Internal helpers ───────────────────────────────────────────────────────

    @classmethod
    def _walk_and_apply(cls, widget: tk.Widget, theme: dict) -> None:
        """Recursively apply theme colours to widget and all its descendants."""
        wtype = widget.winfo_class()

        try:
            if wtype in ("Frame", "Toplevel", "Tk", "Labelframe"):
                widget.configure(bg=theme["bg_primary"])

            elif wtype == "Label":
                widget.configure(bg=widget.master.cget("bg") if widget.master else theme["bg_primary"],
                                 fg=theme["fg_primary"])

            elif wtype == "Button":
                widget.configure(bg=theme["button_bg"], fg=theme["button_fg"],
                                 activebackground=theme["accent"],
                                 activeforeground=theme["fg_primary"])

            elif wtype in ("Entry", "Spinbox"):
                widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"],
                                 insertbackground=theme["fg_primary"],
                                 highlightbackground=theme["border"])

            elif wtype == "Text":
                widget.configure(bg=theme["entry_bg"], fg=theme["entry_fg"],
                                 insertbackground=theme["fg_primary"])

            elif wtype == "Listbox":
                widget.configure(bg=theme["table_bg"], fg=theme["table_fg"],
                                 selectbackground=theme["accent"],
                                 selectforeground=theme["fg_primary"])

            elif wtype == "Canvas":
                widget.configure(bg=theme["bg_primary"])

        except Exception:
            pass  # Some widgets may reject certain options silently

        # Recurse into children
        for child in widget.winfo_children():
            cls._walk_and_apply(child, theme)

    @classmethod
    def _apply_ttk_styles(cls, theme: dict) -> None:
        """Apply theme to all ttk widget styles globally."""
        style = ttk.Style()

        style.configure(".", background=theme["bg_secondary"],
                         foreground=theme["fg_primary"],
                         fieldbackground=theme["entry_bg"],
                         bordercolor=theme["border"],
                         troughcolor=theme["bg_primary"],
                         selectbackground=theme["accent"],
                         selectforeground=theme["fg_primary"])

        style.configure("TFrame",      background=theme["bg_primary"])
        style.configure("TLabel",      background=theme["bg_primary"],  foreground=theme["fg_primary"])
        style.configure("TButton",     background=theme["button_bg"],   foreground=theme["button_fg"])
        style.configure("TEntry",      fieldbackground=theme["entry_bg"], foreground=theme["entry_fg"])
        style.configure("TCombobox",   fieldbackground=theme["entry_bg"], foreground=theme["entry_fg"],
                         background=theme["entry_bg"])
        style.configure("TSpinbox",    fieldbackground=theme["entry_bg"], foreground=theme["entry_fg"])
        style.configure("TNotebook",   background=theme["bg_secondary"])
        style.configure("TNotebook.Tab", background=theme["button_bg"], foreground=theme["fg_primary"],
                         padding=[16, 8])
        style.map("TNotebook.Tab",
                  background=[("selected", theme["accent"])],
                  foreground=[("selected", theme["fg_primary"])])
        style.configure("Treeview",
                         background=theme["table_bg"],
                         foreground=theme["table_fg"],
                         fieldbackground=theme["table_bg"],
                         rowheight=25)
        style.configure("Treeview.Heading",
                         background=theme["header_bg"],
                         foreground=theme["header_fg"],
                         font=("Helvetica", 10, "bold"))
        style.map("Treeview", background=[("selected", theme["accent"])],
                  foreground=[("selected", theme["fg_primary"])])
        style.configure("TRadiobutton", background=theme["bg_card"],
                         foreground=theme["fg_primary"])
        style.configure("TCheckbutton", background=theme["bg_card"],
                         foreground=theme["fg_primary"])
        style.configure("TScrollbar",   background=theme["bg_secondary"],
                         troughcolor=theme["bg_primary"])
