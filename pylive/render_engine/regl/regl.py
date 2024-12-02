from typing import *
import weakref
import moderngl
from pylive.render_engine.resource_manager import ResourceManager
from pylive.render_engine.camera import Camera


class Command(ResourceManager):
	def __init__(self, parent, *, vert:str, frag:str, uniforms:Dict, attributes:Dict, count:int):
		super().__init__()
		self.program(
			vertex_shader=vert,
			fragment_shader=frag,
		)

	def __call__(self):
		...


camera = Camera()
import glm
class REGL(ResourceManager):
	def command(self, vert:str, frag:str, uniforms:Dict, attributes:Dict, count:int):
		return Command(self,
			vert=vert,
			frag=frag,
			uniforms=uniforms,
			attributes=attributes,
			count=count)

	def clear(self, color:glm.vec4=glm.vec4(0,0,0,1)):
		pass

	def frame(self, callback:Callable):
		...


if __name__ == "__main__":
	import sys
	from PySide6.QtCore import *
	from PySide6.QtGui import *
	from PySide6.QtWidgets import *
	from PySide6.QtOpenGLWidgets import QOpenGLWidget

	from pylive.render_engine.orbit_control import OrbitControl
	from textwrap import dedent
	class Canvas(QOpenGLWidget):
		def __init__(self, parent=None):
			super().__init__(parent=parent)
			self._context = None
		
		def initializeGL(self):
			self._context = moderngl.get_context()
			self.regl = REGL()

		def getContext(self)->moderngl.Context:
			if not self._context:
				raise RuntimeError("context was not initialized")
			return self._context

		def paintGL(self):
			print("paintGL")
			draw_triangle = self.regl.command(
				vert=dedent("""\
				precision mediump float;
				attribute vec2 position;
				void main () {
					gl_Position = vec4(position, 0, 1);
				}
				"""),

				frag=dedent("""\
				precision mediump float;
				uniform vec4 color;
				void main () {
					gl_FragColor = color;
				}"""),

				uniforms={
					'view': camera.viewMatrix(),
					'projection': camera.projectionMatrix(),
					'color': glm.vec4(1.0, 1.0, 0.3, 1.0)
				},

				attributes={
					'position': [
						[-1, 0],
						[0, -1],
						[1, 1]
					]
				},

				count=3
			)
			fbo = self.regl.mgl().detect_framebuffer() 
			fbo.use()
			self.regl.clear(color=glm.vec4(0, 0.1, 0.26, 1))
			draw_triangle()
	

	app = QApplication(sys.argv)

	canvas = Canvas()
	# camera = Camera()
	# camera.setPosition(glm.vec3(0, 1.5, 2.5))
	# camera.lookAt(glm.vec3(0,0,0), glm.vec3(0.0, 0.0, 1.0))
	# orbit_control = OrbitControl(canvas, camera)

	canvas.show()

	sys.exit(app.exec())
