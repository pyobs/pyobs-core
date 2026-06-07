import logging
from typing import Any

# PySide is no requirement for pyobs-core...
try:
    from PySide6 import QtGui, QtWidgets

    class ModuleGui(QtWidgets.QMainWindow, logging.Handler):  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any):
            QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
            logging.Handler.__init__(self, *args, **kwargs)

            # basic stuff
            self.setWindowTitle("pytel")
            self.resize(900, 500)

            # main menu
            menu_main = self.menuBar()
            menu_file = menu_main.addMenu("&File")
            menu_file.addAction("E&xit", self.close)

            # add QPlainTextEdit
            self.log = QtWidgets.QTextBrowser(self)
            self.setCentralWidget(self.log)

            # font
            font = QtGui.QFont()
            font.setPointSize(12)
            self.log.setFont(font)

            # create log handler
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s")
            logging.root.addHandler(self)
            self.setFormatter(formatter)

        def emit(self, record: logging.LogRecord) -> None:  # type: ignore
            # format entry
            log_entry = self.format(record)  # noqa: UP031

            # colors?
            if "[ERROR]" in log_entry:
                log_entry = f'<font color="red">{log_entry}</font>'
            elif "[WARNING]" in log_entry:
                log_entry = f'<font color="orange">{log_entry}</font>'

            # append to log
            self.log.append(log_entry)

            # scroll to end
            self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

except ImportError:
    pass
