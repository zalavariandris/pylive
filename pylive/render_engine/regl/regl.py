from typing import *
import weakref
import moderngl
from pylive.render_engine.resource_manager import ResourceManager
from pylive.render_engine.camera import Camera


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


class Command(ResourceManager):
	def __init__(self, vert:str, frag:str, uniforms:Dict, attributes:Dict, count:int):
		super().__init__()
		self.vert = vert
		self.frag = frag
		self.uniforms = uniforms
		self.attributes = attributes
		self.count = count

		# GL OBJECTS
		self.vbo = None
		self.vao = None
		self.program:moderngl.Program = None

		# self.program(
		# 	vertex_shader=vert,
		# 	fragment_shader=frag,
		# )

	def setup(self):
		ctx = moderngl.get_context()

		self.prog = ctx.program(self.vert, self.frag)
		vertices = np.array([
			[-1,  0, 0],    # Vertex 1
			[ 0, -1, 0],    # Vertex 2
			[+1, +1, 0]   # Vertex 3
		], dtype=np.float32)
		self.vbo = ctx.buffer(vertices.tobytes())
		

	def __call__(self):
		# lazy setup
		if not (self.vbo and self.vao and self.prog):
			self.setup()

		assert self.prog
		# update uniforms
		for key, value in self.uniforms.items():
			self.prog[key].write(value)

		ctx = moderngl.get_context()
		vao = ctx.vertex_array(
			self.prog,
			[
				(self.vbo, '3f', 'position'),
			],
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
		
		def initializeGL(self):
			self.regl = REGL()

		def paint_with_moderngl(self):
			VERTEX_SHADER = dedent('''
				#version 330 core

				uniform mat4 view;
				uniform mat4 projection;


				layout(location = 0) in vec3 position;

				void main() {
					gl_Position = projection * view * vec4(position, 1.0);
				}
			''')

			FRAGMENT_SHADER = dedent('''
				#version 330 core

				layout (location = 0) out vec4 out_color;
				uniform vec4 color;
				void main() {
					out_color = color;
				}
			''')

			ctx = moderngl.get_context()
			program = ctx.program(VERTEX_SHADER, FRAGMENT_SHADER)
			program['projection'].write(glm.ortho(-1,1,-1,1,0,1))
			program['view'].write(glm.mat4(1))
			program['color'].write(glm.vec4(1.0, 1.0, 0.3, 1.0))
			# triangle
			vertices = np.array([
				[-1,  0, 0],    # Vertex 1
				[ 0, -1, 0],    # Vertex 2
				[+1, +1, 0]   # Vertex 3
			], dtype=np.float32)
			vbo = ctx.buffer(vertices.tobytes())

			vao = ctx.vertex_array(
				program,
				[
					(vbo, '3f', 'position'),
				],
				mode=moderngl.TRIANGLES
			)

			ctx.clear(1,.3,1,1)
			vao.render()

		def paint_with_regl(self):
			VERTEX_SHADER = dedent('''
				#version 330 core

				uniform mat4 view;
				uniform mat4 projection;


				layout(location = 0) in vec3 position;

				void main() {
					gl_Position = projection * view * vec4(position, 1.0);
				}
			''')

			FRAGMENT_SHADER = dedent('''
				#version 330 core

				layout (location = 0) out vec4 out_color;
				uniform vec4 color;
				void main() {
					out_color = color;
				}
			''')

			ctx = moderngl.get_context()
			draw_triangle = self.regl.command(
				vert=VERTEX_SHADER,
				frag=FRAGMENT_SHADER,

				uniforms={
					'projection': glm.ortho(-1,1,-1,1,0,1),
					'view': glm.mat4(1),
					'color': glm.vec4(0.0, 1.0, 0.3, 1.0)
				},

				attributes={
					'position': [
						[-1,  0, 0],
						[ 0, -1, 0],
						[+1, +1, 0]
					]
				},

				count=3
			)

			self.regl.clear(color=glm.vec4(0, 0.1, 0.26, 1))
			draw_triangle()


		def paintGL(self):
			ctx = moderngl.get_context()
			fbo = ctx.detect_framebuffer() 
			fbo.use()

			

			self.paint_with_regl()

			
	

	app = QApplication(sys.argv)

	canvas = Canvas()
	# camera = Camera()
	# camera.setPosition(glm.vec3(0, 1.5, 2.5))
	# camera.lookAt(glm.vec3(0,0,0), glm.vec3(0.0, 0.0, 1.0))
	# orbit_control = OrbitControl(canvas, camera)

	canvas.show()



	sys.exit(app.exec())

	# # itt should work like this:
	# canvas.render(lambda ctx: "whatever render function")
	# canvas.update()

	# # or like this
	# ctx = canvas.getContext()
	# regl = createRegl(ctx)
	# regl.command(...) # will update the opengl widget
