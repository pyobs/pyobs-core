from qtpy import QtWidgets, QtCore


class BinningWidget(QtWidgets.QGroupBox):
    binning_changed = QtCore.Signal(int, int)

    def __init__(self, binnings: list[tuple[int, int]]) -> None:
        super().__init__()

        self._binnings = binnings

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.combo_binnings = QtWidgets.QComboBox()
        self.combo_binnings.addItems([f"{b[0]}x{b[1]}" for b in binnings])
        self.combo_binnings.setCurrentIndex(0)
        self.combo_binnings.currentIndexChanged.connect(self._binning_changed)
        layout.addRow("Binning:", self.combo_binnings)

    def _binning_changed(self, index: int) -> None:
        self.binning_changed.emit(*self._binnings[index])
