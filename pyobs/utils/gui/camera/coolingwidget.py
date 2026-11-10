from qtpy import QtCore, QtWidgets


class CoolingWidget(QtWidgets.QGroupBox):
    """Cooler control: on/off, target temperature and readouts of current temperature and power."""

    cooling_changed = QtCore.Signal(bool, float)

    def __init__(
        self,
        temperature_range: tuple[float, float] = (-30.0, 30.0),
        enabled: bool = False,
        set_point: float | None = None,
    ) -> None:
        super().__init__()

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.check_enabled = QtWidgets.QCheckBox()
        self.check_enabled.setChecked(enabled)
        self.check_enabled.toggled.connect(self._changed)
        layout.addRow("Cooler:", self.check_enabled)

        self.spin_set_point = QtWidgets.QDoubleSpinBox()
        self.spin_set_point.setRange(*temperature_range)
        self.spin_set_point.setDecimals(1)
        self.spin_set_point.setSuffix(" °C")
        self.spin_set_point.setValue(temperature_range[0] if set_point is None else set_point)
        # only react when editing is finished, not on every key stroke
        self.spin_set_point.setKeyboardTracking(False)
        self.spin_set_point.valueChanged.connect(self._changed)
        layout.addRow("Target:", self.spin_set_point)

        self.label_temperature = QtWidgets.QLabel("-")
        layout.addRow("Temperature:", self.label_temperature)
        self.label_power = QtWidgets.QLabel("-")
        layout.addRow("Power:", self.label_power)

    @QtCore.Slot()
    def _changed(self) -> None:
        self.cooling_changed.emit(self.enabled, self.set_point)  # type: ignore[attr-defined]

    @property
    def enabled(self) -> bool:
        return self.check_enabled.isChecked()

    @property
    def set_point(self) -> float:
        return self.spin_set_point.value()

    def set_temperature(self, temperature: float) -> None:
        self.label_temperature.setText(f"{temperature:.1f} °C")

    def set_power(self, power: float) -> None:
        self.label_power.setText(f"{power:.0f} %")
