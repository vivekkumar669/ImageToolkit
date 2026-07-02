"""
Entry point. Keep this file minimal — no logic here.
"""

import sys
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app import MainWindow
from constants import APP_NAME, ORG_NAME, LOG_FORMAT, LOG_FILE


def setup_logging() -> None:
    """Configure logging to both file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting %s", APP_NAME)

    # High DPI support — must be set before QApplication is created
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()