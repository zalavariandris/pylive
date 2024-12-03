from typing import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from OpenGL.GL import *  # PyOpenGL bindings
from PySide6.QtOpenGL import *

import numpy as np

from pylive.render_engine.utils import draw_triangle_with_qopengl


class GLWindow(QOpenGLWindow):
    def __init__(self, parent=None):
        super().__init__()
        # self.gllayer = GLLayer(parent=self)

    def sizeHint(self) -> QSize:
        return QSize(800,600)

    def initializeGL(self):
        ...

    def paintGL(self):
        draw_triangle_with_qopengl(self, 1.0)

    def resizeGL(self, w, h):
        """Handle widget resizing."""
        glViewport(0, 0, w, h)
        print(f"Viewport resized to {w}x{h}.")


# class GLCanvasWindow(QWindow, QOpenGLFunctions):
#     vertexShaderSource = """\
#         attribute highp vec4 posAttr;
#         attribute lowp vec4 colAttr;
#         varying lowp vec4 col;
#         uniform highp mat4 matrix;
#         void main() {
#            col = colAttr;
#            gl_Position = matrix * posAttr;
#         }"""

#     fragmentShaderSource = """\
#         varying lowp vec4 col;
#         void main() {
#             gl_FragColor = col;
#         }"""

#     def __init__(self, parent=None):
#         QWindow.__init__(self, parent)
#         QOpenGLFunctions.__init__(self)

#         self.context:QOpenGLContext = None
#         self.device:QOpenGLPaintDevice = None
#         self.animating:bool = False
#         self.setSurfaceType(QWindow.OpenGLSurface)

#     def sizeHint(self):
#         return QSize(256,256)

#     def renderPainter(self, painter):
#         ...

#     def initialize(self):
#         ...

#     def render(self):
#         if not self.device:
#             self.device = QOpenGLPaintDevice()

#         glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
#         self.device.setSize(self.size() * self.devicePixelRatio())
#         self.device.setDevicePixelRatio(self.devicePixelRatio())

#         painter = QPainter(self.device)
#         self.renderPainter(painter)

#     def renderLayer(self):
#         self.requestUpdate()

#     def event(self, event):
#         match event.type():
#             case QEvent.UpdateRequest:
#                 self.renerNow()
#                 return True
#             case _:
#                 return QWindow.event(self, event)

#     def exposeEvent(self, event):
#         if self.isExposed():
#             self.renderNow()

#     def renderLater(self):
#         self.requestUpdate()

#     def renderNow(self):
#         if not self.isExposed():
#             return

#         needsInitialize = False

#         if not self.context:
#             self.context = QOpenGLContext(self)
#             self.context.setFormat(self.requestedFormat())
#             self.context.create()
#             needsInitialize = True

#         self.context.makeCurrent(self)

#         if needsInitialize:
#             self.initializeOpenGLFunctions()
#             self.initialize()

#         self.render()

#         self.context.swapBuffers(self)

#         if self.animating:
#             self.renderLater()

#     def setAnimating(self, animating:bool):
#         self.animating = animating
#         if animating:
#             self.renderLater()


# class TriangleCanvas(GLCanvasWindow):
#     def __init__(self, parent=None):
#         super().__init__(parent)

#         self.matrixUniform = 0
#         self.vbo:QOpenGLBuffer = None
#         self.program:QOpenGLShaderProgram = None
#         self.frame = 0

#         self.gllayer = GLLayer(parent=self)

#     def initialize(self):
#         self.gllayer.initializeGL()
#         # vertices = np.array([
#         #     +0.0, +0.707, 1.0, 0.0, 0.0,  # Vertex 1: Position (x, y), Color (r, g, b)
#         #     -0.5, -0.500, 0.0, 1.0, 0.0,  # Vertex 2: Position (x, y), Color (r, g, b)
#         #     +0.5, -0.500, 0.0, 0.0, 1.0   # Vertex 3: Position (x, y), Color (r, g, b)
#         # ], dtype=np.float32)

