from qtpy import QtWidgets, QtCore


class WindowingWidget(QtWidgets.QGroupBox):
    window_changed = QtCore.Signal(int, int, int, int)

    def __init__(self, max_width: int, max_height: int) -> None:
        super().__init__()

        self._max_width = max_width
        self._max_height = max_height
        self._binning = (1, 1)

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.spin_left = QtWidgets.QSpinBox()
        self.spin_left.setMinimum(0)
        self.spin_left.valueChanged.connect(self._update_min_max)
        layout.addRow("Left:", self.spin_left)
        self.spin_top = QtWidgets.QSpinBox()
        self.spin_top.setMinimum(0)
        self.spin_top.valueChanged.connect(self._update_min_max)
        layout.addRow("Top:", self.spin_top)
        self.spin_width = QtWidgets.QSpinBox()
        self.spin_width.setMinimum(1)
        layout.addRow("Width:", self.spin_width)
        self.spin_height = QtWidgets.QSpinBox()
        self.spin_height.setMinimum(1)
        layout.addRow("Height:", self.spin_height)

        self.button = QtWidgets.QPushButton("Full Frame")
        self.button.clicked.connect(self.full_frame)
        layout.addRow(self.button)

        self._signal_timer = QtCore.QTimer()
        self._signal_timer.setSingleShot(True)
        self._signal_timer.timeout.connect(self._emit_signal)
        self.spin_left.valueChanged.connect(lambda: self._signal_timer.start(500))
        self.spin_top.valueChanged.connect(lambda: self._signal_timer.start(500))
        self.spin_width.valueChanged.connect(lambda: self._signal_timer.start(500))
        self.spin_height.valueChanged.connect(lambda: self._signal_timer.start(500))

        self._update_min_max()
        self.full_frame()

    @property
    def left(self) -> int:
        return self.spin_left.value()

    @property
    def top(self) -> int:
        return self.spin_left.value()

    @property
    def width(self) -> int:
        return self.spin_width.value()

    @property
    def height(self) -> int:
        return self.spin_height.value()

    @property
    def values(self) -> tuple[int, int, int, int]:
        return self.left, self.top, self.width, self.height

    @property
    def max_width(self) -> int:
        return self._max_width

    @max_width.setter
    def max_width(self, value: int) -> None:
        self._max_width = value
        self._update_min_max()

    @property
    def max_height(self) -> int:
        return self._max_height

    @max_height.setter
    def max_height(self, value: int) -> None:
        self._max_height = value
        self._update_min_max()

    @property
    def binning(self) -> tuple[int, int]:
        return self._binning

    @QtCore.Slot(int, int)
    def set_binning(self, x: int, y: int) -> None:
        self._binning = (x, y)
        self._update_min_max()
        self.full_frame()

    @property
    def binned_width(self) -> int:
        return self._max_width // self.binning[0]

    @property
    def binned_height(self) -> int:
        return self._max_height // self.binning[1]

    @QtCore.Slot()
    def _update_min_max(self) -> None:
        self.spin_left.setMaximum(self.binned_width)
        self.spin_top.setMaximum(self.binned_height)
        self.spin_width.setMaximum(self.binned_width - self.spin_left.value())
        self.spin_height.setMaximum(self.binned_height - self.spin_top.value())

    @QtCore.Slot()
    def full_frame(self) -> None:
        self.spin_left.setValue(0)
        self.spin_top.setValue(0)
        self.spin_width.setValue(self.binned_width)
        self.spin_height.setValue(self.binned_height)

    def _emit_signal(self) -> None:
        self.window_changed.emit(
            self.spin_left.value(), self.spin_top.value(), self.spin_width.value(), self.spin_height.value()
        )
