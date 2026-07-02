"""
Main application window: sidebar navigation, page switching,
window geometry persistence, theme setup.
"""

import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QStatusBar, QButtonGroup
)
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QScreen
import qdarktheme

from constants import (
    APP_NAME, ORG_NAME, DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT, SIDEBAR_WIDTH,
    SETTINGS_WINDOW_GEOMETRY, SETTINGS_THEME
)
from styles import get_sidebar_stylesheet
from ui.home import HomePage

logger = logging.getLogger(__name__)

# Sidebar pages: (internal_key, display_label)
# Only "Home" is a real page right now. The rest are placeholders
# until their ui/ files are built in later steps.
PAGES = [
    ("home", "🏠 Home"),
    ("convert", "🖼 Convert"),
    ("resize", "📏 Resize"),
    ("compress", "🗜 Compress"),
    ("crop", "✂ Crop"),
    ("rotate", "🔄 Rotate"),
    ("background", "🎨 Background"),
    ("metadata", "📄 Metadata"),
    ("settings", "⚙ Settings"),
]


class PlaceholderPage(QWidget):
    """Temporary page shown until the real page module is built."""

    def __init__(self, title: str) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label = QLabel(f"{title}\n\n(Not built yet)")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)


class MainWindow(QMainWindow):
    """Top-level application window."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = QSettings(ORG_NAME, APP_NAME)
        self.dark_mode = self.settings.value(SETTINGS_THEME, "dark") == "dark"

        self._apply_theme()
        self._setup_window()
        self._build_ui()
        self._restore_geometry()

    def _apply_theme(self) -> None:
        """Apply qdarktheme globally. Custom widget QSS is layered on top per-widget."""
        theme = "dark" if self.dark_mode else "light"
        qdarktheme.setup_theme(theme)

    def _setup_window(self) -> None:
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())
        root_layout.addWidget(self._build_pages(), stretch=1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setStyleSheet(get_sidebar_stylesheet(self.dark_mode))

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(4)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        for index, (key, label) in enumerate(PAGES):
            btn = QPushButton(label)
            btn.setObjectName("sidebarButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, i=index: self.stack.setCurrentIndex(i))
            self.nav_group.addButton(btn, index)
            layout.addWidget(btn)

        layout.addStretch()
        self.nav_group.button(0).setChecked(True)  # Home selected by default

        return sidebar

    def _build_pages(self) -> QStackedWidget:
        self.stack = QStackedWidget()
        for key, label in PAGES:
            if key == "home":
                self.stack.addWidget(HomePage(self.dark_mode))
            else:
                self.stack.addWidget(PlaceholderPage(label))
        return self.stack

    def _restore_geometry(self) -> None:
        """Restore last window size/position, or center on screen for first launch."""
        geometry = self.settings.value(SETTINGS_WINDOW_GEOMETRY)
        if geometry is not None:
            self.restoreGeometry(geometry)
        else:
            self._center_on_screen()

    def _center_on_screen(self) -> None:
        screen = self.screen() or QScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def closeEvent(self, event) -> None:
        """Save window geometry on exit."""
        self.settings.setValue(SETTINGS_WINDOW_GEOMETRY, self.saveGeometry())
        logger.info("Window closed, geometry saved")
        super().closeEvent(event)