"""
Clipboard image handling — paste screenshots or copied images (Ctrl+V).
"""

import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage

logger = logging.getLogger(__name__)


def get_clipboard_image() -> QImage | None:
    """
    Returns a QImage from the system clipboard, or None if the clipboard
    doesn't contain image data.
    """
    clipboard = QApplication.clipboard()
    mime_data = clipboard.mimeData()

    if mime_data.hasImage():
        image = clipboard.image()
        if not image.isNull():
            logger.info("Retrieved image from clipboard: %dx%d", image.width(), image.height())
            return image

    logger.info("No image found in clipboard")
    return None