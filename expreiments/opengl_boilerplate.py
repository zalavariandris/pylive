from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtOpenGL import *
from OpenGL.GL import *
import numpy as np
from typing import *


class Shader:
	"""
	GL_VERTEX_SHADER
	GL_FRAGMENT_SHADER
	"""
	def __init__(self, shader_source:str, shader_type):
		self.shader_source = shader_source
		self.shader_type = shader_type

		shader_id = glCreateShader(self.shader_type)
		glShaderSource(shader_id, self.shader_source)
		glCompileShader(shader_id)
		
		# Check for shader compile errors
		success = glGetShaderiv(shader_id, GL_COMPILE_STATUS)
		if not success:
			info_log = glGetShaderInfoLog(shader_id).decode()
			raise RuntimeError(f"Shader compilation failed: {info_log}")
		
		self.shader_id = shader_id


class Program:
	def __init__(self, vertexShader, fragmentShader):
		self.vertexShader = vertexShader
		self.fragmentShader = fragmentShader
		program_id = glCreateProgram()
		glAttachShader(program_id, vertex_shader_id)
		glAttachShader(program_id, fragment_shader_id)
		glLinkProgram(program_id)

		# Check for linking errors
		success = glGetProgramiv(program_id, GL_LINK_STATUS)
		if not success:
			info_log = glGetProgramInfoLog(program_id).decode()
			raise RuntimeError(f"Program linking failed: {info_log}")
		self.program_id = program_id

	def use(self):
		glUseProgram(self.program_id)



def regl(frag:str, vert:str, attributes:dict, uniforms: dict, count:int):
	# Init
	# Compile the shaders
	vertex_shader_id = compileShader(vert, GL_VERTEX_SHADER)
	fragment_shader_id = compileShader(frag, GL_FRAGMENT_SHADER)

	# Link shaders to create the program
	shader_program = createShaderProgram(vertex_shader_id, fragment_shader_id)

	# Create and bind the VAO (Vertex Array Object)
	vao = glGenVertexArrays(1)
	glBindVertexArray(vao)

	# Create and bind the VBO (Vertex Buffer Object)
	vbo = glGenBuffers(1)
	glBindBuffer(GL_ARRAY_BUFFER, vbo)

	# Load the vertices into the buffer
	vertices = attributes[0]
	glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

	# Define the vertex attribute (how to interpret the data)
	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * vertices.itemsize, ctypes.c_void_p(0))
	glEnableVertexAttribArray(0)

	# Unbind the VBO and VAO
	glBindBuffer(GL_ARRAY_BUFFER, 0)
	glBindVertexArray(0)
	
	# Paint
	# Use the shader program
	glUseProgram(shader_program)

	# Bind the VAO (Vertex Array Object)
	glBindVertexArray(vao)

	# Draw the triangle
	glDrawArrays(GL_TRIANGLES, 0, 3)

	# Unbind the VAO
	glBindVertexArray(0)



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


	def paintGL(self):
		glClear(GL_COLOR_BUFFER_BIT)  # Clear the screen

		regl(
			frag=self.fragment_shader,
			vert=self.vertex_shader,
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
