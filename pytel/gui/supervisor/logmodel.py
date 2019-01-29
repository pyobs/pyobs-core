from colour import Color
from PyQt5 import QtCore, QtGui


class LogModel(QtCore.QAbstractTableModel):
    def __init__(self, *args):
        QtCore.QAbstractTableModel.__init__(self, *args)
        self._entries = []

    def rowCount(self, parent=None, *args, **kwargs):
        return len(self._entries)

    def columnCount(self, parent=None, *args, **kwargs):
        return 5

    def data(self, index: QtCore.QModelIndex, role=None):
        if role == QtCore.Qt.DisplayRole:
            # data to display
            d = self._entries[index.row()][index.column()]
            return d

        elif role == QtCore.Qt.TextColorRole and index.column() == 2:
            # text colors for log level
            return {
                'INFO': QtGui.QColor('lime'),
                'WARNING': QtGui.QColor('orange'),
                'ERROR': QtGui.QColor('red'),
                'DEBUG': QtGui.QColor('blue')
            }[self._entries[index.row()][index.column()]]

        elif role == QtCore.Qt.TextColorRole and index.column() == 1:
            # text colors for senders
            c = Color(pick_for=self._entries[index.row()][index.column()])
            return QtGui.QColor(c.hex)

        return QtCore.QVariant()

    def headerData(self, section: int, orientation, role=None):
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return ['Time', 'Source', 'Level', 'File', 'Message'][section]
        return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)

    @QtCore.pyqtSlot(list)
    def add_entry(self, entry):
        self.beginInsertRows(QtCore.QModelIndex(), len(self._entries), len(self._entries))
        self._entries.append(entry)
        self.endInsertRows()


class LogModelProxy(QtCore.QSortFilterProxyModel):
    def __init__(self, *args):
        QtCore.QSortFilterProxyModel.__init__(self, *args)
        self.setDynamicSortFilter(True)
        self.sort(0)
        self._filter_source = []

    def filterAcceptsRow(self, row: int, parent: QtCore.QModelIndex):
        # check sender
        index = self.sourceModel().index(row, 1, parent)
        sender = str(self.sourceModel().data(index, role=QtCore.Qt.DisplayRole))
        if sender in self._filter_source:
            return False

        # show it
        return True

    def filter_source(self, source: str, show: bool):
        if show and source in self._filter_source:
            self._filter_source.remove(source)
            self.invalidateFilter()
        elif not show and source not in self._filter_source:
            self._filter_source.append(source)
            self.invalidateFilter()


__all__ = ['LogModel', 'LogModelProxy']
