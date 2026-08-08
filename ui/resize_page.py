


import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QMessageBox, QFileDialog, QProgressBar, QSpinBox, QDoubleSpinBox,
    QCheckBox, QRadioButton, QButtonGroup, QStackedWidget
)
from PySide6.QtCore import QThread, Signal

from constants import OUTPUT_DIR
from styles import Spacing, Fonts
from resizer import resize_image, calculate_dimensions, ResizeError
from PIL import Image
logger = logging.getLogger(__name__)


class ResizeWorker(QThread):
    """Runs batch resize off the main thread."""

    progress = Signal(int, int)
    file_done = Signal(str, bool, str)
    finished_all = Signal()

    def __init__(self, files: list[Path], mode: str, width, height, percentage,
                 maintain_aspect: bool, output_dir: Path, overwrite: bool):
        super().__init__()
        self.files = files
        self.mode = mode
        self.width = width
        self.height = height
        self.percentage = percentage
        self.maintain_aspect = maintain_aspect
        self.output_dir = output_dir
        self.overwrite = overwrite
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        total = len(self.files)
        for i, file_path in enumerate(self.files, start=1):
            if self._cancelled:
                logger.info("Resize cancelled by user")
                break
            try:
                with Image.open(file_path) as img:
                    orig_w, orig_h = img.size

                target_w, target_h = calculate_dimensions(
                    orig_w, orig_h, self.mode,
                    width=self.width, height=self.height,
                    percentage=self.percentage, maintain_aspect=self.maintain_aspect,
                )
                resize_image(file_path, self.output_dir, target_w, target_h, self.overwrite)
                self.file_done.emit(file_path.name, True, "")
            except ResizeError as e:
                self.file_done.emit(file_path.name, False, str(e))
            self.progress.emit(i, total)
        self.finished_all.emit()


class ResizePage(QWidget):

    def __init__(self, dark_mode: bool) -> None:
        super().__init__()
        self.dark_mode = dark_mode
        self.loaded_files: list[Path] = []
        self.worker: ResizeWorker | None = None
        self.output_dir = OUTPUT_DIR

        self._build_ui()

    # ---------------------------------------------------------
    # UI construction
    # ---------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        title = QLabel("Resize")
        title.setStyleSheet(f"font-size: {Fonts.SIZE_TITLE}px; font-weight: 600;")
        layout.addWidget(title)

        layout.addWidget(QLabel("Files to resize:"))
        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(150)
        layout.addWidget(self.file_list)

        layout.addLayout(self._build_mode_selector())
        layout.addWidget(self._build_mode_stack())
        layout.addLayout(self._build_output_row())

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addLayout(self._build_action_row())
        layout.addStretch()

    def _build_mode_selector(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.dimensions_radio = QRadioButton("By Dimensions")
        self.percentage_radio = QRadioButton("By Percentage")
        self.dimensions_radio.setChecked(True)

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.dimensions_radio, 0)
        self.mode_group.addButton(self.percentage_radio, 1)
        self.mode_group.idClicked.connect(self._on_mode_changed)

        row.addWidget(self.dimensions_radio)
        row.addWidget(self.percentage_radio)
        row.addStretch()
        return row

    def _build_mode_stack(self) -> QStackedWidget:
        self.mode_stack = QStackedWidget()
        self.mode_stack.addWidget(self._build_dimensions_panel())
        self.mode_stack.addWidget(self._build_percentage_panel())
        return self.mode_stack

    def _build_dimensions_panel(self) -> QWidget:
        panel = QWidget()
        row = QHBoxLayout(panel)

        row.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(800)
        row.addWidget(self.width_spin)

        row.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(600)
        row.addWidget(self.height_spin)

        self.aspect_checkbox = QCheckBox("Maintain aspect ratio")
        self.aspect_checkbox.setChecked(True)
        self.aspect_checkbox.toggled.connect(self._on_aspect_toggled)
        row.addWidget(self.aspect_checkbox)

        row.addStretch()

        # Aspect locked by default — height field is derived, not user-set, so disable it
        self.height_spin.setEnabled(False)

        return panel

    def _build_percentage_panel(self) -> QWidget:
        panel = QWidget()
        row = QHBoxLayout(panel)
        row.addWidget(QLabel("Scale:"))
        self.percentage_spin = QDoubleSpinBox()
        self.percentage_spin.setRange(1, 1000)
        self.percentage_spin.setValue(100)
        self.percentage_spin.setSuffix(" %")
        row.addWidget(self.percentage_spin)
        row.addStretch()
        return panel

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
        self.resize_btn = QPushButton("Resize")
        self.resize_btn.clicked.connect(self._start_resize)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_resize)
        row.addWidget(self.resize_btn)
        row.addWidget(self.cancel_btn)
        row.addStretch()
        return row

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def add_files(self, files: list[Path]) -> None:
        for f in files:
            if f not in self.loaded_files:
                self.loaded_files.append(f)
                self.file_list.addItem(f.name)

   
    def _on_mode_changed(self, button_id: int) -> None:
        self.mode_stack.setCurrentIndex(button_id)

    def _on_aspect_toggled(self, checked: bool) -> None:
        # When aspect is locked, height is computed per-image — disable manual entry
        # so the user isn't misled into thinking their height value will be used literally.
        self.height_spin.setEnabled(not checked)

    

    def _change_output_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder", str(self.output_dir))
        if folder:
            self.output_dir = Path(folder)
            self.output_label.setText(f"Output: {self.output_dir}")

    

    def _start_resize(self) -> None:
        if not self.loaded_files:
            QMessageBox.warning(self, "No Files", "Load images from the Home page first.")
            return

        if self.dimensions_radio.isChecked():
            mode = "dimensions"
            maintain_aspect = self.aspect_checkbox.isChecked()
            width = self.width_spin.value()
            height = None if maintain_aspect else self.height_spin.value()
            percentage = None
        else:
            mode = "percentage"
            maintain_aspect = True
            width = height = None
            percentage = self.percentage_spin.value()

        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.loaded_files))
        self.progress_bar.setVisible(True)
        self.resize_btn.setVisible(False)
        self.cancel_btn.setVisible(True)

        self.worker = ResizeWorker(
            self.loaded_files, mode, width, height, percentage,
            maintain_aspect, self.output_dir, overwrite=False
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.file_done.connect(self._on_file_done)
        self.worker.finished_all.connect(self._on_all_done)
        self.worker.start()

    def _cancel_resize(self) -> None:
        if self.worker is not None:
            self.worker.cancel()

    def _on_progress(self, current: int, total: int) -> None:
        self.progress_bar.setValue(current)

    def _on_file_done(self, filename: str, success: bool, message: str) -> None:
        if not success:
            logger.error("Resize failed for %s: %s", filename, message)

    def _on_all_done(self) -> None:
        self.progress_bar.setVisible(False)
        self.resize_btn.setVisible(True)
        self.cancel_btn.setVisible(False)
        QMessageBox.information(self, "Done", "Resize finished. Check the output folder.")