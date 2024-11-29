import moderngl
import glm
import math
import time
import trimesh
import glm # or import pyrr !!!! TODO: checkout pyrr
import numpy as np
from OpenGL import GL as gl

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

class GLCanvas:
	def __init__(self):
		# Setup camera controls
		self.camera = Camera()
		self.camera.setPosition(glm.vec3(0, 1.5, 2.5))
		self.camera.lookAt(glm.vec3(0,0,0), glm.vec3(0.0, 0.0, 1.0))

	def initalizeGL(self):
		# Setup GL Context
		self.ctx = moderngl.get_context()

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

	def resizeGL(self, w, h):
		print("resizeGL", w, h)

	def paintGL(self):
		# update camera
		
		# render scene
		self.ctx.clear(0.1, 0.2, 0.3, 1.0)  # Clear screen with a color
		# self.ctx.enable(self.ctx.DEPTH_TEST)
		self.program['view'].write(self.camera.viewMatrix())
		self.program['projection'].write(self.camera.projectionMatrix())
		
		for vao in self.VAOs:
			vao.render()