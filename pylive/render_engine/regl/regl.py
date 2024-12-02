from typing import *
import weakref

from numpy import dtype
import moderngl
from pylive.render_engine.resource_manager import ResourceManager
from pylive.render_engine.camera import Camera
from OpenGL.GL import *

camera = Camera()
import glm
class REGL(ResourceManager):
	def command(self, vert:str, frag:str, uniforms:Dict, attributes:Dict, count:int):
		return Command(vert=vert,
			frag=frag,
			uniforms=uniforms,
			attributes=attributes,
			count=count)

	def clear(self, color:glm.vec4=glm.vec4(0,0,0,1)):
		ctx = moderngl.get_context()
		ctx.clear(1,.3,1,1)

	def frame(self, callback:Callable):
		""" for animation? """
		...

from dataclasses import dataclass
class Command:
	def __init__(self, vert:str, frag:str, uniforms:Dict, attributes:Dict, count:int):
		super().__init__()
		self.vert = vert
		self.frag = frag
		self.uniforms = uniforms
		self.attributes = attributes
		self.count = count

		# GL OBJECTS
		self.vao = None
		self.buffers = []
		self.program:moderngl.Program = None

	def _lazy_setup(self):
		ctx = moderngl.get_context()

		self.program = ctx.program(self.vert, self.frag)


		self.buffers = [
			(
				ctx.buffer(buffer.tobytes()), 
				f"{buffer.shape[1]}{buffer.dtype.char}", 
				name
			)
			for name, buffer in self.attributes.items()
		]

	def __del__(self):
		for buffer, type_string, name in self.buffers:
			buffer.release()
		if vao:=self.vao:
			vao.release()
		if program:=self.program:
			program.release()

	def validate_uniforms(self):
		for uniform in self.uniforms.values():
			... #TODO: Validate uniform values. allow tuples, numpy arrays and glm values.

	def validate_attributes(self):
		if not all(isinstance(buffer, np.ndarray) or isinstance(buffer, list) for buffer in self.attributes.values()):
			raise ValueError(f"All buffer must be np.ndarray or a List, got:{self.attributes.values()}")

		if not all(len(buffer.shape) == 2 for buffer in self.attributes.values()):
			# see  opengl docs: https://registry.khronos.org/OpenGL-Refpages/gl4/html/glVertexAttribPointer.xhtml
			# size must be aither 1,2,3 or 4
			raise ValueError(f"The buffers must be 2 dimensional.") #TODO: accep 1 or a flat array for 1 dimensional data.

		if not all(buffer.shape[1] in {1,2,3,4} for buffer in self.attributes.values()):
			# see  opengl docs: https://registry.khronos.org/OpenGL-Refpages/gl4/html/glVertexAttribPointer.xhtml
			# size must be aither 1,2,3 or 4
			raise ValueError(f"The number of components per generic vertex attribute. Must be 1, 2, 3, or 4.")

		supported_datatypes = {'f','u'}
		for buffer in self.attributes.values():
			if buffer.dtype.char not in supported_datatypes:
				raise ValueError(f"Datatype '{buffer.dtype}' is not supported.")

	def __call__(self):
		# lazy setup
		if not (self.buffers and self.vao and self.program):
			self._lazy_setup()

		# validate input parameters
		self.validate_uniforms()
		self.validate_attributes()

		assert self.program
		# update uniforms
		for key, value in self.uniforms.items():
			self.program[key].write(value)

		ctx = moderngl.get_context()

		# reorganize buffers for modenrgl format

		# create vao
		vao = ctx.vertex_array(
			self.program,
			self.buffers,
			mode=moderngl.TRIANGLES
		)
		vao.render()
		

if __name__ == "__main__":
	import sys
	from PySide6.QtCore import *
	from PySide6.QtGui import *
	from PySide6.QtWidgets import *
	from PySide6.QtOpenGLWidgets import QOpenGLWidget
	import numpy as np
	from pylive.render_engine.orbit_control import OrbitControl
	from textwrap import dedent

	

	class Canvas(QOpenGLWidget):
		def __init__(self, parent=None):
			super().__init__(parent=parent)
			self.regl = REGL()

		
		def initializeGL(self):
			...

		def paintGL(self):
			# ctx = moderngl.get_context()
			# fbo = ctx.detect_framebuffer() 
			# print(fbo)
			# fbo.use()
			# print("viewport", ctx.viewport)

			# draw_triangle()
			# self.paint_with_regl()
			print("painGL")
			# glClearColor(0.1, 0.1, 0.1, 1.0)  # Dark background
			# glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

		def drawTriangle(self):
			print("drawTriangle")
			# Step 1: Make the context current
			self.makeCurrent()

			try:
				# Step 2: Set up the ModernGL context
				ctx = moderngl.get_context()

				# Step 3: Configure the viewport to match widget size
				# ctx.viewport = (0, 0, self.width(), self.height())

				# Step 4: Bind the default framebuffer
				fbo_handle = self.defaultFramebufferObject()
				fbo = ctx.detect_framebuffer()
				print('fbo.glo', fbo.glo)
				fbo.use()

				# Step 5: Call the custom render function
				draw_triangle()
				

				self.context().swapBuffers(self.context().surface())
				
			finally:
				# Step 6: Release the context
				self.doneCurrent()
				...
			self.update()


	app = QApplication(sys.argv)

	canvas = Canvas()

	draw_triangle = canvas.regl.command(
		vert=dedent('''\
			#version 330 core

			uniform mat4 view;
			uniform mat4 projection;


			layout(location = 0) in vec3 position;

			void main() {
				gl_Position = projection * view * vec4(position, 1.0);
			}
		'''),
		frag=dedent('''
			#version 330 core

			layout (location = 0) out vec4 out_color;
			uniform vec4 color;
			void main() {
				out_color = color;
			}
		'''),

		uniforms={
			'projection': glm.ortho(-1,1,-1,1,0,1),
			'view': glm.mat4(1),
			'color': glm.vec4(0.0, 1.0, 0.3, 1.0)
		},

		attributes={
			'position': np.array([
				[-1,  0, 0],
				[ 0, -1, 0],
				[+1, +1, 0]
			], dtype=np.float32)
		},

		count=3
	)


	# camera = Camera()
	# camera.setPosition(glm.vec3(0, 1.5, 2.5))
	# camera.lookAt(glm.vec3(0,0,0), glm.vec3(0.0, 0.0, 1.0))
	# orbit_control = OrbitControl(canvas, camera)

	canvas.show()

	canvas.drawTriangle()


	sys.exit(app.exec())

	# # itt should work like this:
	# canvas.render(lambda ctx: "whatever render function")
	# canvas.update()

	# # or like this
	# ctx = canvas.getContext()
	# regl = createRegl(ctx)
	# regl.command(...) # will update the opengl widget
