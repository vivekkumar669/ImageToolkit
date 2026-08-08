"""
Image resizing logic. Pure functions — no UI code, testable independently.
"""

import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


class ResizeError(Exception):
    """Raised when a single image fails to resize."""
    pass


def calculate_dimensions(
    original_width: int,
    original_height: int,
    mode: str,
    width: int | None = None,
    height: int | None = None,
    percentage: float | None = None,
    maintain_aspect: bool = True,
) -> tuple[int, int]:
    """
    Resolve final (width, height) for one image based on the chosen mode.
    mode: 'percentage' or 'dimensions'
    """
    if mode == "percentage":
        if percentage is None or percentage <= 0:
            raise ResizeError("Percentage must be greater than 0")
        scale = percentage / 100.0
        return max(1, round(original_width * scale)), max(1, round(original_height * scale))

    if mode == "dimensions":
        if not maintain_aspect:
            if width is None or height is None:
                raise ResizeError("Both width and height are required when aspect ratio is not locked")
            return width, height

        
        ratio = original_width / original_height
        if width is not None:
            return width, max(1, round(width / ratio))
        if height is not None:
            return max(1, round(height * ratio)), height
        raise ResizeError("Provide at least width or height")

    raise ResizeError(f"Unknown resize mode: {mode}")


def resize_image(
    source_path: Path,
    output_dir: Path,
    target_width: int,
    target_height: int,
    overwrite: bool = False,
) -> Path:
    """Resize a single image to exact target dimensions and save it."""
    try:
        with Image.open(source_path) as img:
            resized = img.resize((target_width, target_height), Image.LANCZOS)

            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = _resolve_output_path(source_path, output_dir, overwrite)

            resized.save(output_path, format=img.format or "PNG")
            logger.info("Resized %s -> %dx%d", source_path.name, target_width, target_height)
            return output_path

    except ResizeError:
        raise
    except Exception as e:
        logger.error("Failed to resize %s: %s", source_path, e)
        raise ResizeError(f"Could not resize {source_path.name}: {e}") from e


def _resolve_output_path(source_path: Path, output_dir: Path, overwrite: bool) -> Path:
    """Same auto-rename pattern as converter.py — kept consistent, not shared,
    since resize and convert have different enough contexts to risk coupling them."""
    output_path = output_dir / source_path.name

    if overwrite or not output_path.exists():
        return output_path

    counter = 1
    stem, suffix = source_path.stem, source_path.suffix
    while output_path.exists():
        output_path = output_dir / f"{stem}({counter}){suffix}"
        counter += 1
    return output_path