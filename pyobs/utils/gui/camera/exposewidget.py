from time import time

from qtpy import QtWidgets, QtCore


class ExposeWidget(QtWidgets.QGroupBox):
    expose_clicked = QtCore.Signal(int)
    abort_clicked = QtCore.Signal()

    def __init__(self, can_abort_exposure: bool = True, can_progress: bool = True):
        super().__init__()

        self._can_abort_exposure = can_abort_exposure
        self._exposures_left = 1
        self._exposing = False
        self._progress = 0.0
        self._exposure_time = 0.0
        self._exposure_start = 0.0

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.spin_count = QtWidgets.QSpinBox()
        self.spin_count.setMinimum(1)
        self.spin_count.setMaximum(9999)
        layout.addRow("Count:", self.spin_count)

        self.button = QtWidgets.QPushButton("Expose")
        self.button.setStyleSheet("background-color: lime; color: black;")
        self.button.clicked.connect(self._button_clicked)
        layout.addRow(self.button)

        self.progress_bar = QtWidgets.QProgressBar()
        layout.addRow(self.progress_bar)

        self.label_exposures_left = QtWidgets.QLabel("Exposures")
        self.label_exposures_left.setVisible(False)
        layout.addRow(self.label_exposures_left)

        self.progress_timer = QtCore.QTimer()
        self.progress_timer.setInterval(100)
        self.progress_timer.timeout.connect(self._progress_timer_update)

    def _update_gui(self) -> None:
        if self._exposing:
            if self._exposures_left > 1:
                self.button.setText("Abort sequence")
                self.button.setStyleSheet("background-color: red; color: black;")
            else:
                if self._can_abort_exposure:
                    self.button.setText("Abort")
                    self.button.setStyleSheet("background-color: red; color: black;")
                else:
                    self.button.setStyleSheet("")
                    self.button.setEnabled(False)
        else:
            self.button.setEnabled(True)
            self.button.setText("Expose")
            self.button.setStyleSheet("background-color: lime; color: black;")

        self.label_exposures_left.setVisible(self._exposures_left > 1)
        self.label_exposures_left.setText(f"Exposures left: {self._exposures_left}")

    @QtCore.Slot()
    def _button_clicked(self) -> None:
        if self._exposing:
            self.abort_clicked.emit()
        else:
            self._exposing = True
            self._exposures_left = self.spin_count.value()
            self.progress_bar.setValue(0)
            self._update_gui()
            self.expose_clicked.emit(self.spin_count.value())

    @QtCore.Slot()
    def set_exposures_left(self, exposures_left: int = 0) -> None:
        self._exposing = exposures_left > 0
        self._exposures_left = exposures_left
        self.progress_timer.stop()
        self.progress_bar.setValue(0)
        self._update_gui()

    @QtCore.Slot()
    def start_exposure(self, exposure_time: float) -> None:
        self._exposure_time = exposure_time
        self._exposure_start = time()
        self.progress_timer.start()

    @QtCore.Slot()
    def _progress_timer_update(self) -> None:
        done = min(100.0, (time() - self._exposure_start) / self._exposure_time * 100.0)
        self.progress_bar.setValue(int(done))

    @QtCore.Slot()
    def set_progress(self, progress: float = 0.0) -> None:
        self._progress = progress
        self.progress_bar.setValue(int(self._progress))
