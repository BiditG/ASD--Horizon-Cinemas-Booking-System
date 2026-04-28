# HCBS GUI Style Guide

This document defines the visual standards for the Horizon Cinemas Booking System (HCBS) desktop application. All developers must adhere to these conventions to ensure a consistent user experience.

## 1. Colour Palette

The application uses a modern, high-contrast palette. While a light mode is available, the dark mode is the primary theme.

| Name | Hex Code | Purpose |
| :--- | :--- | :--- |
| **Primary Background (Dark)** | `#0b1220` | Main window and frame backgrounds. |
| **Primary Background (Light)** | `#f8fafc` | Secondary surfaces or light mode alternative. |
| **Secondary Surface** | `#111b2e` | Top bars, controls, and contrast surfaces. |
| **Card Surface** | `#162338` | Cards, forms, and content containers. |
| **Primary Accent** | `#4f8cff` | Primary buttons, active state highlights. |
| **Secondary Accent** | `#22c55e` | Positive feedback and success states. |
| **Warning** | `#f59e0b` | Cautions, pending statuses. |
| **Error** | `#ef4444` | Destructive actions, validation errors. |
| **Text Primary** | `#f8fafc` | Main headings and labels (on dark). |
| **Text Secondary** | `#a7b4c8` | Subtext, hints, and disabled labels. |
| **Border** | `#26344a` | Subtle separators and input outlines. |

## 2. Typography

We use clean, sans-serif fonts for maximum readability.

- **Font Family**: `Segoe UI` (Primary), `Arial` (Fallback).
- **Heading 1**: 24pt, Bold.
- **Heading 2**: 18pt, Bold.
- **Body Text**: 11pt, Regular.
- **Monospace (for references)**: `Consolas` or `Courier`, 10pt.

## 3. Widget Conventions

### Buttons
- **Padding**: 10px horizontal, 5px vertical.
- **Style**: Flat design. Primary buttons use the blue accent; secondary buttons use a dark slate.
- **States**: Slightly darker background on hover.

### Input Fields (Entry)
- **Border**: 1px solid.
- **Focus State**: Border changes to Primary Accent blue.
- **Padding**: 5px internal padding.

### Labels
- **Headings**: Use Text Primary and bold weights.
- **Body**: Use Text Primary and regular weights.
- **Helper Text**: Use Text Secondary and smaller size (9pt).

### Tables (Treeview)
- **Header**: Primary Accent background with white text.
- **Rows**: Alternating row colours for readability (`#1e293b` and `#0f172a`).
- **Selection**: Highlight row with Primary Accent.

## 4. Layout Rules

- **Minimum Window Size**: 1024x768 pixels.
- **Global Margin**: 20px around the main container.
- **Element Spacing**: 10px vertical spacing between related elements; 20px between sections.
- **Form Arrangement**: Labels should be placed above their respective input fields, left-aligned.

## 5. Tkinter Code Snippets

Use `tkinter.ttk` for a more modern look where possible.

### Applying the Theme
```python
import tkinter as tk
from tkinter import ttk

# Constants
BG_PRIMARY = "#0b1220"
BG_SECONDARY = "#111b2e"
BG_CARD = "#162338"
ACCENT = "#4f8cff"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
ERROR = "#ef4444"
TEXT_PRIMARY = "#f8fafc"
TEXT_SECONDARY = "#a7b4c8"

def apply_style():
    style = ttk.Style()
    style.theme_use('clam')
    
    # Configure Frame
    style.configure("TFrame", background=BG_PRIMARY)
    
    # Configure Label
    style.configure("TLabel", 
                    background=BG_PRIMARY, 
                    foreground=TEXT_PRIMARY, 
                    font=("Helvetica", 11))
    
    # Configure Heading
    style.configure("Header.TLabel", 
                    font=("Helvetica", 24, "bold"))
    
    # Configure Button
    style.configure("TButton", 
                    background=ACCENT, 
                    foreground="white", 
                    padding=10, 
                    font=("Segoe UI", 11, "bold"))
    style.map("TButton", background=[('active', '#3478f6')])
```

### Creating a Styled Entry
```python
# Entry widgets are better styled individually or via a custom class
entry = tk.Entry(root, 
                 bg="#1e293b", 
                 fg=TEXT_PRIMARY, 
                 insertbackground="white", 
                 relief="flat", 
                 font=("Helvetica", 11))
# Add 1px border simulation using a parent frame
```

### Striped Treeview
```python
tree = ttk.Treeview(root, columns=("id", "name"), show="headings")
tree.tag_configure('oddrow', background="#1e293b")
tree.tag_configure('evenrow', background="#0f172a")

# When inserting:
tree.insert("", "end", values=(1, "Inception"), tags=('oddrow',))
```
