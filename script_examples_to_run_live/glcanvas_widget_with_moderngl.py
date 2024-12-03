from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
import moderngl
from pylive.render_engine.GLCanvasWidget_with_painting_signal import GLCanvasWidget

import sys
### create the app ###
app = QApplication.instance() or QApplication(sys.argv)
glcanvas = GLCanvasWidget()
glcanvas.show()
if __name__ == "__live__":
	live.setPreview(glcanvas)
ctx = None

#%% update
### define render function ###

from pylive.render_engine.utils import draw_triangle_with_moderngl
speed = 4.0
def paint():
	import time
	# QOpenGLWidget uses an internal FBO for drawing, use that with moderngl
	global ctx
	start_time = time.perf_counter_ns()
	if not ctx:
		ctx = moderngl.get_context()
		ctx.gc_mode = 'context_gc'
		print(time.perf_counter_ns()-start_time)
	fbo = ctx.detect_framebuffer()
	fbo.use()
	import math
	import time
	ctx.clear(0.5,.1,0.5,1)
	draw_triangle_with_moderngl(ctx, size=math.cos(time.time()*speed))
	ctx.gc()
	# connect continously, and request update
	glcanvas.painting.connect(paint, Qt.ConnectionType.SingleShotConnection)
	glcanvas.update() #request repaint continously

### set render function ###
glcanvas.painting.connect(paint, Qt.ConnectionType.SingleShotConnection)
glcanvas.update()
	
import inspect
print(inspect.getsource(sys.modules[__name__]))
app.exec()