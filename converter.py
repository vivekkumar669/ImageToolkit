"""
Image format conversion logic. No UI code here — pure functions,
testable independently of PySide6.
"""

import logging
from pathlib import Path
from PIL import Image

from constants import FORMATS_WITH_ALPHA, FORMAT_EXTENSIONS

logger = logging.getLogger(__name__)

# Pillow's internal format names don't always match our display names
FORMAT_TO_PILLOW = {
    "JPEG": "JPEG",
    "JPG": "JPEG",
    "PNG": "PNG",
    "WEBP": "WEBP",
    "BMP": "BMP",
    "GIF": "GIF",
    "TIFF": "TIFF",
    "ICO": "ICO",
    "HEIC": "HEIF",
    "HEIF": "HEIF",
    "AVIF": "AVIF",
    "JPEG2000": "JPEG2000",
    "DDS": "DDS",
    "TGA": "TGA",
    "PDF": "PDF",
}


class ConversionError(Exception):
    """Raised when a single image fails to convert. Caller decides whether to stop or continue."""
    pass


def has_alpha_channel(image: Image.Image) -> bool:
    """Check if the image actually uses transparency, not just has an alpha-capable mode."""
    if image.mode in ("RGBA", "LA", "PA"):
        alpha = image.getchannel("A") if "A" in image.mode else None
        if alpha is not None:
            # If alpha channel exists but every pixel is fully opaque, no real transparency
            extrema = alpha.getextrema()
            return extrema[0] < 255
    return False


def needs_transparency_warning(image: Image.Image, target_format: str) -> bool:
    """True if converting this image to target_format will silently destroy transparency."""
    return has_alpha_channel(image) and target_format not in FORMATS_WITH_ALPHA


def convert_image(
    source_path: Path,
    target_format: str,
    output_dir: Path,
    flatten_background: str = "white",
    overwrite: bool = False,
) -> Path:
    """
    Convert a single image to target_format, save it in output_dir.
    Returns the output path. Raises ConversionError on failure.
    """
    if target_format not in FORMAT_TO_PILLOW:
        raise ConversionError(f"Unsupported target format: {target_format}")

    pillow_format = FORMAT_TO_PILLOW[target_format]
    extension = FORMAT_EXTENSIONS[target_format][0]

    try:
        with Image.open(source_path) as img:
            img = _prepare_for_format(img, target_format, flatten_background)
            output_path = _resolve_output_path(source_path, output_dir, extension, overwrite)

            save_kwargs = _get_save_kwargs(target_format)
            img.save(output_path, format=pillow_format, **save_kwargs)

            logger.info("Converted %s -> %s", source_path.name, output_path.name)
            return output_path

    except ConversionError:
        raise
    except Exception as e:
        logger.error("Failed to convert %s: %s", source_path, e)
        raise ConversionError(f"Could not convert {source_path.name}: {e}") from e


def _prepare_for_format(image: Image.Image, target_format: str, flatten_background: str) -> Image.Image:
    """Handle mode conversion, including alpha flattening when target doesn't support transparency."""
    if target_format in FORMATS_WITH_ALPHA:
        return image  # keep as-is, including alpha if present

    if has_alpha_channel(image):
        # Flatten onto solid background — losing transparency is unavoidable here,
        # but doing it explicitly beats Pillow's default (which can corrupt colors).
        background = Image.new("RGB", image.size, flatten_background)
        background.paste(image, mask=image.split()[-1])  # use alpha channel as mask
        return background

    return image.convert("RGB") if image.mode != "RGB" else image


def _resolve_output_path(source_path: Path, output_dir: Path, extension: str, overwrite: bool) -> Path:
    """Build output path, auto-renaming if file exists and overwrite is False."""
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = source_path.stem
    output_path = output_dir / f"{base_name}{extension}"

    if overwrite or not output_path.exists():
        return output_path

    # Auto-rename: file(1).ext, file(2).ext, ...
    counter = 1
    while output_path.exists():
        output_path = output_dir / f"{base_name}({counter}){extension}"
        counter += 1
    return output_path


def _get_save_kwargs(target_format: str) -> dict:
    """Format-specific save parameters."""
    if target_format in ("JPEG", "JPG"):
        return {"quality": 95}
    if target_format == "WEBP":
        return {"quality": 95}
    if target_format == "PNG":
        return {"optimize": True}
    return {}