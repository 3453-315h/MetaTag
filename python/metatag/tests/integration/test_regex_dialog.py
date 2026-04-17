"""Integration tests for RegexDialog."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QApplication
from unittest.mock import patch
from metatag.ui.regex_dialog import RegexDialog


def test_regex_dialog_initialization(qtbot):
    """Test RegexDialog can be instantiated."""
    dialog = RegexDialog()
    qtbot.add_widget(dialog)
    assert dialog.windowTitle() == "Find & Replace"
    assert dialog._pattern_edit is not None
    assert dialog._replacement_edit is not None
    assert dialog._field_list is not None
    assert dialog._case_check is not None
    assert dialog._ok_button is not None
    assert dialog._cancel_button is not None


def test_regex_dialog_accept_valid_input(qtbot):
    """Test dialog emits pattern_accepted signal with valid input."""
    dialog = RegexDialog()
    qtbot.add_widget(dialog)

    # Enter pattern and replacement
    qtbot.keyClicks(dialog._pattern_edit, r"\d{4}")
    qtbot.keyClicks(dialog._replacement_edit, "YEAR")

    # Select some fields
    dialog._field_list.item(0).setSelected(True)  # Artist
    dialog._field_list.item(1).setSelected(True)  # Album

    # Capture emitted signal
    captured_pattern = []
    captured_replacement = []
    captured_fields = []
    captured_case = []

    def capture(pattern, replacement, fields, case_sensitive):
        captured_pattern.append(pattern)
        captured_replacement.append(replacement)
        captured_fields.append(fields)
        captured_case.append(case_sensitive)

    dialog.pattern_accepted.connect(capture)

    # Click OK
    with qtbot.wait_signal(dialog.pattern_accepted) as blocker:
        qtbot.mouseClick(dialog._ok_button, Qt.MouseButton.LeftButton)

    # Verify signal data
    assert captured_pattern[0] == r"\d{4}"
    assert captured_replacement[0] == "YEAR"
    assert "artist" in captured_fields[0]
    assert "album" in captured_fields[0]
    assert captured_case[0] is True  # default case sensitive checked


def test_regex_dialog_accept_no_pattern(qtbot):
    """Test dialog shows warning when pattern is empty."""
    dialog = RegexDialog()
    qtbot.add_widget(dialog)

    signal_called = False

    def on_signal():
        nonlocal signal_called
        signal_called = True

    dialog.pattern_accepted.connect(on_signal)

    # Don't enter pattern, click OK
    with patch.object(QMessageBox, "warning") as mock_warning:
        qtbot.mouseClick(dialog._ok_button, Qt.MouseButton.LeftButton)
        # Should have called warning
        mock_warning.assert_called_once()
        # Signal should NOT have been emitted
        assert not signal_called
        # Dialog should still exist (not closed)
        assert dialog is not None


def test_regex_dialog_accept_no_fields_selected(qtbot):
    """Test dialog shows warning when no fields selected."""
    dialog = RegexDialog()
    qtbot.add_widget(dialog)

    signal_called = False

    def on_signal():
        nonlocal signal_called
        signal_called = True

    dialog.pattern_accepted.connect(on_signal)

    # Enter pattern but don't select fields
    qtbot.keyClicks(dialog._pattern_edit, r"\d{4}")

    # Click OK
    with patch.object(QMessageBox, "warning") as mock_warning:
        qtbot.mouseClick(dialog._ok_button, Qt.MouseButton.LeftButton)
        mock_warning.assert_called_once()
        assert not signal_called
        assert dialog is not None


def test_regex_dialog_case_sensitive_toggle(qtbot):
    """Test case sensitive checkbox affects emitted signal."""
    dialog = RegexDialog()
    qtbot.add_widget(dialog)

    qtbot.keyClicks(dialog._pattern_edit, r"\d{4}")
    dialog._field_list.item(0).setSelected(True)

    # Uncheck case sensitive
    dialog._case_check.setChecked(False)

    captured_case = []
    dialog.pattern_accepted.connect(lambda p, r, f, c: captured_case.append(c))

    with qtbot.wait_signal(dialog.pattern_accepted):
        qtbot.mouseClick(dialog._ok_button, Qt.MouseButton.LeftButton)

    assert captured_case[0] is False


def test_regex_dialog_cancel(qtbot):
    """Test cancel button closes dialog without emitting signal."""
    dialog = RegexDialog()
    qtbot.add_widget(dialog)

    qtbot.keyClicks(dialog._pattern_edit, r"\d{4}")
    dialog._field_list.item(0).setSelected(True)

    signal_emitted = False

    def on_signal():
        nonlocal signal_emitted
        signal_emitted = True

    dialog.pattern_accepted.connect(on_signal)

    # Click cancel
    qtbot.mouseClick(dialog._cancel_button, Qt.MouseButton.LeftButton)

    # Dialog should be closed
    assert not dialog.isVisible()
    # Signal should NOT have been emitted
    assert not signal_emitted


def test_regex_dialog_getters(qtbot):
    """Test getter methods return correct values after acceptance."""
    dialog = RegexDialog()
    qtbot.add_widget(dialog)

    qtbot.keyClicks(dialog._pattern_edit, r"\d{4}")
    qtbot.keyClicks(dialog._replacement_edit, "YEAR")
    dialog._field_list.item(0).setSelected(True)
    dialog._case_check.setChecked(False)

    # Accept dialog
    with qtbot.wait_signal(dialog.pattern_accepted):
        qtbot.mouseClick(dialog._ok_button, Qt.MouseButton.LeftButton)

    # Check getters
    assert dialog.pattern() == r"\d{4}"
    assert dialog.replacement() == "YEAR"
    assert dialog.selected_fields() == ["artist"]
    assert dialog.case_sensitive() is False


if __name__ == "__main__":
    pytest.main([__file__])
