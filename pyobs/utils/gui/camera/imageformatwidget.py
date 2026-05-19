from qtpy import QtWidgets, QtCore

from pyobs.utils.enums import ImageFormat


class ImageFormatWidget(QtWidgets.QGroupBox):
    format_changed = QtCore.Signal(ImageFormat)

    def __init__(self, formats: list[ImageFormat]) -> None:
        super().__init__()

        self._formats = formats

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.combo_formats = QtWidgets.QComboBox()
        self.combo_formats.addItems([f"{f.name}" for f in formats])
        self.combo_formats.setCurrentIndex(0)
        self.combo_formats.currentIndexChanged.connect(self._format_changed)
        layout.addRow("Format:", self.combo_formats)

    @property
    def value(self) -> ImageFormat:
        return self._formats[self.combo_formats.currentIndex()]

    def _format_changed(self, index: int) -> None:
        self.format_changed.emit(self._formats[index])
