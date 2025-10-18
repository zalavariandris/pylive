"""
TODO:
- update the modderngl window example with a camera control, by using the new __call__ overrides
- create an imgui example, where the ResourceManager resources, cache, buffers etc are visualized in realtime.
- use Regl.__call__ to execute commands?
- VAO caching: per-command dictionary keyed by (program, buffer ids, attribute names)
- clear cached weak refs each frame?
- implement the frame method for animation?
- consider using VAO and Program resource objects
"""

from typing import *
import weakref

from numpy import dtype
import moderngl
from pylive.glrenderer.regl.command import Command
from pylive.glrenderer.regl.resource_manager import ResourceManager
from pylive.glrenderer.utils.camera import Camera
from OpenGL.GL import *

camera = Camera()
import glm
import textwrap

class REGL(ResourceManager):
	def command(self, *, vert:str, frag:str, uniforms:Dict, attributes:Dict, count:int, framebuffer:moderngl.Framebuffer=None):
		return Command(
			vert=vert,
			frag=frag,
			uniforms=uniforms,
			attributes=attributes,
			count=count,
			framebuffer=framebuffer
		)

	def clear(self, color:glm.vec4=glm.vec4(0,0,0,1)):
		ctx = moderngl.get_context()
		ctx.clear(1,.3,1,1)

	def frame(self, callback:Callable):
		""" for animation? """
		...


if __name__ == "__main__":
	from textwrap import dedent
	import numpy as np
	
	regl = REGL()
	# create draw triangle command
	draw_triangle = regl.command(
		vert='''\
			#version 410 core

			uniform mat4 view;
			uniform mat4 projection;

			layout(location = 0) in vec3 position;

			void main() {
				gl_Position = projection * view * vec4(position, 1.0);
			}
		''',
		frag='''
			#version 410 core

			layout (location = 0) out vec4 out_color;
			uniform vec4 color;
			
			void main() {
				out_color = color;
			}
		''',

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

# if __name__ == "__main__":
# 	import sys
# 	from PySide6.QtCore import *
# 	from PySide6.QtGui import *
# 	from PySide6.QtWidgets import *
# 	from PySide6.QtOpenGLWidgets import QOpenGLWidget
# 	import numpy as np
# 	from pylive.glrenderer.windows.orbitcontrol_for_qtwidget import OrbitControl
# 	from textwrap import dedent
# 	from collections import defaultdict

# 	class ExampleGLCanvasWidget(QOpenGLWidget):
# 		def __init__(self, commands:List[Command]=[], parent=None):
# 			super().__init__(parent=parent)
# 			self._draw_commands = commands

# 		def initializeGL(self):
# 			ctx = moderngl.get_context()
# 			print(f"OpenGL Version: {ctx.version_code}")
# 			print(f"OpenGL Vendor: {ctx.info['GL_VENDOR']}")
# 			print(f"OpenGL Renderer: {ctx.info['GL_RENDERER']}")

# 		def paintGL(self):
# 			ctx = moderngl.get_context()
# 			fbo = ctx.detect_framebuffer()
# 			fbo.use()
			
# 			# Clear the screen
# 			ctx.clear(0.1, 0.1, 0.1, 1.0)
			
# 			# Execute the draw command
# 			for paintgl in self._draw_commands:
# 				paintgl()

# 	app = QApplication(sys.argv)

# 	# Set default OpenGL format before creating widgets - 4.1 is max on macOS
# 	format = QSurfaceFormat()
# 	format.setVersion(4, 1)
# 	format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
# 	format.setDepthBufferSize(24)
# 	format.setStencilBufferSize(8)
# 	format.setSamples(4)  # Enable 4x MSAA for smoother edges
# 	QSurfaceFormat.setDefaultFormat(format)

# 	# create drawable canvas widget
	
# 	regl = REGL()
# 	# create draw triangle command
# 	draw_triangle = regl.command(
# 		vert=dedent('''\
# 			#version 410 core

# 			uniform mat4 view;
# 			uniform mat4 projection;

# 			layout(location = 0) in vec3 position;

# 			void main() {
# 				gl_Position = projection * view * vec4(position, 1.0);
# 			}
# 		'''),
# 		frag=dedent('''
# 			#version 410 core

# 			layout (location = 0) out vec4 out_color;
# 			uniform vec4 color;
			
# 			void main() {
# 				out_color = color;
# 			}
# 		'''),

# 		uniforms={
# 			'projection': glm.ortho(-1,1,-1,1,0,1),
# 			'view': glm.mat4(1),
# 			'color': glm.vec4(0.0, 1.0, 0.3, 1.0)
# 		},

# 		attributes={
# 			'position': np.array([
# 				[-1,  0, 0],
# 				[ 0, -1, 0],
# 				[+1, +1, 0]
# 			], dtype=np.float32)
# 		},

# 		count=3
# 	)

# 	canvas = ExampleGLCanvasWidget(commands=[
# 		draw_triangle
# 	])


# 	# camera = Camera()
# 	# camera.setPosition(glm.vec3(0, 1.5, 2.5))
# 	# camera.lookAt(glm.vec3(0,0,0), glm.vec3(0.0, 0.0, 1.0))
# 	# orbit_control = OrbitControl(canvas, camera)

# 	canvas.show()
# 	# canvas.add_draw_commands('paintgl', draw_triangle)
# 	sys.exit(app.exec())
