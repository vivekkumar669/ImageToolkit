"""
Image preview panel: displays the currently loaded image with zoom,
fit-to-screen, and file info (format, dimensions, size).
"""

import logging
from pathlib import Path
from PIL import Image
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QSlider, QFrame
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt

from styles import Spacing, Fonts, get_card_stylesheet
from utils import format_file_size, get_pixmap_from_path, get_pixmap_from_qimage

logger = logging.getLogger(__name__)

MIN_ZOOM = 10   # percent
MAX_ZOOM = 400  # percent
DEFAULT_ZOOM = 100


class PreviewPanel(QWidget):
    """
    Displays a single image with zoom controls and metadata.
    Accepts either a file path (Path) or an in-memory QImage (clipboard paste).
    """

    def __init__(self, dark_mode: bool) -> None:
        super().__init__()
        self.dark_mode = dark_mode
        self.current_pixmap: QPixmap | None = None
        self.current_path: Path | None = None  # None for clipboard images
        self.zoom_level = DEFAULT_ZOOM

        self._build_ui()
        self._show_empty_state()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.MD, Spacing.MD, Spacing.MD, Spacing.MD)
        layout.setSpacing(Spacing.SM)

        layout.addWidget(self._build_info_bar())
        layout.addWidget(self._build_scroll_area(), stretch=1)
        layout.addWidget(self._build_zoom_controls())

    def _build_info_bar(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setStyleSheet(get_card_stylesheet(self.dark_mode))

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)

        self.info_label = QLabel("No image loaded")
        self.info_label.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}px; color: gray;")

        layout.addWidget(self.info_label)
        layout.addStretch()

        return frame

    def _build_scroll_area(self) -> QScrollArea:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll_area.setWidget(self.image_label)
        return self.scroll_area

    def _build_zoom_controls(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setFixedWidth(32)
        zoom_out_btn.clicked.connect(lambda: self._set_zoom(self.zoom_level - 10))

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(MIN_ZOOM, MAX_ZOOM)
        self.zoom_slider.setValue(DEFAULT_ZOOM)
        self.zoom_slider.valueChanged.connect(self._set_zoom)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedWidth(32)
        zoom_in_btn.clicked.connect(lambda: self._set_zoom(self.zoom_level + 10))

        self.zoom_label = QLabel(f"{DEFAULT_ZOOM}%")
        self.zoom_label.setFixedWidth(45)

        fit_btn = QPushButton("Fit to Screen")
        fit_btn.clicked.connect(self._fit_to_screen)

        original_btn = QPushButton("100%")
        original_btn.clicked.connect(lambda: self._set_zoom(DEFAULT_ZOOM))

        for w in (zoom_out_btn, self.zoom_slider, zoom_in_btn, self.zoom_label, fit_btn, original_btn):
            layout.addWidget(w)

        return container

    def _show_empty_state(self) -> None:
        self.image_label.setText("Drop or paste an image to preview it here")
        self.info_label.setText("No image loaded")

    # --- Public slots, connected from HomePage signals in app.py ---

    def load_from_path(self, path: Path) -> None:
        """Load and display an image from a file path."""
        try:
            pixmap = get_pixmap_from_path(path)
        except Exception as e:
            logger.error("Failed to load image %s: %s", path, e)
            self.info_label.setText(f"Error loading image: {e}")
            return

        self.current_pixmap = pixmap
        self.current_path = path
        self.zoom_level = DEFAULT_ZOOM
        self.zoom_slider.setValue(DEFAULT_ZOOM)

        self._render()
        self._update_info_from_path(path, pixmap)

    def load_from_qimage(self, image: QImage) -> None:
        """Load and display an image from clipboard (no file path)."""
        pixmap = get_pixmap_from_qimage(image)

        self.current_pixmap = pixmap
        self.current_path = None
        self.zoom_level = DEFAULT_ZOOM
        self.zoom_slider.setValue(DEFAULT_ZOOM)

        self._render()
        self._update_info_from_qimage(image)

    # --- Internal ---

    def _update_info_from_path(self, path: Path, pixmap: QPixmap) -> None:
        try:
            file_size = format_file_size(path.stat().st_size)
        except OSError:
            file_size = "Unknown size"

        fmt = path.suffix.lstrip(".").upper() or "Unknown"
        self.info_label.setText(
            f"{path.name}  |  {pixmap.width()}x{pixmap.height()}  |  {fmt}  |  {file_size}"
        )

    def _update_info_from_qimage(self, image: QImage) -> None:
        # No file size or format — this image has never touched disk.
        self.info_label.setText(
            f"Pasted image  |  {image.width()}x{image.height()}  |  Not saved yet"
        )

    def _render(self) -> None:
        if self.current_pixmap is None:
            return
        scale = self.zoom_level / 100.0
        w = int(self.current_pixmap.width() * scale)
        h = int(self.current_pixmap.height() * scale)
        scaled = self.current_pixmap.scaled(
            w, h, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.image_label.setPixmap(scaled)

    def _set_zoom(self, value: int) -> None:
        value = max(MIN_ZOOM, min(MAX_ZOOM, value))
        self.zoom_level = value
        self.zoom_slider.blockSignals(True)
        self.zoom_slider.setValue(value)
        self.zoom_slider.blockSignals(False)
        self.zoom_label.setText(f"{value}%")
        self._render()

    def _fit_to_screen(self) -> None:
        if self.current_pixmap is None:
            return
        area_size = self.scroll_area.viewport().size()
        pixmap_size = self.current_pixmap.size()

        if pixmap_size.width() == 0 or pixmap_size.height() == 0:
            return

        scale_w = area_size.width() / pixmap_size.width()
        scale_h = area_size.height() / pixmap_size.height()
        scale = min(scale_w, scale_h) * 100

        self._set_zoom(int(scale))