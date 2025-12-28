from reloading import reloading
from imgui_bundle import imgui, immapp, hello_imgui
import moderngl as mgl
import numpy as np
import time
import math

# Cache for GPU resources
ctx = None
tex = None
program = None
vao = None
fbo = None

def post_init():
    """Called after GLFW window is created and OpenGL context is available"""
    global ctx, tex, program, vao, fbo
    
    ctx = mgl.get_context()
    ctx.gc_mode = 'auto'
    
    # Create all resources once
    tex = ctx.texture((400, 400), 4)
    
    program = ctx.program(
        vertex_shader="""
        #version 330
        in vec2 in_position;
        void main() {
            gl_Position = vec4(in_position, 0.0, 1.0);
        }
        """,
        fragment_shader="""
        #version 330
        uniform float hue;
        out vec4 f_color;
        
        vec3 hsv2rgb(vec3 c) {
            vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
            vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
            return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
        }
        
        void main() {
            vec3 hsv = vec3(hue * 0.1, 1.0, 1.0);
            vec3 rgb = hsv2rgb(hsv);
            f_color = vec4(rgb, 1.0);
        }
        """,
    )
    
    # Create vertices as numpy array of float32
    vertices = np.array([
        -1.0, -1.0,
        1.0, -1.0,
        -1.0,  1.0,
        -1.0,  1.0,
        1.0, -1.0,
        1.0,  1.0,
    ], dtype='f4')
    
    vbo = ctx.buffer(vertices.tobytes())
    vao = ctx.simple_vertex_array(program, vbo, "in_position")
    fbo = ctx.framebuffer(color_attachments=[tex])

@reloading
def gui():
    try:
        global ctx, tex, program, vao, fbo

        imgui.text("objects:")
        for obj in ctx.objects:
            imgui.text(f" - {obj}")
        
        imgui.text(f"Framerate: {imgui.get_io().framerate:.2f} FPS")
        
        # Set time uniform
        t = time.time()
        k = 0.5 + 0.5 * math.sin(t*2.0)
        imgui.text(f"k: {k:.2f} seconds")
        program['hue'] = k * math.pi*2.0
        
        # Render to texture
        fbo.use()
        fbo.viewport = (0, 0, 400, 400)
        fbo.clear(0.2, 0.4, 0.6, 1.0)
        vao.render()
        ctx.screen.use()

        # Display the texture
        imgui.text("Hello, World!")
        imgui.image(imgui.ImTextureRef(tex.glo), (400, 400))

        

    except SyntaxError as se:
        imgui.text(f"Syntax Error: {se}")
    except Exception as e:
        imgui.text(f"Error: {e}")
    
    

if __name__ == "__main__":
    params = hello_imgui.RunnerParams()
    params.callbacks.post_init = post_init
    params.callbacks.show_gui = gui
    immapp.run(params)
