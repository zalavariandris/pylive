import logging
import time
from typing import *
import numpy as np
import glm # or import pyrr !!!! TODO: checkout pyrr
import trimesh
import moderngl
from textwrap import dedent
from pylive.glrenderer.utils.camera import Camera
from .render_layer import RenderLayer

logger = logging.getLogger(__name__)

class TriangleLayer(RenderLayer):
    """ A simple render layer that draws a triangle.
    """

    def __init__(self, camera:Camera|None=None) -> None:
        super().__init__()
        self.camera = camera or Camera()
        self.program = None

    @override
    def setup(self, ctx:moderngl.Context):
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

        # triangle
        vertices = np.array([
             0.0, 0.0,  0.4,   # Vertex 1
            -0.4, 0.0, -0.3,   # Vertex 2
             0.4, 0.0, -0.3    # Vertex 3
        ], dtype=np.float32)

        self.vbo = ctx.buffer(vertices.tobytes())

        self.vao = ctx.vertex_array(
            self.program,
            [
                (self.vbo, '3f', 'position'),
            ],
            mode=moderngl.TRIANGLES
        )
        
        setup_time = time.time() - start_time
        logger.info(f"{self.__class__.__name__} setup completed in {setup_time:.3f}s")

    @override
    def destroy(self):
        if self.program:
            self.program.release()
            self.program = None
        if self.vbo:
            self.vbo.release()
            self.vbo = None
        if self.vao:
            self.vao.release()
            self.vao = None

    @override
    def render(self, **kwargs):
        self.program['view'].write(self.camera.viewMatrix())
        self.program['projection'].write(self.camera.projectionMatrix())
        self.program['color'].write(glm.vec4(1.0, 1.0, 0.3, 1.0))
        self.vao.render()