from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtOpenGL import *
from OpenGL.GL import *
import numpy as np
from typing import *

import moderngl

class OpenGLWindow(QOpenGLWindow, QOpenGLFunctions):
	def __init__(self):
		super().__init__()
		self.shader_program = None
		self.vao = None  # Vertex Array Object
		self.vbo = None  # Vertex Buffer Object
	
	def initializeGL(self):

		# Vertex shader source
		self.vertex_shader = """
		#version 330 core
		layout(location = 0) in vec3 aPos;
		void main() {
			gl_Position = vec4(aPos, 1.0);
		}
		"""

		# Fragment shader source
		self.fragment_shader = """
		#version 330 core
		out vec4 FragColor;
		void main() {
			FragColor = vec4(1.0, 0.0, 0.0, 1.0);  // Red color
		}
		"""

		# Define the triangle's vertices (x, y, z)
		self.vertices = np.array([
			0.0,  0.5, 0.0,  # Top vertex
		   -0.5, -0.5, 0.0,  # Bottom-left vertex
			0.5, -0.5, 0.0   # Bottom-right vertex
		], dtype=np.float32)

		self.program = Program(Shader(self.vertex_shader, GL_VERTEX_SHADER)


	def paintGL(self):
		glClear(GL_COLOR_BUFFER_BIT)  # Clear the screen

		regl(
			program=self.program
			attributes={
				0: self.vertices
			},
			uniforms=None,
			count=0
		)

	def closeEvent(self, event):
		print("close")

	def resizeGL(self, w, h):
		"""Handle window resizing."""
		glViewport(0, 0, w, h)


if __name__ == "__main__":
	app = QApplication([])
	window = OpenGLWindow()
	window.resize(800, 600)
	window.show()
	app.exec()
