"""
Centralized styling: colors, fonts, spacing, and QSS (Qt Style Sheet) generation.
Keeps visual design decisions in one place instead of scattered across UI files.
"""


class Colors:
    """Color palette. Kept separate from qdarktheme so we can theme custom widgets consistently."""

    # Dark theme
    DARK_BG = "#1e1e1e"
    DARK_SURFACE = "#2b2b2b"
    DARK_SURFACE_HOVER = "#3a3a3a"
    DARK_BORDER = "#3f3f3f"
    DARK_TEXT = "#e6e6e6"
    DARK_TEXT_MUTED = "#9a9a9a"

    # Light theme
    LIGHT_BG = "#f5f5f5"
    LIGHT_SURFACE = "#ffffff"
    LIGHT_SURFACE_HOVER = "#ececec"
    LIGHT_BORDER = "#e0e0e0"
    LIGHT_TEXT = "#1a1a1a"
    LIGHT_TEXT_MUTED = "#6e6e6e"

    # Accent (same across both themes)
    ACCENT = "#5b8def"
    ACCENT_HOVER = "#4a7ce0"
    SUCCESS = "#3fb950"
    WARNING = "#d29922"
    ERROR = "#f85149"


class Fonts:
    """Typography settings."""

    FAMILY = "Segoe UI"          # Falls back gracefully on Mac/Linux
    FAMILY_FALLBACK = "Arial"
    SIZE_SMALL = 11
    SIZE_NORMAL = 13
    SIZE_MEDIUM = 15
    SIZE_LARGE = 18
    SIZE_TITLE = 24


class Spacing:
    """Consistent spacing scale — use these instead of guessing pixel values."""

    XS = 4
    SM = 8
    MD = 16
    LG = 24
    XL = 32

    RADIUS_SM = 6
    RADIUS_MD = 10
    RADIUS_LG = 14


def get_sidebar_stylesheet(dark: bool) -> str:
    """
    Returns QSS for the sidebar widget.
    Sidebar is custom-built, so it needs its own stylesheet on top of qdarktheme.
    """
    bg = Colors.DARK_SURFACE if dark else Colors.LIGHT_SURFACE
    hover = Colors.DARK_SURFACE_HOVER if dark else Colors.LIGHT_SURFACE_HOVER
    text = Colors.DARK_TEXT if dark else Colors.LIGHT_TEXT
    border = Colors.DARK_BORDER if dark else Colors.LIGHT_BORDER

    return f"""
    QWidget#sidebar {{
        background-color: {bg};
        border-right: 1px solid {border};
    }}
    QPushButton#sidebarButton {{
        background-color: transparent;
        color: {text};
        text-align: left;
        padding: {Spacing.SM}px {Spacing.MD}px;
        border-radius: {Spacing.RADIUS_SM}px;
        font-size: {Fonts.SIZE_NORMAL}px;
        border: none;
    }}
    QPushButton#sidebarButton:hover {{
        background-color: {hover};
    }}
    QPushButton#sidebarButton:checked {{
        background-color: {Colors.ACCENT};
        color: white;
        font-weight: 600;
    }}
    """


def get_card_stylesheet(dark: bool) -> str:
    """QSS for card-style containers used across pages (drop zones, preview panels, etc.)."""
    bg = Colors.DARK_SURFACE if dark else Colors.LIGHT_SURFACE
    border = Colors.DARK_BORDER if dark else Colors.LIGHT_BORDER

    return f"""
    QFrame#card {{
        background-color: {bg};
        border: 1px solid {border};
        border-radius: {Spacing.RADIUS_MD}px;
    }}
    """


def get_toast_stylesheet(dark: bool, level: str = "info") -> str:
    """
    QSS for toast notifications.
    level: 'info', 'success', 'warning', 'error'
    """
    color_map = {
        "info": Colors.ACCENT,
        "success": Colors.SUCCESS,
        "warning": Colors.WARNING,
        "error": Colors.ERROR,
    }
    accent = color_map.get(level, Colors.ACCENT)
    bg = Colors.DARK_SURFACE if dark else Colors.LIGHT_SURFACE
    text = Colors.DARK_TEXT if dark else Colors.LIGHT_TEXT

    return f"""
    QFrame#toast {{
        background-color: {bg};
        border-left: 4px solid {accent};
        border-radius: {Spacing.RADIUS_SM}px;
        padding: {Spacing.SM}px {Spacing.MD}px;
    }}
    QLabel#toastLabel {{
        color: {text};
        font-size: {Fonts.SIZE_NORMAL}px;
    }}
    """