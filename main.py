"""
main.py
=======
Entry point for the Horizon Cinemas Booking System (HCBS).

Run with:
    python main.py
"""

import sys
import os

# Ensure the project root is on the path so 'src.*' imports resolve correctly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from src.gui.login_window import LoginWindow


def main() -> None:
    from src.utils.waitlist_manager import init_waitlist_db
    from src.utils.loyalty_manager import init_loyalty_db
    init_waitlist_db()
    init_loyalty_db()

    root = tk.Tk()
    
    # Globally fix Tkinter Combobox dropdown list styling for the 'clam' theme
    BG2 = "#1e293b"
    TEXT = "#f8fafc"
    ACCENT = "#1e40af"
    root.option_add('*TCombobox*Listbox.background', BG2)
    root.option_add('*TCombobox*Listbox.foreground', TEXT)
    root.option_add('*TCombobox*Listbox.selectBackground', ACCENT)
    root.option_add('*TCombobox*Listbox.selectForeground', TEXT)
    
    # Aggressive fallback for Windows native listboxes
    try:
        root.tk_setPalette(background=BG2, foreground=TEXT, activeBackground=ACCENT, activeForeground=TEXT)
    except Exception:
        pass
    
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
