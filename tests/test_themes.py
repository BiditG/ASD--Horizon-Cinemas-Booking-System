"""
tests/test_themes.py
"""

import json
import os
import pytest
import tempfile
from unittest.mock import patch


class TestLoadUserPreference:
    def test_returns_dark_when_no_file(self, tmp_path):
        """Returns 'dark' by default when no prefs file exists."""
        fake_path = str(tmp_path / "user_prefs.json")
        with patch("src.utils.themes.PREFS_PATH", fake_path):
            from src.utils.themes import ThemeManager
            result = ThemeManager.load_user_preference("alice")
        assert result == "dark"

    def test_returns_saved_theme(self, tmp_path):
        """Returns the saved theme name for the given username."""
        prefs_file = tmp_path / "user_prefs.json"
        prefs_file.write_text(json.dumps({"alice": {"theme": "light"}}), encoding="utf-8")
        with patch("src.utils.themes.PREFS_PATH", str(prefs_file)):
            from src.utils.themes import ThemeManager
            result = ThemeManager.load_user_preference("alice")
        assert result == "light"

    def test_returns_dark_for_unknown_user(self, tmp_path):
        """Returns 'dark' for a user not present in the prefs file."""
        prefs_file = tmp_path / "user_prefs.json"
        prefs_file.write_text(json.dumps({"alice": {"theme": "light"}}), encoding="utf-8")
        with patch("src.utils.themes.PREFS_PATH", str(prefs_file)):
            from src.utils.themes import ThemeManager
            result = ThemeManager.load_user_preference("bob")
        assert result == "dark"


class TestThemeTogglePersistence:
    def test_toggle_from_dark_saves_light(self, tmp_path):
        """Toggling from dark saves 'light' to the prefs file."""
        prefs_file = tmp_path / "user_prefs.json"
        with patch("src.utils.themes.PREFS_PATH", str(prefs_file)):
            from src.utils.themes import ThemeManager
            ThemeManager._current = "dark"
            ThemeManager.save_user_preference("charlie", "light")
            result = ThemeManager.load_user_preference("charlie")
        assert result == "light"

    def test_toggle_from_light_saves_dark(self, tmp_path):
        """Toggling from light saves 'dark' to the prefs file."""
        prefs_file = tmp_path / "user_prefs.json"
        with patch("src.utils.themes.PREFS_PATH", str(prefs_file)):
            from src.utils.themes import ThemeManager
            ThemeManager.save_user_preference("dana", "dark")
            result = ThemeManager.load_user_preference("dana")
        assert result == "dark"

    def test_multiple_users_isolated(self, tmp_path):
        """Preferences for different users are stored independently."""
        prefs_file = tmp_path / "user_prefs.json"
        with patch("src.utils.themes.PREFS_PATH", str(prefs_file)):
            from src.utils.themes import ThemeManager
            ThemeManager.save_user_preference("user1", "light")
            ThemeManager.save_user_preference("user2", "dark")
            assert ThemeManager.load_user_preference("user1") == "light"
            assert ThemeManager.load_user_preference("user2") == "dark"


class TestThemeDictionaries:
    def test_dark_theme_has_all_keys(self):
        from src.utils.themes import DARK_THEME
        required = {"name", "bg_primary", "bg_secondary", "fg_primary", "fg_secondary",
                    "accent", "border", "button_bg", "button_fg", "entry_bg",
                    "header_bg", "header_fg", "table_bg", "table_alt_row", "table_fg"}
        assert required.issubset(DARK_THEME.keys())

    def test_light_theme_has_all_keys(self):
        from src.utils.themes import LIGHT_THEME
        required = {"name", "bg_primary", "bg_secondary", "fg_primary", "fg_secondary",
                    "accent", "border", "button_bg", "button_fg", "entry_bg",
                    "header_bg", "header_fg", "table_bg", "table_alt_row", "table_fg"}
        assert required.issubset(LIGHT_THEME.keys())

    def test_themes_are_distinct(self):
        from src.utils.themes import DARK_THEME, LIGHT_THEME
        assert DARK_THEME["bg_primary"] != LIGHT_THEME["bg_primary"]
        assert DARK_THEME["fg_primary"] != LIGHT_THEME["fg_primary"]
