"""
main.py
=======
Entry point for the Horizon Cinemas Booking System (HCBS).

Run with:
    python main.py
"""

import sys
import os
import ctypes

# Ensure the project root is on the path so 'src.*' imports resolve correctly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from tkinter import ttk
from src.gui.login_window import LoginWindow


BG_PRIMARY = "#0b1220"
BG_SECONDARY = "#111b2e"
ACCENT = "#4f8cff"
TEXT_PRIMARY = "#f8fafc"


def _configure_windows_dpi(root: tk.Tk) -> None:
    """Reduce blur on Windows by opting into per-monitor DPI scaling."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    try:
        dpi = root.winfo_fpixels("1i")
        root.tk.call("tk", "scaling", (dpi / 72.0) * 1.1)
    except Exception:
        pass


def main() -> None:
    from src.utils.waitlist_manager import init_waitlist_db
    from src.utils.loyalty_manager import init_loyalty_db
    init_waitlist_db()
    init_loyalty_db()

    root = tk.Tk()
    _configure_windows_dpi(root)
    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TNotebook', background=BG_PRIMARY, borderwidth=0)
    style.configure('TNotebook.Tab', background=BG_SECONDARY, foreground=TEXT_PRIMARY, padding=[16, 10], font=('Segoe UI', 10, 'bold'))
    style.map('TNotebook.Tab', background=[('selected', ACCENT)], foreground=[('selected', TEXT_PRIMARY)])
    style.configure('TButton', background=ACCENT, foreground='white', padding=10, font=('Segoe UI', 10, 'bold'))
    style.map('TButton', background=[('active', '#3478f6')])
    style.configure('TCombobox', fieldbackground=BG_SECONDARY, background=BG_SECONDARY, foreground=TEXT_PRIMARY, arrowcolor=TEXT_PRIMARY)
    style.map('TCombobox',
              fieldbackground=[('readonly', BG_SECONDARY), ('disabled', BG_SECONDARY), ('focus', BG_SECONDARY), ('active', BG_SECONDARY)],
              foreground=[('readonly', TEXT_PRIMARY), ('disabled', TEXT_PRIMARY), ('focus', TEXT_PRIMARY), ('active', TEXT_PRIMARY)])
    style.configure('Treeview', background=BG_SECONDARY, foreground=TEXT_PRIMARY, fieldbackground=BG_SECONDARY, borderwidth=0, rowheight=26)
    style.configure('Treeview.Heading', background=BG_SECONDARY, foreground=TEXT_PRIMARY, font=('Segoe UI', 10, 'bold'))
    style.map('Treeview', background=[('selected', ACCENT)], foreground=[('selected', TEXT_PRIMARY)])

    root.option_add('*TCombobox*Listbox.background', BG_SECONDARY, 100)
    root.option_add('*TCombobox*Listbox.foreground', TEXT_PRIMARY, 100)
    root.option_add('*TCombobox*Listbox.selectBackground', ACCENT, 100)
    root.option_add('*TCombobox*Listbox.selectForeground', TEXT_PRIMARY, 100)
    root.option_add('*Button.background', BG_SECONDARY)
    root.option_add('*Button.foreground', TEXT_PRIMARY)
    root.option_add('*Entry.background', BG_SECONDARY)
    root.option_add('*Entry.foreground', TEXT_PRIMARY)
    root.option_add('*Entry.insertBackground', TEXT_PRIMARY)

    # Aggressive fallback for Windows native listboxes
    try:
        root.tk_setPalette(background=BG_PRIMARY, foreground=TEXT_PRIMARY, activeBackground=ACCENT, activeForeground=TEXT_PRIMARY)
    except Exception:
        pass
    
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
