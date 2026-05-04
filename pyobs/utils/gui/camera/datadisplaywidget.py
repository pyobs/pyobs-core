from qtpy import QtWidgets, QtCore
from qfitswidget import QFitsWidget
from astropy.io import fits
import os


class DataDisplayWidget(QtWidgets.QWidget):
    signal_update_gui = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()

        self.vertical_layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.vertical_layout)
        self.tab_widget = QtWidgets.QTabWidget()
        self.vertical_layout.addWidget(self.tab_widget)

        # image
        self.fits_widget = QFitsWidget()
        self.tab_widget.addTab(self.fits_widget, "Image")

        # fits header
        self.tab_fits_header = QtWidgets.QWidget()
        self.tab_fits_header_layout = QtWidgets.QVBoxLayout(self.tab_fits_header)
        self.tab_fits_header_layout.setContentsMargins(0, 0, 0, 0)
        self.table_fits_header = QtWidgets.QTableWidget(self.tab_fits_header)
        self.table_fits_header.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_fits_header.setAlternatingRowColors(True)
        self.table_fits_header.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.table_fits_header.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_fits_header.horizontalHeader().setStretchLastSection(True)
        self.table_fits_header.verticalHeader().setVisible(False)
        self.tab_fits_header_layout.addWidget(self.table_fits_header)
        self.tab_widget.addTab(self.tab_fits_header, "FITS header")

        # toolbar
        self.toolbar_layout = QtWidgets.QHBoxLayout()
        self.check_auto_save = QtWidgets.QCheckBox("Auto save:")
        self.toolbar_layout.addWidget(self.check_auto_save)
        self.text_autosave_path = QtWidgets.QLineEdit()
        self.text_autosave_path.setEnabled(False)
        self.toolbar_layout.addWidget(self.text_autosave_path)
        self.button_autosave = QtWidgets.QToolButton()
        self.button_autosave.setText("...")
        self.button_autosave.setEnabled(False)
        self.toolbar_layout.addWidget(self.button_autosave)
        self.toolbar_spacer = QtWidgets.QSpacerItem(
            40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum
        )
        self.toolbar_layout.addItem(self.toolbar_spacer)
        self.button_save_to = QtWidgets.QToolButton()
        self.button_save_to.setText("Save to...")
        self.button_save_to.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.button_save_to.setEnabled(False)
        self.toolbar_layout.addWidget(self.button_save_to)
        self.vertical_layout.addLayout(self.toolbar_layout)
        self.tab_widget.setCurrentIndex(0)

        # set headers for fits header tab
        self.table_fits_header.setColumnCount(3)
        self.table_fits_header.setHorizontalHeaderLabels(["Key", "Value", "Comment"])

        # connect signals
        # self.signal_update_gui.connect(self.update_gui)
        self.check_auto_save.stateChanged.connect(lambda x: self.text_autosave_path.setEnabled(x))
        self.check_auto_save.stateChanged.connect(lambda x: self.button_autosave.setEnabled(x))
        self.button_autosave.clicked.connect(self.select_autosave_path)
        self.button_save_to.clicked.connect(self.save_data)

        # variables
        self._count = 0
        self.data: fits.ImageHDU | None = None

    def set_data(self, data: fits.ImageHDU) -> None:
        """Show data."""
        self.button_save_to.setEnabled(True)
        self.data = data
        self.data.header["FNAME"] = f"image_{self._count:04d}.fits"
        self._count += 1
        self.fits_widget.display(self.data)
        self._show_fits_headers()
        if self.check_auto_save.isChecked():
            self._auto_save()

    def _show_fits_headers(self) -> None:
        # get all header cards
        headers = {}
        for card in self.data.header.cards:
            headers[card.keyword] = (card.value, card.comment)

        # prepare table
        self.table_fits_header.setRowCount(len(headers))

        # set headers
        for i, key in enumerate(sorted(headers.keys())):
            self.table_fits_header.setItem(i, 0, QtWidgets.QTableWidgetItem(key))
            self.table_fits_header.setItem(i, 1, QtWidgets.QTableWidgetItem(str(headers[key][0])))
            self.table_fits_header.setItem(i, 2, QtWidgets.QTableWidgetItem(headers[key][1]))

        # adjust column widths
        self.table_fits_header.resizeColumnToContents(0)
        self.table_fits_header.resizeColumnToContents(1)

    def _auto_save(self) -> None:
        # autosave?
        path = self.text_autosave_path.text()

        # get path and check
        if not os.path.exists(path):
            print("Invalid path for auto-saving.")

        else:
            # save image
            filename = os.path.join(path, self.data.header["FNAME"])
            fits.writeto(filename, self.data.data, self.data.header, overwrite=True)

    @QtCore.Slot()  # type: ignore
    def select_autosave_path(self) -> None:
        """Select path for auto-saving."""

        # ask for path
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")

        # set it
        if path:
            self.text_autosave_path.setText(path)
        else:
            self.text_autosave_path.clear()

    @QtCore.Slot()  # type: ignore
    def save_data(self) -> None:
        """Save image."""

        # get initial filename
        init_filename = "image.fits"

        # ask for filename
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save image", init_filename, "FITS Files (*.fits *.fits.gz)"
        )

        # save
        if filename:
            fits.writeto(filename, self.data.data, self.data.header, overwrite=True)
