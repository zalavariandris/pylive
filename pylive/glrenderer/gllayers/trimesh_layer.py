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

class TrimeshLayer(RenderLayer):
    """ A render layer that draws any trimesh.Trimesh mesh.
    """
    def __init__(self, mesh:trimesh.Trimesh|None=None) -> None:
        super().__init__()
        self.program = None
        self.mesh = mesh

    @override
    def setup(self):
        ctx = moderngl.get_context()
        if ctx is None:
            raise Exception("No current ModernGL context. Cannot setup ArrowLayer.")
        logger.info(f"Setting up {self.__class__.__name__}...")
        start_time = time.time()
        
        # Setup shaders
        logger.info(f"{self.__class__.__name__}: Compiling shaders...")
        shader_start = time.time()
        self.program = ctx.program(
            vertex_shader=self.FLAT_VERTEX_SHADER,
            fragment_shader=self.FLAT_FRAGMENT_SHADER
        )
        shader_time = time.time() - shader_start
        logger.info(f"{self.__class__.__name__}: Shader compilation took {shader_time:.3f}s")

        # to VAO
        vertices = self.mesh.vertices.flatten().astype(np.float32)
        indices = self.mesh.faces.flatten().astype(np.uint32)
        self.vbo = ctx.buffer(vertices)
        self.ibo = ctx.buffer(indices)

        self.vao = ctx.vertex_array(
            self.program,
            [
                (self.vbo, '3f', 'position'),
            ],
            mode=moderngl.TRIANGLES,
            index_buffer=self.ibo
        )
        
        setup_time = time.time() - start_time
        logger.info(f"{self.__class__.__name__} setup completed in {setup_time:.3f}s")

    @override
    def render(self, *, view:glm.mat4=None, projection:glm.mat4=None, color:glm.vec4=None):
        assert self.program is not None
        if view is None:
            view = glm.mat4(1.0)
        if projection is None:
            projection = glm.mat4(1.0)
        if color is None:
            color = glm.vec4(0.5, 0.5, 0.5, 1.0)

        self.program['view'].write(view)
        self.program['projection'].write(projection)
        self.program['color'].write(color)
        
        self.vao.render()

    def release(self):
        if self.program:
            self.program.release()
            self.program = None
        if self.vao:
            self.vao.release()
            self.vao = None
        if self.vbo:
            self.vbo.release()
            self.vbo = None
        if self.ibo:
            self.ibo.release()
            self.ibo = None
