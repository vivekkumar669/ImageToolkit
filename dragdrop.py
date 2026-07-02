"""
Drag and drop support for image files/folders.
Reusable across Home page and other pages that accept file input.
"""

import logging
from pathlib import Path
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtCore import Signal

from constants import FORMAT_EXTENSIONS

logger = logging.getLogger(__name__)

# Flatten all valid extensions into one set for fast lookup
VALID_EXTENSIONS = {ext for exts in FORMAT_EXTENSIONS.values() for ext in exts}


class DropZone(QWidget):
    """
    A widget that accepts drag-and-drop of image files and folders.
    Emits files_dropped(list[Path]) with validated, existing image file paths.
    """

    files_dropped = Signal(list)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        valid_files = self._collect_valid_files(paths)

        if valid_files:
            logger.info("Dropped %d valid file(s)", len(valid_files))
            self.files_dropped.emit(valid_files)
        else:
            logger.warning("Drop rejected: no valid image files found")

        event.acceptProposedAction()

    def _collect_valid_files(self, paths: list[Path]) -> list[Path]:
        """Expand folders and filter to supported image extensions only."""
        valid = []
        for path in paths:
            if path.is_dir():
                for file in path.rglob("*"):
                    if file.is_file() and file.suffix.lower() in VALID_EXTENSIONS:
                        valid.append(file)
            elif path.is_file() and path.suffix.lower() in VALID_EXTENSIONS:
                valid.append(path)
        return valid