"""
Convert page: pick target format, warn on transparency loss, run batch conversion.
PDF is handled separately — it merges all images into one file instead of 1:1 conversion.
"""

import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QListWidget, QMessageBox, QFileDialog, QProgressBar, QInputDialog
)
from PySide6.QtCore import Qt, QThread, Signal

from constants import SUPPORTED_OUTPUT_FORMATS, OUTPUT_DIR
from styles import Spacing, Fonts
from converter import convert_image, needs_transparency_warning, ConversionError
from PIL import Image

logger = logging.getLogger(__name__)


class ConversionWorker(QThread):
    """Runs batch conversion off the main thread so the UI doesn't freeze."""

    progress = Signal(int, int)
    file_done = Signal(str, bool, str)
    finished_all = Signal()

    def __init__(self, files: list[Path], target_format: str, output_dir: Path, overwrite: bool):
        super().__init__()
        self.files = files
        self.target_format = target_format
        self.output_dir = output_dir
        self.overwrite = overwrite
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        total = len(self.files)
        for i, file_path in enumerate(self.files, start=1):
            if self._cancelled:
                logger.info("Conversion cancelled by user")
                break
            try:
                convert_image(file_path, self.target_format, self.output_dir, overwrite=self.overwrite)
                self.file_done.emit(file_path.name, True, "")
            except ConversionError as e:
                self.file_done.emit(file_path.name, False, str(e))
            self.progress.emit(i, total)
        self.finished_all.emit()


class ConvertPage(QWidget):
    """Convert page UI. Receives loaded files from Home page via app.py wiring."""

    def __init__(self, dark_mode: bool) -> None:
        super().__init__()
        self.dark_mode = dark_mode
        self.loaded_files: list[Path] = []
        self.worker: ConversionWorker | None = None
        self.output_dir = OUTPUT_DIR

        self._build_ui()

    # ---------------------------------------------------------
    # UI construction
    # ---------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        title = QLabel("Convert")
        title.setStyleSheet(f"font-size: {Fonts.SIZE_TITLE}px; font-weight: 600;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Files to convert:"))
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(150)
        layout.addWidget(self.file_list)

        layout.addLayout(self._build_format_row())
        layout.addLayout(self._build_output_row())

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addLayout(self._build_action_row())
        layout.addStretch()

    def _build_format_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel("Convert to:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(SUPPORTED_OUTPUT_FORMATS)
        row.addWidget(self.format_combo)
        row.addStretch()
        return row

    def _build_output_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.output_label = QLabel(f"Output: {self.output_dir}")
        change_output_btn = QPushButton("Change Output Folder")
        change_output_btn.clicked.connect(self._change_output_folder)
        row.addWidget(self.output_label)
        row.addWidget(change_output_btn)
        row.addStretch()
        return row

    def _build_action_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.convert_btn = QPushButton("Convert")
        self.convert_btn.clicked.connect(self._start_conversion)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_conversion)
        row.addWidget(self.convert_btn)
        row.addWidget(self.cancel_btn)
        row.addStretch()
        return row

    # ---------------------------------------------------------
    # Public API (called from app.py)
    # ---------------------------------------------------------

    def add_files(self, files: list[Path]) -> None:
        for f in files:
            if f not in self.loaded_files:
                self.loaded_files.append(f)
                self.file_list.addItem(f.name)

    # ---------------------------------------------------------
    # Output folder
    # ---------------------------------------------------------

    def _change_output_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", str(self.output_dir))
        if folder:
            self.output_dir = Path(folder)
            self.output_label.setText(f"Output: {self.output_dir}")

    # ---------------------------------------------------------
    # Conversion entry point
    # ---------------------------------------------------------

    def _start_conversion(self) -> None:
        if not self.loaded_files:
            QMessageBox.warning(self, "No Files", "Load images from the Home page first.")
            return

        target_format = self.format_combo.currentText()

        if target_format == "PDF":
            self._convert_to_single_pdf()
            return

        if self._any_file_needs_warning(target_format):
            if not self._confirm_transparency_loss(target_format):
                return

        self._run_batch_conversion(target_format)

    def _any_file_needs_warning(self, target_format: str) -> bool:
        for file_path in self.loaded_files:
            try:
                with Image.open(file_path) as img:
                    if needs_transparency_warning(img, target_format):
                        return True
            except Exception as e:
                logger.warning("Could not check transparency for %s: %s", file_path, e)
        return False

    def _confirm_transparency_loss(self, target_format: str) -> bool:
        reply = QMessageBox.question(
            self,
            "Transparency Will Be Lost",
            f"Some images have transparent backgrounds. {target_format} doesn't support "
            f"transparency — those areas will be filled with white.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    # ---------------------------------------------------------
    # Batch (1:1) conversion — every format except PDF
    # ---------------------------------------------------------

    def _run_batch_conversion(self, target_format: str) -> None:
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.loaded_files))
        self.progress_bar.setVisible(True)
        self.convert_btn.setVisible(False)
        self.cancel_btn.setVisible(True)

        self.worker = ConversionWorker(self.loaded_files, target_format, self.output_dir, overwrite=False)
        self.worker.progress.connect(self._on_progress)
        self.worker.file_done.connect(self._on_file_done)
        self.worker.finished_all.connect(self._on_all_done)
        self.worker.start()

    def _cancel_conversion(self) -> None:
        if self.worker is not None:
            self.worker.cancel()

    def _on_progress(self, current: int, total: int) -> None:
        self.progress_bar.setValue(current)

    def _on_file_done(self, filename: str, success: bool, message: str) -> None:
        if not success:
            logger.error("Conversion failed for %s: %s", filename, message)

    def _on_all_done(self) -> None:
        self.progress_bar.setVisible(False)
        self.convert_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        QMessageBox.information(self, "Done", "Conversion finished. Check the output folder.")

    # ---------------------------------------------------------
    # PDF (many-to-one) conversion — separate path from batch
    # ---------------------------------------------------------

    def _convert_to_single_pdf(self) -> None:
        filename, ok = QInputDialog.getText(
            self, "Save PDF As", "File name:", text="converted"
        )
        if not ok or not filename.strip():
            return

        filename = filename.strip()
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        try:
            images = []
            for file_path in self.loaded_files:
                with Image.open(file_path) as img:
                    img = img.convert("RGB") if img.mode != "RGB" else img.copy()
                    images.append(img)

            if not images:
                return

            self.output_dir.mkdir(parents=True, exist_ok=True)
            output_path = self.output_dir / filename

            if output_path.exists():
                reply = QMessageBox.question(
                    self, "File Exists",
                    f"{filename} already exists. Overwrite?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return

            images[0].save(output_path, save_all=True, append_images=images[1:])
            logger.info("Merged %d images into %s", len(images), output_path)
            QMessageBox.information(self, "Done", f"Saved {len(images)}-page PDF to {output_path}")

        except Exception as e:
            logger.error("PDF merge failed: %s", e)
            QMessageBox.critical(self, "Error", f"Failed to create PDF: {e}")