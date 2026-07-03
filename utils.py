"""
Shared utility functions used across multiple modules.
"""

from pathlib import Path
from PySide6.QtGui import QPixmap, QImage

# Register HEIF/AVIF plugins once, at import time, so Pillow can open them.
import pillow_heif
import pillow_avif
pillow_heif.register_heif_opener()


def format_file_size(size_bytes: int) -> str:
    """Convert bytes to a human-readable string (KB, MB, GB)."""
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def get_pixmap_from_path(path: Path) -> QPixmap:
    """
    Load an image file into a QPixmap. Uses Pillow first for broad format
    support (HEIC, AVIF, etc. — Qt's native loader doesn't support these),
    then converts to QPixmap via QImage.
    """
    from PIL import Image
    from io import BytesIO

    with Image.open(path) as img:
        img = img.convert("RGBA") if img.mode not in ("RGB", "RGBA") else img
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

    qimage = QImage.fromData(buffer.read())
    return QPixmap.fromImage(qimage)


def get_pixmap_from_qimage(image: QImage) -> QPixmap:
    """Convert a QImage (from clipboard) to QPixmap."""
    return QPixmap.fromImage(image)