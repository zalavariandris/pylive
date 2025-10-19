import logging


# Configure logging to see shader compilation logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


from imgui_bundle import imgui, immapp

from pylive.glrenderer.regl_lazy.regl import REGL
import glm
import numpy as np
# ############## #
# GUI #
# ############## #

regl = REGL()
color = regl.texture(
    size=(800,800), 
    components=4
)

# fbo = regl.framebuffer(color_attachments=[color])
draw_triangle = regl.command(
    framebuffer=None,
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



def gui():
    imgui.begin_child("3d_viewport")
    from pprint import pformat
    imgui.text(pformat(regl.stats()))
    imgui.text("This is where the 3D viewport would be rendered.")
    imgui.end_child()
    draw_triangle()



if __name__ == "__main__":
    immapp.run(gui, window_title="RenderLayers example with imgui", window_size=(800, 800))

