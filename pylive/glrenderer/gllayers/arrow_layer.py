import logging
import time
from typing import *
import numpy as np
import glm # or import pyrr !!!! TODO: checkout pyrr
import moderngl
from textwrap import dedent
from pylive.glrenderer.utils.camera import Camera
from .render_layer import RenderLayer

logger = logging.getLogger(__name__)

class ArrowLayer(RenderLayer):
    """ A render layer that draws an arrow with a flat head, useful for visualizing axes.

    NOTE: BILLBOARD constant and helper functions (decompose, lookAt) are reserved 
    for future billboard/sprite implementation.
    """
    BILLBOARD = dedent('''\
        // Decompose the view matrix to remove its rotational part
        mat4 billboard(mat4 view, vec4 position){
            // Extract translation and scale (ignore rotation) from the view matrix
            mat4 billboardMatrix = mat4(1.0); // Identity matrix for billboard effect
            billboardMatrix[3] = view[3];     // Keep camera's translation
            
            // Compute final position in world space
            return billboardMatrix * vec4(position, 1.0);
        }
    ''')
    FLAT_VERTEX_SHADER = dedent('''\
        #version 330 core

        uniform mat4 view;         // View matrix
        uniform mat4 projection;   // Projection matrix
        uniform mat4 model;        // Model matrix

        layout(location = 0) in vec3 position; // Local vertex position (e.g., quad corners)

        // Function to decompose a matrix into position, rotation, and scale
        void decompose(mat4 M, out vec3 position, out mat3 rotation, out vec3 scale) {
            // Extract translation
            position = vec3(M[3][0], M[3][1], M[3][2]);

            // Extract the upper-left 3x3 matrix for rotation and scale
            mat3 upper3x3 = mat3(M);

            // Extract scale
            scale.x = length(upper3x3[0]); // Length of the X-axis
            scale.y = length(upper3x3[1]); // Length of the Y-axis
            scale.z = length(upper3x3[2]); // Length of the Z-axis

            // Normalize the columns of the 3x3 matrix to remove scaling, leaving only rotation
            rotation = mat3(
                upper3x3[0] / scale.x,
                upper3x3[1] / scale.y,
                upper3x3[2] / scale.z
            );
        }

        // Function to create a lookAt matrix
        mat4 lookAt(vec3 eye, vec3 center, vec3 up) {
            vec3 forward = normalize(center - eye);
            vec3 right = normalize(cross(forward, up));
            vec3 cameraUp = cross(right, forward);

            // Create a rotation matrix
            mat4 rotation = mat4(
                vec4(right, 0.0),
                vec4(cameraUp, 0.0),
                vec4(-forward, 0.0),
                vec4(0.0, 0.0, 0.0, 1.0)
            );

            // Create a translation matrix
            mat4 translation = mat4(
                vec4(1.0, 0.0, 0.0, 0.0),
                vec4(0.0, 1.0, 0.0, 0.0),
                vec4(0.0, 0.0, 1.0, 0.0),
                vec4(-eye, 1.0)
            );

            // Combine rotation and translation
            return rotation * translation;
        }

        void main() {
            // Decompose the inverse of the view matrix to get camera properties
            vec3 eye;
            mat3 rotation;
            vec3 scale;
            decompose(inverse(view), eye, rotation, scale);

            // Create a lookAt matrix (view matrix from camera properties)
            mat4 lookAtMatrix = lookAt(vec3(0.0, 0.0, 0.0), eye, vec3(0.0, 1.0, 0.0));

            // Apply transformations: projection * view * model
            gl_Position = projection * view * model * vec4(position, 1.0);
        }
    ''')
    def __init__(self, model=glm.mat4(1.0), color=glm.vec4(1.0, 1.0, 1.0, 1.0)):
        super().__init__()
        self.program = None
        self.vao = None
        self.model = model
        self.color = color
        
    def setup(self, ctx):
        logger.info(f"Setting up {self.__class__.__name__}...")
        start_time = time.time()
        
        logger.info(f"{self.__class__.__name__}: Compiling shaders...")
        shader_start = time.time()
        self.program = ctx.program(
            vertex_shader=self.FLAT_VERTEX_SHADER,
            fragment_shader=self.FLAT_FRAGMENT_SHADER
        )
        shader_time = time.time() - shader_start
        logger.info(f"{self.__class__.__name__}: Shader compilation took {shader_time:.3f}s")
        
        vertices = np.array([
            (0.0, 0.0, 0.0),  # Bottom of the shaft
            (0.0, 1.0, 0.0),  # Top of the shaft

            (0.0, 1.0, 0.0),  # Top of the shaft
            (-0.1, 0.9, 0.0),  # Left of the arrowhead
            
            (0.0, 1.0, 0.0),  # Top of the shaft
            (0.1, 0.9, 0.0)   # Right of the arrowhead
        ], dtype=np.float32).flatten()
    

        self.vbo = ctx.buffer(vertices)

        self.vao = ctx.vertex_array(
            self.program,
            [
                (self.vbo, '3f', 'position'),
            ],
            mode=moderngl.LINES
        )
        
        setup_time = time.time() - start_time
        logger.info(f"{self.__class__.__name__} setup completed in {setup_time:.3f}s")
        
    def render(self, view:glm.mat4=None, projection:glm.mat4=None):
        self.program['view'].write(view)
        self.program['projection'].write(projection)
        self.program['model'].write(self.model)
        self.program['color'].write(self.color)
        self.vao.render()

    def destroy(self):
        if self.program:
            self.program.release()
            self.program = None
        if self.vao:
            self.vao.release()
            self.vao = None
        if self.vbo:
            self.vbo.release()
            self.vbo = None