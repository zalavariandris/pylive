from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pylive.QtLiveApp.live_script_skeleton import LiveScriptWindow


class SupportLiveDisplay(Protocol):
	def _repr_html_(self)->str:
		...

	def _repr_latex_(self)->str:
		...

	def _repr_widfget_(self)->QWidget:
		...

def display(data):
	live = LiveScriptWindow.instance()
	live.display(data)