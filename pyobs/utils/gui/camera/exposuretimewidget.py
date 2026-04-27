from qtpy import QtWidgets, QtCore


class ExposureTimeWidget(QtWidgets.QGroupBox):
    exposure_time_changed = QtCore.Signal(float)

    def __init__(self, max_exposure_time_sec: float = 9999.99) -> None:
        super().__init__()

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.spin_exposure_time = QtWidgets.QDoubleSpinBox()
        self.spin_exposure_time.setRange(0, max_exposure_time_sec)
        self.spin_exposure_time.valueChanged.connect(self._exposure_time_changed)
        layout.addRow("ExpTime:", self.spin_exposure_time)

    @QtCore.Slot(float)
    def _exposure_time_changed(self, value: float) -> None:
        self.exposure_time_changed.emit(value)

    @property
    def value(self) -> float:
        return self.spin_exposure_time.value()
