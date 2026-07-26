"""Integrated audio player widget for MetaTag."""

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal, Slot, QUrl
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

class AudioPlayer(QWidget):
    """Miniature audio player for track preview."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self._player = QMediaPlayer(self)
        self._audio_output = QAudioOutput(self)
        self._player.setAudioOutput(self._audio_output)
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self._play_button = QPushButton("Play")
        self._play_button.setFixedWidth(60)
        
        self._time_label = QLabel("0:00 / 0:00")
        self._time_label.setFixedWidth(80)
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._seek_slider = QSlider(Qt.Orientation.Horizontal)
        self._seek_slider.setEnabled(False)
        
        self._volume_slider = QSlider(Qt.Orientation.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(70)
        self._volume_slider.setFixedWidth(80)
        self._audio_output.setVolume(0.7)
        
        layout.addWidget(self._play_button)
        layout.addWidget(self._time_label)
        layout.addWidget(self._seek_slider)
        layout.addWidget(QLabel("Vol:"))
        layout.addWidget(self._volume_slider)

    def _connect_signals(self) -> None:
        self._play_button.clicked.connect(self.toggle_playback)
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_state_changed)
        self._seek_slider.sliderMoved.connect(self._on_seek)
        self._volume_slider.valueChanged.connect(self._on_volume_changed)

    def load_track(self, file_path: Optional[Path]) -> None:
        """Load a new file into the player and stop current playback."""
        self._player.stop()
        if file_path:
            self._player.setSource(QUrl.fromLocalFile(str(file_path)))
            self._seek_slider.setEnabled(True)
        else:
            self._player.setSource(QUrl())
            self._seek_slider.setEnabled(False)
            self._time_label.setText("0:00 / 0:00")

    def toggle_playback(self) -> None:
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def _on_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._play_button.setText("Pause")
        else:
            self._play_button.setText("Play")

    def _on_position_changed(self, position: int) -> None:
        if not self._seek_slider.isSliderDown():
            self._seek_slider.setValue(position)
        self._update_time_label()

    def _on_duration_changed(self, duration: int) -> None:
        self._seek_slider.setRange(0, duration)
        self._update_time_label()

    def _on_seek(self, position: int) -> None:
        self._player.setPosition(position)

    def _on_volume_changed(self, value: int) -> None:
        self._audio_output.setVolume(value / 100.0)

    def _update_time_label(self) -> None:
        pos = self._player.position() // 1000
        dur = self._player.duration() // 1000
        self._time_label.setText(
            f"{pos // 60}:{pos % 60:02d} / {dur // 60}:{dur % 60:02d}"
        )
    
    def stop(self) -> None:
        self._player.stop()
