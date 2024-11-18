from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtOpenGL import *
import moderngl
import glm
import math
import time
import trimesh
import glm # or import pyrr !!!! TODO: checkout pyrr
import numpy as np


from camera import Camera


FLAT_VERTEX_SHADER = '''
	#version 330 core

	uniform mat4 view;
	uniform mat4 projection;

	layout(location = 0) in vec3 position;

	void main() {
		gl_Position = projection * view * vec4(position, 1.0);
	}
'''

FLAT_FRAGMENT_SHADER = '''
	#version 330 core

	layout (location = 0) out vec4 out_color;

	void main() {
		out_color = vec4(1.0, 1.0, 1.0, 1.0);
	}
'''


class GLWindow(QOpenGLWindow):
	def initializeGL(self) -> None:
		super().initializeGL()


		# Setup GL Context
		self.ctx = moderngl.get_context()
		fmt = QSurfaceFormat()
		fmt.setDepthBufferSize(24);
		fmt.setStencilBufferSize(8);
		fmt.setSwapInterval(1)
		self.setFormat(fmt)

		# Setup camera controls
		self.camera = Camera()
		self.is_dragging = False
		self.camera.setPosition(glm.vec3(0, 1.5, 2.5))
		self.camera.lookAt(glm.vec3(0,0,0), glm.vec3(0.0, 0.0, 1.0))

		# Setup shaders
		self.program = self.ctx.program(
			vertex_shader=FLAT_VERTEX_SHADER,
			fragment_shader=FLAT_FRAGMENT_SHADER
		)

		### Setup VAOs ###
		self.VAOs = []

		# triangle
		vertices = np.array([
			 0.0, 0.0,  0.4,   # Vertex 1
			-0.4, 0.0, -0.3,   # Vertex 2
			 0.4, 0.0, -0.3    # Vertex 3
		], dtype=np.float32)

		vbo = self.ctx.buffer(vertices.tobytes())

		triangleVAO = self.ctx.vertex_array(
			self.program,
			[
				(vbo, '3f', 'position'),
			],
			mode=moderngl.TRIANGLES
		)
		self.VAOs.append(triangleVAO)

		# Trimesh Cube
		box = trimesh.creation.box(extents=(1, 1, 1))

		vertices = box.vertices.flatten().astype(np.float32)
		indices = box.faces.flatten().astype(np.uint32)
		vbo = self.ctx.buffer(vertices)
		ibo = self.ctx.buffer(indices)

		cubeVAO = self.ctx.vertex_array(
			self.program,
			[
				(vbo, '3f', 'position'),
			],
			mode=moderngl.POINTS,
			index_buffer=ibo
		)
		self.VAOs.append(cubeVAO)

		### Start Animation Loop ###
		self.timer = QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(1000//60)

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

	def mousePressEvent(self, event: QMouseEvent) -> None:
		if event.button() == Qt.LeftButton:
			self.is_dragging = True
			self.last_mouse_pos = event.globalPosition()  # Store initial mouse position

	def mouseMoveEvent(self, event: QMouseEvent) -> None:
		rotation_speed = 1.0
		if self.is_dragging:
			current_mouse_pos = event.globalPosition()  # Get current mouse position

			if self.last_mouse_pos is not None:
				# Calculate the change in mouse position (delta)
				delta_x = current_mouse_pos.x() - self.last_mouse_pos.x()
				delta_y = current_mouse_pos.y() - self.last_mouse_pos.y()

				self.camera.orbit(-delta_x, -delta_y)

			# Update the last mouse position
			self.last_mouse_pos = current_mouse_pos

	def mouseReleaseEvent(self, event: QMouseEvent) -> None:
		if event.button() == Qt.LeftButton:
			self.is_dragging = False
			self.last_mouse_pos = None  # Reset mouse position when dragging ends

	def paintGL(self) -> None:
		# update camera

		# render scene
		self.ctx.clear(0.1, 0.2, 0.3, 1.0)  # Clear screen with a color
		self.ctx.enable(self.ctx.DEPTH_TEST)
		self.program['view'].write(self.camera.viewMatrix())
		self.program['projection'].write(self.camera.projectionMatrix())
		
		for vao in self.VAOs:
			vao.render()

		# schedule next paint
		# self.update()


if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	window = GLWindow()
	window.setTitle("GLWindow boilerplate")

	window.resize(800, 600)
	window.show()
	sys.exit(app.exec())
