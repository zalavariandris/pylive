from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from pylive.utils.qtfactory import vboxlayout

from pylive.utils.diff import diff_dict

from dataclasses import dataclass




if __name__ == "__main__":
	app = QApplication()
	_qapp = QApplication.instance()

	# widget = QLabel("main")
	# widget.show()

	# self._qapp.exec()
	app.exec()
