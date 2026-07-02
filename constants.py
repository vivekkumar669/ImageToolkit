"""
Application-wide constants.
No logic here — only fixed values referenced across the app.
"""

from pathlib import Path

# --- App Info ---
APP_NAME = "Image Toolkit"
APP_VERSION = "1.0.0"
ORG_NAME = "ImageToolkit"

# --- Paths ---
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
LOGO_PATH = ASSETS_DIR / "logo.png"
OUTPUT_DIR = BASE_DIR / "output"

# --- Window ---
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800
MIN_WINDOW_WIDTH = 900
MIN_WINDOW_HEIGHT = 600

# --- Sidebar ---
SIDEBAR_WIDTH = 220
SIDEBAR_COLLAPSED_WIDTH = 64

# --- Supported Formats ---
SUPPORTED_INPUT_FORMATS = [
    "PNG", "JPEG", "JPG", "WEBP", "BMP", "GIF",
    "TIFF", "ICO", "HEIC", "HEIF", "AVIF",
    "JPEG2000", "DDS", "TGA"
]

SUPPORTED_OUTPUT_FORMATS = SUPPORTED_INPUT_FORMATS + ["PDF"]

# Formats that support transparency (alpha channel)
FORMATS_WITH_ALPHA = ["PNG", "WEBP", "GIF", "TIFF", "ICO"]

# File extension mapping (some formats have multiple valid extensions)
FORMAT_EXTENSIONS = {
    "PNG": [".png"],
    "JPEG": [".jpg", ".jpeg"],
    "JPG": [".jpg", ".jpeg"],
    "WEBP": [".webp"],
    "BMP": [".bmp"],
    "GIF": [".gif"],
    "TIFF": [".tif", ".tiff"],
    "ICO": [".ico"],
    "HEIC": [".heic"],
    "HEIF": [".heif"],
    "AVIF": [".avif"],
    "JPEG2000": [".jp2", ".j2k"],
    "DDS": [".dds"],
    "TGA": [".tga"],
    "PDF": [".pdf"],
}

# --- Compression Defaults ---
DEFAULT_JPEG_QUALITY = 85
DEFAULT_WEBP_QUALITY = 85
MIN_QUALITY = 1
MAX_QUALITY = 100

# --- Crop Ratios ---
CROP_RATIOS = {
    "Free": None,
    "1:1": (1, 1),
    "4:3": (4, 3),
    "16:9": (16, 9),
    "9:16": (9, 16),
}

# --- Settings Keys (for QSettings) ---
SETTINGS_WINDOW_GEOMETRY = "window/geometry"
SETTINGS_THEME = "app/theme"
SETTINGS_LANGUAGE = "app/language"
SETTINGS_DEFAULT_SAVE_FOLDER = "app/default_save_folder"
SETTINGS_DEFAULT_FORMAT = "app/default_format"
SETTINGS_LAST_FOLDER = "app/last_folder"

# --- Logging ---
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = BASE_DIR / "app.log"