
import trimesh
import moderngl

from pylive.glrenderer.windows.mgl_render_window import MGLCameraWindow
from pylive.glrenderer.regl_old.regl import REGL
import glm
import numpy as np

regl = REGL()
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

class REGLExampleWindow(MGLCameraWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # create draw triangle command
        
    def on_render(self, time: float, frametime: float):
        self.ctx.clear(0.1, 0.1, 0.1, 1.0)
        draw_triangle()

if __name__ == "__main__":
    # Run the window
    REGLExampleWindow.run()