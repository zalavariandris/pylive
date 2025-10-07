from textwrap import dedent
import moderngl
from OpenGL.GL import *
import glm
import numpy as np

def draw_triangle_with_moderngl(ctx, size=1.0):
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
	vertices*=size
	vbo = ctx.buffer(vertices.tobytes())

	vao = ctx.vertex_array(
		program,
		[
			(vbo, '3f', 'position'),
		],	
		mode=moderngl.TRIANGLES
	)

	glPolygonMode( GL_FRONT_AND_BACK, GL_LINE  )
	vao.render()

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from OpenGL.GL import *  # PyOpenGL bindings
from PySide6.QtOpenGL import *
def draw_triangle_with_opengl(parent, size=1.0):
    ### init ###

    # Initialize shader program
    program = QOpenGLShaderProgram(parent)

    # Vertex shader
    program.addShaderFromSourceCode(QOpenGLShader.Vertex, """
    #version 330 core
    layout(location = 0) in vec3 aPos;
    void main() {
        gl_Position = vec4(aPos, 1.0);
    }
    """)

    # Fragment shader
    program.addShaderFromSourceCode(QOpenGLShader.Fragment, """
    #version 330 core
    out vec4 FragColor;
    void main() {
        FragColor = vec4(1.0, 0.5, 0.2, 1.0); // Orange
    }
    """)

    # Link the shader program
    program.link()

    # Define vertices for a triangle
    vertices = np.array([
        -0.5, -0.5, 0.0,  # Bottom-left
         0.5, -0.5, 0.0,  # Bottom-right
         0.0,  0.5, 0.0   # Top
    ], dtype=np.float32)

    # Create and bind the VAO
    VAO = QOpenGLVertexArrayObject(parent)
    VAO.create()
    VAO.bind()

    # Create and fill the VBO with vertex data
    VBO = QOpenGLBuffer(QOpenGLBuffer.VertexBuffer)
    VBO.create()
    VBO.bind()
    VBO.allocate(vertices.tobytes(), vertices.nbytes)

    # Set the vertex attribute pointer
    program.enableAttributeArray(0)
    program.setAttributeBuffer(0, GL_FLOAT, 0, 3)

    # Unbind buffers and VAO
    VBO.release()
    VAO.release()

    ### draw ###
    # Use the shader program and bind VAO
    program.bind()
    VAO.bind()

    # Draw the triangle
    glDrawArrays(GL_TRIANGLES, 0, 3)

    # Unbind VAO and shader program
    VAO.release()
    program.release()

def set_default_opengl_format(version=(3,3)):
    """call thi before initializing the QApplication
    set the version as desired
    """
    format = QSurfaceFormat()
    format.setVersion(*version)  # OpenGL 3.3
    format.setDepthBufferSize(24)
    format.setStencilBufferSize(8)
    format.setSwapInterval(1)
    format.setMajorVersion(4)
    format.setMinorVersion(6)
    format.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)  # Use Core Profile
    format.setOption(QSurfaceFormat.FormatOption.DebugContext)  # Enable debugging for OpenGL (optional)
    QSurfaceFormat.setDefaultFormat(format)  # Set this format as default