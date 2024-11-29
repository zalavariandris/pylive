import sys
import numpy as np
import moderngl
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtOpenGLWidgets import QOpenGLWidget
import OpenGL.GL as gl
import numpy as np
import moderngl
import OpenGL.GL as gl
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtOpenGLWidgets import QOpenGLWidget

class ModernGLWidget(QOpenGLWidget):
    def initializeGL(self):
        # Ensure OpenGL context is current
        self.makeCurrent()

        # Get current OpenGL context
        gl.glGetError()  # Clear any existing errors

        # Create ModernGL context using current GL context
        version = self.context().format().version()
        print("OpenGL", version)
        self.mgl = moderngl.create_context(require=330)
        print(self.mgl.info)

        # Define triangle vertices
        vertices = np.array([
            -0.6, -0.6, 1.0, 0.0, 0.0,  # Bottom-left (red)
             0.6, -0.6, 0.0, 1.0, 0.0,  # Bottom-right (green)
             0.0,  0.6, 0.0, 0.0, 1.0,  # Top-center (blue)
        ], dtype='f4')
        
        # Shaders
        vertex_shader = """
        #version 330 core
        in vec2 in_position;
        in vec3 in_color;
        out vec3 color;
        void main() {
            gl_Position = vec4(in_position, 0.0, 1.0);
            color = in_color;
        }
        """
        fragment_shader = """
        #version 330 core
        in vec3 color;
        out vec4 fragColor;
        void main() {
            fragColor = vec4(color, 1.0);
        }
        """
        
        # Create program and buffers
        self.program = self.mgl.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )
        
        self.vbo = self.mgl.buffer(vertices.tobytes())
        self.vao = self.mgl.vertex_array(
            self.program, 
            [(self.vbo, '2f 3f', 'in_position', 'in_color')]
        )

    def paintGL(self):
        self.doneCurrent()
        self.mgl.clear(0.5, 0.0, 0.5, 1.0)
        # self.vao.render(moderngl.TRIANGLES)



if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Detailed OpenGL format configuration
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.CoreProfile)
    QSurfaceFormat.setDefaultFormat(fmt)
    
    window = ModernGLWidget()
    window.show()
    sys.exit(app.exec())