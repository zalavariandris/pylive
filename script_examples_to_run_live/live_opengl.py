#%% setup
from typing import *
from PySide6.QtOpenGLWidgets import QOpenGLWidget
import moderngl



class Canvas(QOpenGLWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self._context = None
	
	def initializeGL(self):
		self._context = moderngl.get_context()

	def getContext(self)->moderngl.Context:
		if not self._context:
			raise RuntimeError("context was not initialized")
		return self._context

	def paintGL(self):
		...

canvas = Canvas()
app.setPreview(canvas)

#%% update
print("hello")
from pylive.render_engine.render_layers import RenderLayer
from pylive.render_engine.camera import Camera
from textwrap import dedent

class Triangle:
	FLAT_VERTEX_SHADER = dedent('''
		#version 330 core

		uniform mat4 view;
		uniform mat4 projection;


		layout(location = 0) in vec3 position;

		void main() {
			gl_Position = projection * view * vec4(position, 1.0);
		}
	''')

	FLAT_FRAGMENT_SHADER = dedent('''
		#version 330 core

		layout (location = 0) out vec4 out_color;
		uniform vec4 color;
		void main() {
			out_color = color;
		}
	''')
	def __init__(self, ctx, camera:Camera|None=None) -> None:
		super().__init__()
		self.camera = camera or Camera()
		self.program = None
		self.ctx = ctx

	def setup(self):
	    
		self.program = self.ctx.program(
			vertex_shader=self.FLAT_VERTEX_SHADER,
			fragment_shader=self.FLAT_FRAGMENT_SHADER
		)

		# triangle
		vertices = np.array([
			 0.0, 0.0,  0.4,   # Vertex 1
			-0.4, 0.0, -0.3,   # Vertex 2
			 0.4, 0.0, -0.3    # Vertex 3
		], dtype=np.float32)

		self.vbo = ctx.buffer(vertices.tobytes())

		self.vao = ctx.vertex_array(
			self.program,
			[
				(self.vbo, '3f', 'position'),
			],
			mode=moderngl.TRIANGLES
		)

	def destroy(self):
		if self.program:
			self.program.release()
		if self.vbo:
			self.vbo.release()
		if self.vao:
			self.vao.release()

	def render(self, ctx:moderngl.Context):
		if not self.program:
			self.setup()
		assert self.program
		self.program['view'].write(self.camera.viewMatrix())
		self.program['projection'].write(self.camera.projectionMatrix())
		self.program['color'].write(glm.vec4(1.0, 1.0, 0.3, 1.0))
		self.vao.render()

camera = Camera()
ctx = canvas.getContext()
fbo = ctx.detect_framebuffer()
triangle = Triangle(ctx, camera)

