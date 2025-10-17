import logging
import time
from typing import *
import numpy as np
import glm # or import pyrr !!!! TODO: checkout pyrr
import moderngl
from textwrap import dedent
from pylive.glrenderer.utils.camera import Camera
from .render_layer import RenderLayer
from .arrow_layer import ArrowLayer
import math
logger = logging.getLogger(__name__)


class AxesLayer(RenderLayer):
    """ A render layer that draws 3 arrows representing the X, Y, and Z axes.
    """
    def __init__(self):
        super().__init__()

        self.xarrow = ArrowLayer( 
            model=glm.rotate(math.radians(90), glm.vec3(1,0,0)),
            color=glm.vec4(1,0,0,1)
        ) # X

        self.yarrow = ArrowLayer(
            model=glm.mat4(1),
            color=glm.vec4(0,1,0,1),
        ) # Y

        self.zarrow = ArrowLayer( 
            model=glm.rotate(math.radians(90), glm.vec3(0,0,1)),
            color=glm.vec4(0,0,1,1)
        ) # Z

    def setup(self, ctx: moderngl.Context):
        logger.info(f"Setting up {self.__class__.__name__}...")
        start_time = time.time()
        
        self.xarrow.setup(ctx)
        self.yarrow.setup(ctx)
        self.zarrow.setup(ctx)
        
        setup_time = time.time() - start_time
        logger.info(f"{self.__class__.__name__} setup completed in {setup_time:.3f}s")

    def render(self, view:glm.mat4, projection:glm.mat4):
        self.xarrow.render(view, projection)
        self.yarrow.render(view, projection)
        self.zarrow.render(view, projection)

    def destroy(self):
        self.xarrow.destroy()
        self.yarrow.destroy()
        self.zarrow.destroy()


