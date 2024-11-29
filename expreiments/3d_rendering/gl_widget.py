from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtOpenGL import *
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from OpenGL import GL as gl
from gl_canvas import GLCanvas


class GLWidget(QOpenGLWidget):
	def __init__(self, parent=None):
		fmt = QSurfaceFormat()
		fmt.setDepthBufferSize(24);
		fmt.setStencilBufferSize(8);
		fmt.setSwapInterval(1)

		super().__init__(parent=parent)
		self.canvas = GLCanvas()
		self.is_dragging = False

		
		

		### Start Animation Loop ###
		self.timer = QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(1000//60)

	def initializeGL(self) -> None:
		self.canvas.initalizeGL()

		context = self.context()
		if context is not None and context.isValid():
			version = context.format().version()
			print(f"OpenGL Version Used by QOpenGLWidget: {version[0]}.{version[1]}")
		else:
			print("Failed to retrieve OpenGL context.")

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

	def paintGL(self) -> None:
		# gl.glClearColor(0.2, 0.2, 0.4, 1)
		# gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
		self.canvas.paintGL()

		# schedule next paint
		# self.update()


if __name__ == "__main__":
	import sys
	fmt = QSurfaceFormat()
	fmt.setVersion(4,6)
	fmt.setDepthBufferSize(24);
	fmt.setStencilBufferSize(8);
	fmt.setSwapInterval(1)
	QSurfaceFormat.setDefaultFormat(fmt)
	QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL)
	app = QApplication(sys.argv)
	window = GLWidget()


	window.resize(800, 600)
	window.show()
	sys.exit(app.exec())