#         # self.vbo = QOpenGLBuffer()
#         # self.vbo.create()
#         # self.vbo.bind()
#         # self.vbo.allocate(vertices.tobytes(), vertices.size)

#         # # Number of components for position and color
#         # position_components = 2  # 2 components for the position (x, y)
#         # color_components = 3     # 3 components for the color (r, g, b)

#         # # Stride: the total size of a single vertex (5 GL_FLOATs)
#         # stride = vertices.itemsize * 5

#         # # Offset for position (starts at the beginning of the vertex data)
#         # position_offset = 0  # The position is at the beginning

#         # # Offset for color (after 2 floats for position)
#         # color_offset = position_components * vertices.itemsize  # 2 * size of a single float
#         # # Enable vertex attribute arrays
#         # glEnableVertexAttribArray(0)  # For position
#         # glEnableVertexAttribArray(1)  # For color

#         # # Vertex attribute pointer for position (2D)
#         # glVertexAttribPointer(0, position_components, GL_FLOAT, GL_FALSE, stride, None)

#         # # Vertex attribute pointer for color (3D)
#         # glVertexAttribPointer(1, color_components, GL_FLOAT, GL_FALSE, stride, color_offset)

#         # self.program = QOpenGLShaderProgram(self);
#         # self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, self.vertexShaderSource)
#         # self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, self.fragmentShaderSource)
#         # self.program.bindAttributeLocation("posAttr", 0)
#         # self.program.bindAttributeLocation("colAttr", 1)
#         # self.program.link()
#         # self.program.bind()

#         # self.matrixUniform = self.program.uniformLocation("matrix")

#         # assert self.matrixUniform != -1

#     def render(self):
#         retinaScale = self.devicePixelRatio();
#         glViewport(0, 0, int(self.width() * retinaScale), int(self.height() * retinaScale))
#         self.gllayer.resizeGL(int(self.width() * retinaScale), int(self.height() * retinaScale))
#         self.gllayer.paintGL()
#         # glClear(GL_COLOR_BUFFER_BIT);

#         # self.program.bind();

#         # matrix = QMatrix4x4()
#         # matrix.perspective(60.0, 4.0 / 3.0, 0.1, 100.0)
#         # matrix.translate(0, 0, -2)
#         # matrix.rotate(100.0 * self.frame / self.screen().refreshRate(), 0, 1, 0);

#         # self.program.setUniformValue(self.matrixUniform, matrix);

#         # glEnableVertexAttribArray(0);
#         # glEnableVertexAttribArray(1);

#         # glDrawArrays(GL_TRIANGLES, 0, 3);

#         # glDisableVertexAttribArray(0);
#         # glDisableVertexAttribArray(1);

#         # self.program.release()

#         # self.frame+=1


if __name__ == "__main__":
    format = QSurfaceFormat()
    format.setVersion(3, 3)  # OpenGL 3.3
    format.setProfile(QSurfaceFormat.CoreProfile)  # Use Core Profile
    format.setOption(QSurfaceFormat.DebugContext)  # Enable debugging for OpenGL (optional)
    format.setSwapInterval(1) # vsync on
    format.setSwapBehavior(QSurfaceFormat.DoubleBuffer)
    QSurfaceFormat.setDefaultFormat(format)  # Set this format as default
    app = QApplication([])
    # glwindow = GLWindow()
    # glwindow.show()

    # class MainWindow(QWidget):
    #     def __init__(self, parent=None):
    #         super().__init__(parent=parent)
    #         self.canvas = TriangleCanvas()
    #         canvas_container = self.createWindowContainer(self.canvas)
    #         canvas_container.setFixedSize(256,256)
    #         self.button = QPushButton("hello")
    #         layout = QVBoxLayout()
    #         self.setLayout(layout)
    #         layout.setContentsMargins(0,0,0,0)
    #         layout.addWidget(canvas_container)
    #         # layout.addWidget(self.button)
    #         # layout.addStretch()
    
    

    glwindow = GLWindow()
    glwindow.show()
    # window = MainWindow()
    # window.show()
    app.exec()