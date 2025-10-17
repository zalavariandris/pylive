from typing import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from OpenGL.GL import *  # PyOpenGL bindings
from PySide6.QtOpenGL import *
import numpy as np

class Canvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_PaintOnScreen)
        self.setAttribute(Qt.WA_NoSystemBackground)

        # Create the OpenGL context
        self.context = QOpenGLContext(self)
        format = QSurfaceFormat()
        format.setVersion(3, 3)  # OpenGL 3.3
        format.setProfile(QSurfaceFormat.CoreProfile)
        self.context.setFormat(format)
        self.context.create()

        # Create a surface (QWindow acts as a rendering target)
        self.surface = QWindow()
        self.surface.setSurfaceType(QWindow.OpenGLSurface)
        self.surface.setFormat(format)
        self.surface.create()

        self.context.makeCurrent(self.surface)
        self.functions = self.context.functions()

        # Initialize OpenGL resources
        self.initializeGL()

        # Timer for continuous updates
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(16)  # ~60 FPS

    def sizeHint(self) -> QSize:
        return QSize(800,600)

    def initializeGL(self):
        """Initialize OpenGL context, shaders, and buffers."""
        # Initialize shader program
        self.program = QOpenGLShaderProgram(self)

        # Vertex shader
        self.program.addShaderFromSourceCode(QOpenGLShader.Vertex, """
        #version 330 core
        layout(location = 0) in vec3 aPos;
        void main() {
            gl_Position = vec4(aPos, 1.0);
        }
        """)

        # Fragment shader
        self.program.addShaderFromSourceCode(QOpenGLShader.Fragment, """
        #version 330 core
        out vec4 FragColor;
        void main() {
            FragColor = vec4(1.0, 0.5, 0.2, 1.0); // Orange
        }
        """)

        # Link the shader program
        self.program.link()

        # Define vertices for a triangle
        vertices = np.array([
            -0.5, -0.5, 0.0,  # Bottom-left
             0.5, -0.5, 0.0,  # Bottom-right
             0.0,  0.5, 0.0   # Top
        ], dtype=np.float32)

        # Create Vertex Buffer Object (VBO) and Vertex Array Object (VAO)
        self.VAO = glGenVertexArrays(1)
        self.VBO = glGenBuffers(1)

        glBindVertexArray(self.VAO)

        # Bind VBO and load vertex data
        glBindBuffer(GL_ARRAY_BUFFER, self.VBO)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

        # Define vertex attributes
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * vertices.itemsize, None)
        glEnableVertexAttribArray(0)

        # Unbind buffers
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        # Set the clear color
        glClearColor(0.2, 0.3, 0.3, 1.0)

    def paintEvent(self, event):
        """Render the OpenGL scene."""
        self.context.makeCurrent(self.surface)

        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Use the shader program and bind VAO
        self.program.bind()
        glBindVertexArray(self.VAO)

        # Draw the triangle
        glDrawArrays(GL_TRIANGLES, 0, 3)

        # Unbind VAO and shader program
        glBindVertexArray(0)
        self.program.release()

        # Swap buffers
        self.context.swapBuffers(self.surface)
        print("paintEvent")

    def resizeEvent(self, event):
        """Handle widget resizing."""
        self.context.makeCurrent(self.surface)
        self.functions.glViewport(0, 0, self.width(), self.height())
        print(f"Viewport resized to {self.width()}x{self.height()}.")

    def paintEngine(self):
        """Disable the paint engine to allow OpenGL rendering."""
        return None





if __name__ == "__main__":
    format = QSurfaceFormat()
    format.setVersion(3, 3)  # OpenGL 3.3
    format.setProfile(QSurfaceFormat.CoreProfile)  # Use Core Profile
    format.setOption(QSurfaceFormat.DebugContext)  # Enable debugging for OpenGL (optional)
    QSurfaceFormat.setDefaultFormat(format)  # Set this format as default
    
    app = QApplication([])
    canvas = Canvas()
    canvas.show()
    app.exec()
