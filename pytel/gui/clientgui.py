from PyQt5 import QtWidgets, QtCore, QtGui
import logging


class ClientGui(QtWidgets.QMainWindow, logging.Handler):
    def __init__(self, *args, **kwargs):
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        logging.Handler.__init__(self, *args, **kwargs)

        # basic stuff
        self.setWindowTitle("pytel")
        self.resize(900, 500)

        # main menu
        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')
        fileMenu.addAction('E&xit', self.close)

        # add QPlainTextEdit
        self.log = QtWidgets.QTextBrowser(self)
        self.setCentralWidget(self.log)

        # font
        font = QtGui.QFont()
        font.setPointSize(12)
        self.log.setFont(font)

        # create log handler
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s')
        logging.root.addHandler(self)
        self.setFormatter(formatter)

    def emit(self, record):
        log_entry = self.format(record)
        self.log.append(log_entry)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
