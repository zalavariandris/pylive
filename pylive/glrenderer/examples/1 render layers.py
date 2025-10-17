#%% setup
from PySide6.QtWidgets import *
from pylive.glrenderer.windows.qt_glwidget_using_moderngl import GLWidget

from pylive.glrenderer.utils.camera import Camera
from pylive.glrenderer.windows.orbitcontrol_for_qtwidget import OrbitControl
from pylive.glrenderer.gllayers.gllayers import RenderLayer, BoxLayer, TriangleLayer

import glm

#%% setup
glwidget = GLWidget()

app.setPreview(glwidget)

#%% update
camera = Camera()
camera.setPosition(glm.vec3(0, 1.5, 3.1))
camera.lookAt(glm.vec3(0,0,0), glm.vec3(0.0, 0.0, 1.0))
orbit_control = OrbitControl(glwidget, camera)

triangle = TriangleLayer(camera)
box = BoxLayer(camera)
glwidget.setRenderLayers([
	triangle,
	box
])
glwidget.update()

# %% set render layer


if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	glwidget.setRenderLayers(layers)
	glwidget.show()
	sys.exit(app.exec())
