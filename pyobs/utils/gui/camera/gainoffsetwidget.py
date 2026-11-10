from qtpy import QtCore, QtWidgets


class GainOffsetWidget(QtWidgets.QGroupBox):
    gain_changed = QtCore.Signal(int)
    offset_changed = QtCore.Signal(int)

    def __init__(
        self,
        gain_range: tuple[int, int] = (0, 100),
        offset_range: tuple[int, int] = (0, 100),
        gain: int | None = None,
        offset: int | None = None,
    ) -> None:
        super().__init__()

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.spin_gain = QtWidgets.QSpinBox()
        self.spin_gain.setRange(*gain_range)
        self.spin_gain.setValue(gain_range[0] if gain is None else gain)
        self.spin_gain.valueChanged.connect(self._gain_changed)
        layout.addRow("Gain:", self.spin_gain)

        self.spin_offset = QtWidgets.QSpinBox()
        self.spin_offset.setRange(*offset_range)
        self.spin_offset.setValue(offset_range[0] if offset is None else offset)
        self.spin_offset.valueChanged.connect(self._offset_changed)
        layout.addRow("Offset:", self.spin_offset)

    @QtCore.Slot(int)
    def _gain_changed(self, value: int) -> None:
        self.gain_changed.emit(value)  # type: ignore[attr-defined]

    @QtCore.Slot(int)
    def _offset_changed(self, value: int) -> None:
        self.offset_changed.emit(value)  # type: ignore[attr-defined]

    @property
    def gain(self) -> int:
        return self.spin_gain.value()

    @property
    def offset(self) -> int:
        return self.spin_offset.value()
