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
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
