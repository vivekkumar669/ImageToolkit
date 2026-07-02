"""
Home page: logo, drag & drop area, browse/paste buttons, recent files, supported formats.
"""

import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QFrame, QListWidget, QListWidgetItem
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal, QSettings

from constants import (
    LOGO_PATH, SUPPORTED_INPUT_FORMATS, ORG_NAME, APP_NAME,
    SETTINGS_LAST_FOLDER
)
from styles import Spacing, Fonts, get_card_stylesheet
from dragdrop import DropZone
from clipboard import get_clipboard_image

logger = logging.getLogger(__name__)

MAX_RECENT_FILES = 8


class HomePage(QWidget):
    """
    Landing page. Emits image_loaded(Path) or clipboard_image_loaded(QImage)
    when the user provides an image — the main window / preview logic
    (built in a later step) will listen to these.
    """

    image_loaded = Signal(Path)
    clipboard_image_loaded = Signal(object)  # QImage

    def __init__(self, dark_mode: bool) -> None:
        super().__init__()
        self.dark_mode = dark_mode
        self.settings = QSettings(ORG_NAME, APP_NAME)
        self.recent_files: list[str] = []

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.setSpacing(Spacing.LG)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(self._build_logo())
        layout.addWidget(self._build_drop_zone())
        layout.addLayout(self._build_action_buttons())
        layout.addWidget(self._build_recent_files())
        layout.addWidget(self._build_supported_formats())

    def _build_logo(self) -> QLabel:
        label = QLabel()
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if LOGO_PATH.exists():
            pixmap = QPixmap(str(LOGO_PATH))
            label.setPixmap(pixmap.scaledToHeight(80, Qt.TransformationMode.SmoothTransformation))
        else:
            # No logo file yet — fall back to text so the app doesn't break
            label.setText(APP_NAME)
            label.setStyleSheet(f"font-size: {Fonts.SIZE_TITLE}px; font-weight: 600;")
            logger.warning("Logo not found at %s — using text fallback", LOGO_PATH)

        return label

    def _build_drop_zone(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setStyleSheet(get_card_stylesheet(self.dark_mode))
        frame.setMinimumHeight(220)

        # DropZone logic is mixed into this frame via composition,
        # not inheritance — keeps QFrame styling separate from drop behavior.
        self.drop_zone = DropZone(frame)
        self.drop_zone.files_dropped.connect(self._handle_files_dropped)

        inner_layout = QVBoxLayout(frame)
        inner_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel("📁")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("font-size: 40px;")

        text_label = QLabel("Drag & drop images or folders here")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_label.setStyleSheet(f"font-size: {Fonts.SIZE_MEDIUM}px;")

        inner_layout.addWidget(icon_label)
        inner_layout.addWidget(text_label)

        # Forward drop events from the frame's DropZone child to this frame's size
        self.drop_zone.setGeometry(frame.rect())

        return frame

    def _build_action_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(Spacing.MD)

        browse_btn = QPushButton("Browse Files")
        browse_btn.clicked.connect(self._browse_files)

        paste_btn = QPushButton("Paste Image (Ctrl+V)")
        paste_btn.clicked.connect(self._paste_from_clipboard)

        layout.addWidget(browse_btn)
        layout.addWidget(paste_btn)
        layout.addStretch()

        return layout

    def _build_recent_files(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Recent Files")
        label.setStyleSheet(f"font-size: {Fonts.SIZE_MEDIUM}px; font-weight: 600;")

        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(150)
        self.recent_list.itemDoubleClicked.connect(self._open_recent_file)

        layout.addWidget(label)
        layout.addWidget(self.recent_list)

        return container

    def _build_supported_formats(self) -> QLabel:
        text = "Supported formats: " + ", ".join(SUPPORTED_INPUT_FORMATS)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet(f"font-size: {Fonts.SIZE_SMALL}px; color: gray;")
        return label

    def _browse_files(self) -> None:
        last_folder = self.settings.value(SETTINGS_LAST_FOLDER, str(Path.home()))
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Images", last_folder,
            "Images (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.tiff *.heic *.avif)"
        )
        if files:
            self.settings.setValue(SETTINGS_LAST_FOLDER, str(Path(files[0]).parent))
            for f in files:
                self._add_file(Path(f))

    def _paste_from_clipboard(self) -> None:
        image = get_clipboard_image()
        if image is not None:
            self.clipboard_image_loaded.emit(image)
        else:
            logger.info("Paste attempted but clipboard has no image")
            # Toast notification for "no image in clipboard" comes in a later step
            # once the toast widget exists — not wiring a silent failure permanently.

    def _handle_files_dropped(self, files: list[Path]) -> None:
        for f in files:
            self._add_file(f)

    def _add_file(self, path: Path) -> None:
        self.image_loaded.emit(path)
        self._add_to_recent(path)

    def _add_to_recent(self, path: Path) -> None:
        path_str = str(path)
        if path_str in self.recent_files:
            self.recent_files.remove(path_str)
        self.recent_files.insert(0, path_str)
        self.recent_files = self.recent_files[:MAX_RECENT_FILES]

        self.recent_list.clear()
        for f in self.recent_files:
            item = QListWidgetItem(Path(f).name)
            item.setToolTip(f)
            self.recent_list.addItem(item)

    def _open_recent_file(self, item: QListWidgetItem) -> None:
        path = Path(item.toolTip())
        if path.exists():
            self.image_loaded.emit(path)
        else:
            logger.warning("Recent file no longer exists: %s", path)