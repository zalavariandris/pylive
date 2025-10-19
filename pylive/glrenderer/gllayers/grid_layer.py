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

class GridLayer(RenderLayer):
    """ A render layer that draws a grid on the XZ plane."""
    def __init__(self, XY=False, XZ=True, YZ=False, color=glm.vec4(0.5, 0.5, 0.5, 1.0)):
        super().__init__()
        self.program = None
        self.vao = None
        self.color = color

        self.XY = XY
        self.XZ = XZ
        self.YZ = YZ

        self._initialized = False
        
    def setup(self):
        ctx = moderngl.get_context()
        if ctx is None:
            raise Exception("No current ModernGL context. Cannot setup ArrowLayer.")
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
        
        all_vertices = []
        
        # XZ grid (horizontal plane, Y=0)
        if self.XZ:
            for x in range(0, 11, 1):
                all_vertices.extend([(x-5, 0, -5), (x-5, 0, +5)])
            for z in range(0, 11, 1):
                all_vertices.extend([(-5, 0, z-5), (+5, 0, z-5)])
        
        # XY grid (vertical plane, Z=0)
        if self.XY:
            for x in range(0, 11, 1):
                all_vertices.extend([(x-5, -5, 0), (x-5, +5, 0)])
            for y in range(0, 11, 1):
                all_vertices.extend([(-5, y-5, 0), (+5, y-5, 0)])
        
        # YZ grid (vertical plane, X=0)
        if self.YZ:
            for y in range(0, 11, 1):
                all_vertices.extend([(0, y-5, -5), (0, y-5, +5)])
            for z in range(0, 11, 1):
                all_vertices.extend([(0, -5, z-5), (0, +5, z-5)])

        # Convert to numpy array and create buffer
        vertices = np.array(all_vertices, dtype=np.float32).flatten()
        self.vbo = ctx.buffer(vertices)

        self.vao = ctx.vertex_array(
            self.program,
            [
                (self.vbo, '3f', 'position'),
            ],
            mode=moderngl.LINES
        )
        self._initialized = True
        
        setup_time = time.time() - start_time
        logger.info(f"{self.__class__.__name__} setup completed in {setup_time:.3f}s")
        
    def render(self, view:glm.mat4, projection:glm.mat4):
        if not self._initialized:
            logging.warning("GridLayer not initialized. Call setup(ctx) before render().")
            return
        self.program['view'].write(view)
        self.program['projection'].write(projection)
        self.program['color'].write(self.color)
        self.vao.render()

    def release(self):
        if self.program:
            self.program.release()
        if self.vao:
            self.vao.release()
        if self.vbo:
            self.vbo.release()

