"""
TODO:
- update the modderngl window example with a camera control, by using the new __call__ overrides
- create an imgui example, where the ResourceManager resources, cache, buffers etc are visualized in realtime.
- use Regl.__call__ to execute commands?
- VAO caching: per-command dictionary keyed by (program, buffer ids, attribute names)
- clear cached weak refs each frame?
- implement the frame method for animation?
- consider using VAO and Program resource objects
"""

from typing import *

from numpy import dtype
import moderngl
from .command import Command
from .resource_manager import ResourceManager

from OpenGL.GL import *


import glm

class REGL(ResourceManager):
    def command(self, *, vert:str, frag:str, uniforms:Dict, attributes:Dict, count:int, framebuffer:moderngl.Framebuffer=None):
        return Command(
            vert=vert,
            frag=frag,
            uniforms=uniforms,
            attributes=attributes,
            count=count,
            framebuffer=framebuffer
        )

    def clear(self, color:glm.vec4=glm.vec4(0,0,0,1)):
        ctx = moderngl.get_context()
        ctx.clear(1,.3,1,1)

    def frame(self, callback:Callable):
        """ for animation? """
        ...


if __name__ == "__main__":
    from textwrap import dedent
    import numpy as np
    
    regl = REGL()
    # create draw triangle command
    draw_triangle = regl.command(
        vert='''\
            #version 410 core

            uniform mat4 view;
            uniform mat4 projection;

            layout(location = 0) in vec3 position;

            void main() {
                gl_Position = projection * view * vec4(position, 1.0);
            }
        ''',
        frag='''
            #version 410 core

            layout (location = 0) out vec4 out_color;
            uniform vec4 color;
            
            void main() {
                out_color = color;
            }
        ''',

        uniforms={
            'projection': glm.ortho(-1,1,-1,1,0,1),
            'view': glm.mat4(1),
            'color': glm.vec4(0.0, 1.0, 0.3, 1.0)
        },

        attributes={
            'position': np.array([
                [-1,  0, 0],
                [ 0, -1, 0],
                [+1, +1, 0]
            ], dtype=np.float32)
        },

        count=3
    )

if __name__ == "__main__":
    from pylive.glrenderer.windows.mgl_render_window import MGLCameraWindow
    class REGL_Lazy_ExampleWindow(MGLCameraWindow):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
        
        def on_render(self, time: float, frametime: float):
            self.ctx.clear(0.1, 0.1, 0.1, 1.0)
            draw_triangle()
    REGL_Lazy_ExampleWindow.run()