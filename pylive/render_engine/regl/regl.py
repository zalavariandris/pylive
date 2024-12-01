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


regl = REGL()

draw_triangle = regl.command(
	vert="",
	frag="",
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

# Continuously updates
def animate():
	regl.clear(color=glm.vec4(0, 0.1, 0.26, 1))
	# draw_triangle()

regl.frame(lambda: animate())