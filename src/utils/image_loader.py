"""
src/utils/image_loader.py
=========================
Poster image loading utility for the Horizon Cinemas Booking System (HCBS).

Provides a single public function, ``load_poster()``, that handles all image
loading, resizing, and error fallback logic so GUI code stays clean.

Dependencies
------------
- Pillow (PIL): ``pip install Pillow``

Notes
-----
- All PhotoImage objects returned by this module are Tkinter-compatible.
- Callers MUST keep a reference to every returned PhotoImage (e.g. in a list)
  to prevent Python's garbage collector from deleting them while the widget
  still needs them.  Typical pattern::

      self.poster_images = []
      photo = load_poster(film.poster_path)
      self.poster_images.append(photo)
      label.config(image=photo)
"""

import os
from typing import Optional

try:
    from PIL import Image, ImageDraw, ImageFont, ImageTk
    _PIL_OK = True
except ImportError:
    _PIL_OK = False


# ── Module-level constants ────────────────────────────────────────────────────

_PLACEHOLDER_BG   = (30, 41, 59)      # BG2 dark slate blue (matches HCBS theme)
_PLACEHOLDER_FG   = (148, 163, 184)   # TEXT2 muted slate
_PLACEHOLDER_BORDER = (51, 65, 85)    # BORDER colour


def load_poster(
    poster_path: Optional[str],
    size: tuple[int, int] = (80, 120),
) -> "ImageTk.PhotoImage":
    """
    Load a film poster image and return a Tkinter-compatible PhotoImage.

    Attempts to open the image at ``poster_path``, resize it to ``size``
    while preserving aspect ratio, and convert it for use in a ``tk.Label``.

    If the path is ``None``, the file does not exist, or any exception is
    raised during loading, a themed placeholder image is returned instead.
    The placeholder is a dark slate rectangle with the text "No Poster"
    and a film-reel icon drawn using Pillow's ImageDraw.

    Parameters
    ----------
    poster_path : str or None
        Absolute or relative path to the poster image file.  If relative,
        it is resolved from the project root (two directories above this file).
    size : tuple[int, int]
        ``(width, height)`` of the output image.  Defaults to ``(80, 120)``.

    Returns
    -------
    ImageTk.PhotoImage
        A Tkinter-compatible image object.  The caller must retain a reference
        to prevent garbage collection.

    Raises
    ------
    ImportError
        If Pillow is not installed.  Install with ``pip install Pillow``.

    Examples
    --------
    ::

        photo = load_poster(film.poster_path, size=(90, 130))
        self.poster_images.append(photo)          # keep reference!
        poster_label.config(image=photo, text="")
    """
    if not _PIL_OK:
        raise ImportError(
            "Pillow is required for poster loading. "
            "Install it with: pip install Pillow"
        )

    # Resolve relative paths from the project root
    if poster_path and not os.path.isabs(poster_path):
        _project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..')
        )
        poster_path = os.path.join(_project_root, poster_path)

    # ── Attempt to load the real poster ──────────────────────────────────────
    if poster_path and os.path.isfile(poster_path):
        try:
            img = Image.open(poster_path).convert("RGB")
            img.thumbnail(size, Image.LANCZOS)

            # If thumbnail is smaller than the target (aspect ratio), paste
            # it centred on a solid background so the label stays the right size
            canvas = Image.new("RGB", size, _PLACEHOLDER_BG)
            offset_x = (size[0] - img.width)  // 2
            offset_y = (size[1] - img.height) // 2
            canvas.paste(img, (offset_x, offset_y))

            return ImageTk.PhotoImage(canvas)

        except Exception:
            pass   # fall through to placeholder

    # ── Build a themed placeholder ────────────────────────────────────────────
    return _make_placeholder(size)


def _make_placeholder(size: tuple[int, int]) -> "ImageTk.PhotoImage":
    """
    Generate a styled 'No Poster' placeholder image.

    Draws a dark background, rounded-corner border hint, film-strip
    side bars, and the text "No Poster" centred in the image.

    Parameters
    ----------
    size : tuple[int, int]
        ``(width, height)`` in pixels.

    Returns
    -------
    ImageTk.PhotoImage
        The rendered placeholder as a Tkinter-compatible image.
    """
    w, h   = size
    img    = Image.new("RGB", (w, h), _PLACEHOLDER_BG)
    draw   = ImageDraw.Draw(img)

    # ── Outer border rectangle ────────────────────────────────────────────────
    draw.rectangle([1, 1, w - 2, h - 2], outline=_PLACEHOLDER_BORDER, width=2)

    # ── Film-strip side bars (left and right) ─────────────────────────────────
    bar_w  = max(6, w // 9)
    hole_h = max(4, h // 14)
    hole_w = max(4, bar_w - 4)
    gap    = hole_h + 4

    for x_off in (2, w - bar_w - 2):
        draw.rectangle([x_off, 2, x_off + bar_w, h - 2],
                       fill=_PLACEHOLDER_BORDER)
        y = 6
        while y + hole_h < h - 4:
            draw.rectangle(
                [x_off + 2, y, x_off + 2 + hole_w, y + hole_h],
                fill=_PLACEHOLDER_BG
            )
            y += gap

    # ── Centre icon "▶" ──────────────────────────────────────────────────────
    cx, cy = w // 2, h // 2 - 10
    icon_size = max(10, min(w, h) // 5)
    draw.polygon(
        [
            (cx - icon_size // 2, cy - icon_size // 2),
            (cx + icon_size // 2, cy),
            (cx - icon_size // 2, cy + icon_size // 2),
        ],
        fill=_PLACEHOLDER_FG
    )

    # ── "No Poster" text ──────────────────────────────────────────────────────
    # Try to use a TrueType font; fall back to the built-in bitmap font
    font = None
    try:
        font = ImageFont.truetype("arial.ttf", size=max(9, w // 9))
    except (IOError, AttributeError):
        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

    label_text = "No Poster"
    text_y     = cy + icon_size // 2 + 6

    if font:
        try:
            bbox = draw.textbbox((0, 0), label_text, font=font)
            text_w = bbox[2] - bbox[0]
        except AttributeError:
            text_w = len(label_text) * 6   # rough fallback for older Pillow
        draw.text(
            ((w - text_w) // 2, text_y),
            label_text,
            fill=_PLACEHOLDER_FG,
            font=font
        )
    else:
        draw.text((w // 4, text_y), label_text, fill=_PLACEHOLDER_FG)

    return ImageTk.PhotoImage(img)
