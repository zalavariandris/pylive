from typing import *

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtOpenGL import *

from pylive.render_engine.camera import Camera
import glm
class OrbitControl(QObject):
	def __init__(self, widget:QWidget, camera:Camera):
		super().__init__(parent=widget)
		self.camera = camera
		self._widget = widget
		self._widget.installEventFilter(self)

	def eventFilter(self, watched, event)->bool:
		if watched == self._widget:
			match event.type():
				case QEvent.Type.MouseButtonPress:
					event = cast(QMouseEvent, event)
					if event.button() == Qt.MouseButton.LeftButton:
						self.is_dragging = True
						self.last_mouse_pos = event.globalPosition()  # Store initial mouse position
					return True

				case QEvent.Type.MouseMove:
					event = cast(QMouseEvent, event)
					rotation_speed = 1.0

					if self.is_dragging:
						current_mouse_pos = event.globalPosition()  # Get current mouse position

						if self.last_mouse_pos is not None:
							# Calculate the change in mouse position (delta)
							delta = current_mouse_pos - self.last_mouse_pos
							self.camera.orbit(-delta.x(), -delta.y())

						# Update the last mouse position
						self.last_mouse_pos = current_mouse_pos
						return True

				case QEvent.Type.MouseButtonRelease:
					event = cast(QMouseEvent, event)
					if self.is_dragging:
						self.is_dragging = False
						self.last_mouse_pos = None  # Reset mouse position when dragging ends
					return True

				case QEvent.Type.Wheel:
					event = cast(QWheelEvent, event)
					distance = glm.distance(self.camera.getPosition(), glm.vec3(0,0,0))
					print(distance)
					self.camera.dolly(-event.angleDelta().y()/1000*distance)
					print("wheel", event.angleDelta())


				case QEvent.Type.Resize:
					widget = cast(QWidget, watched)
					self.camera.setAspectRation(widget.width()/widget.height())
		return False