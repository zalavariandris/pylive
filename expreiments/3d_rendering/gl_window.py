from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtOpenGL import *


from gl_canvas import GLCanvas


class GLWindow(QOpenGLWindow):
	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self.canvas = GLCanvas()
		self.is_dragging = False

		### Start Animation Loop ###
		self.timer = QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(1000//60)

	def initializeGL(self) -> None:
		
		fmt = QSurfaceFormat()
		fmt.setDepthBufferSize(24);
		fmt.setStencilBufferSize(8);
		fmt.setSwapInterval(1)
		fmt.setMajorVersion(4)
		fmt.setMinorVersion(6)
		self.setFormat(fmt)
		self.canvas.initalizeGL()
		
		context = self.context()
		if context is not None and context.isValid():
			version = context.format().version()
			print(f"OpenGL Version Used by QOpenGLWindow: {version[0]}.{version[1]}")
		else:
			print("Failed to retrieve OpenGL context.")
	
	def event(self, event:QEvent):
		match event.type:
			case QEvent.Type.MouseButtonDblClick:
				...
			case QEvent.Type.Wheel:
				...
			case QEvent.Type.MouseButtonPress:
				...
			case QEvent.Type.MouseButtonRelease:
				...
			case QEvent.Type.MouseMove:
				...
			case QEvent.Type.MouseTrackingChange:
				...
			case QEvent.Type.NonClientAreaMouseButtonDblClick:
				...
			case QEvent.Type.NonClientAreaMouseButtonPress:
				...
			case QEvent.Type.NonClientAreaMouseButtonRelease:
				...
			case QEvent.Type.NonClientAreaMouseMove:
				...
			case QEvent.Type.Move:
				...
			case QEvent.Type.KeyPress:
				...
			case QEvent.Type.KeyRelease:
				...
			case QEvent.Type.Enter:
				...
			case QEvent.Type.Leave:
				...
			case QEvent.Type.DragEnter:
				...
			case QEvent.Type.DragLeave:
				...
			case QEvent.Type.DragMove:
				...
			case QEvent.Type.UpdateRequest:
				...
			case QEvent.Type.TouchBegin:
				...
			case QEvent.Type.TouchCancel:
				...
			case QEvent.Type.TouchEnd:
				...
			case QEvent.Type.TouchUpdate:
				...
			case QEvent.Type.TabletMove:
				...
			case QEvent.Type.TabletPress:
				...
			case QEvent.Type.TabletRelease:
				...
			case QEvent.Type.TabletEnterProximity:
				...
			case QEvent.Type.TabletLeaveProximity:
				...
			case QEvent.Type.TabletTrackingChange:
				...
			case QEvent.Type.Show:
				...
			case QEvent.Type.Hide:
				...
			case QEvent.Type.Resize:
				...
			
		return super().event(event)

	def mousePressEvent(self, event: QMouseEvent) -> None: #type:ignore
		if event.button() == Qt.MouseButton.LeftButton:
			self.is_dragging = True
			self.last_mouse_pos = event.globalPosition()  # Store initial mouse position

	def mouseMoveEvent(self, event: QMouseEvent) -> None: #type:ignore
		rotation_speed = 1.0
		if self.is_dragging:
			current_mouse_pos = event.globalPosition()  # Get current mouse position

			if self.last_mouse_pos is not None:
				# Calculate the change in mouse position (delta)
				delta_x = current_mouse_pos.x() - self.last_mouse_pos.x()
				delta_y = current_mouse_pos.y() - self.last_mouse_pos.y()

				self.canvas.camera.orbit(-delta_x, -delta_y)

			# Update the last mouse position
			self.last_mouse_pos = current_mouse_pos

	def mouseReleaseEvent(self, event: QMouseEvent) -> None: #type:ignore
		if event.button() == Qt.MouseButton.LeftButton:
			self.is_dragging = False
			self.last_mouse_pos = None  # Reset mouse position when dragging ends

	def resizeGL(self, w: int, h: int) -> None:
		self.canvas.resizeGL(w, h)
		return super().resizeGL(w, h)

	def paintGL(self) -> None:
		self.canvas.paintGL()

		# schedule next paint
		# self.update()


if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	
	window = GLWindow()


	window.resize(800, 600)
	window.show()
	sys.exit(app.exec())
