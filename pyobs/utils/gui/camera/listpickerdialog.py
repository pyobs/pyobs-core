from qtpy import QtWidgets  # type: ignore


class ListPickerDialog(QtWidgets.QDialog):  # type: ignore
    def __init__(self, items: list[str]):
        super().__init__()

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.combo_box = QtWidgets.QComboBox()
        self.combo_box.addItems(items)
        layout.addWidget(self.combo_box)

        self.button = QtWidgets.QPushButton("ok")
        layout.addWidget(self.button)
        self.button.clicked.connect(self.accept)

    def comboBox(self) -> QtWidgets.QComboBox:
        return self.combo_box
