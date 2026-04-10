"""Integration tests for RenameDialog."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from unittest.mock import patch
from metatag.ui.rename_dialog import RenameDialog


def test_rename_dialog_initialization(qtbot):
    """Test RenameDialog can be instantiated."""
    dialog = RenameDialog()
    qtbot.add_widget(dialog)
    assert dialog.windowTitle() == "Rename Files"
    assert dialog._pattern_edit is not None
    assert dialog._preview_label is not None
    assert dialog._ok_button is not None
    assert dialog._cancel_button is not None


def test_rename_dialog_pattern_edit_updates_preview(qtbot):
    """Test that typing in pattern edit updates preview label."""
    dialog = RenameDialog()
    qtbot.add_widget(dialog)

    # Initial preview should be empty or default
    initial_text = dialog._preview_label.text()

    # Type a pattern
    qtbot.keyClicks(dialog._pattern_edit, "%artist% - %title%")

    # Wait for textChanged signal to update preview
    qtbot.wait(50)

    # Preview should have updated
    updated_text = dialog._preview_label.text()
    assert updated_text != initial_text
    assert "Artist" in updated_text
    assert "Title" in updated_text
    assert "Example:" in updated_text


def test_rename_dialog_accept_valid_pattern(qtbot):
    """Test dialog emits pattern_accepted signal with valid pattern."""
    dialog = RenameDialog()
    qtbot.add_widget(dialog)

    # Enter pattern
    qtbot.keyClicks(dialog._pattern_edit, "%artist% - %title%")

    captured_pattern = []
    dialog.pattern_accepted.connect(captured_pattern.append)

    # Click OK
    with qtbot.wait_signal(dialog.pattern_accepted) as blocker:
        qtbot.mouseClick(dialog._ok_button, Qt.MouseButton.LeftButton)

    assert captured_pattern[0] == "%artist% - %title%"
    assert dialog.pattern() == "%artist% - %title%"


def test_rename_dialog_accept_empty_pattern(qtbot):
    """Test dialog shows warning when pattern is empty."""
    dialog = RenameDialog()
    qtbot.add_widget(dialog)

    signal_called = False

    def on_signal():
        nonlocal signal_called
        signal_called = True

    dialog.pattern_accepted.connect(on_signal)

    # Ensure pattern edit is empty (default)
    assert dialog._pattern_edit.text() == ""

    # Click OK - will trigger warning dialog
    with patch.object(QMessageBox, "warning") as mock_warning:
        qtbot.mouseClick(dialog._ok_button, Qt.MouseButton.LeftButton)
        mock_warning.assert_called_once()
        assert not signal_called
        assert dialog is not None


def test_rename_dialog_cancel(qtbot):
    """Test cancel button closes dialog without emitting signal."""
    dialog = RenameDialog()
    qtbot.add_widget(dialog)

    qtbot.keyClicks(dialog._pattern_edit, "%artist% - %title%")

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


def test_rename_dialog_getter(qtbot):
    """Test pattern getter returns correct value after acceptance."""
    dialog = RenameDialog()
    qtbot.add_widget(dialog)

    qtbot.keyClicks(dialog._pattern_edit, "%track% - %title%")

    with qtbot.wait_signal(dialog.pattern_accepted):
        qtbot.mouseClick(dialog._ok_button, Qt.MouseButton.LeftButton)

    assert dialog.pattern() == "%track% - %title%"


if __name__ == "__main__":
    pytest.main([__file__])
