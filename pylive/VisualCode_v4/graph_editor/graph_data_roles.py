from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from enum import IntEnum

class GraphDataRole(IntEnum):
	LinkSourceRole = Qt.ItemDataRole.UserRole+1
	LinkTargetRole = Qt.ItemDataRole.UserRole+2
	NodeInletsRole = Qt.ItemDataRole.UserRole+3
	NodeOutletsRole = Qt.ItemDataRole.UserRole+4