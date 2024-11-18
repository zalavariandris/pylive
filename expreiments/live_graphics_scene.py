from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from pylive import livescript
from typing import *

print("Hello World")

import math

class DAGScene(QGraphicsScene):
	def __init__(self):
		super().__init__(parent=None)
		
		rect = QGraphicsRectItem( QRectF(0,0,100,100 ) )
		rect.setBrush(Qt.red)
		self.addItem(rect)
		self.rect = rect
		
		timer = QTimer(self)
		timer.timeout.connect(self.animate)
		timer.start(1000.0/60.0)
		
	def animate(self):
		import time
		#print("animate", time.time())
		pos = QPointF(0,100*math.sin(time.time()*4))
		self.rect.setPos(pos)

if __name__ == "__live__":
	view = QGraphicsView()
	view.setScene(DAGScene())
	from pylive.preview_widget import PreviewWidget
	preview = PreviewWidget.instance()
	preview.display(view)

if __name__ == "__main__":
	...