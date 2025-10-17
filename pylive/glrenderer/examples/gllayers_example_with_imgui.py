import logging


# Configure logging to see shader compilation logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import math


from pprint import pformat

from imgui_bundle import imgui, immapp


    
# ############## #
# Graphics Layer #
# ############## #
import moderngl
from pylive.glrenderer.gllayers import GridLayer, RenderLayer, AxesLayer
from pylive.glrenderer.utils.render_target import RenderTarget
from pylive.glrenderer.utils.camera import Camera

class SceneLayer(RenderLayer):
    def __init__(self):
        super().__init__()
        self.grid = GridLayer()
        self.axes = AxesLayer()
        self._initialized = False

    @property
    def initialized(self) -> bool:
        return self._initialized

    def setup(self):
        ctx = moderngl.get_context()
        if ctx is None:
            raise Exception("No current ModernGL context. Cannot setup SceneLayer.")
        self.grid.setup(ctx)
        self.axes.setup(ctx)
        super().setup(ctx)
        self._initialized = True

    def destroy(self):
        if self.grid:
            self.grid.destroy()
            self.grid = None
        if self.axes:
            self.axes.destroy()
            self.axes = None
        self._initialized = False
        return super().destroy()
    
    def render(self, camera:Camera):
        self.grid.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        self.axes.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        super().render()

# ModernGL context and framebuffer
scene_layer = SceneLayer()
render_target = RenderTarget(800, 800)

# ############## #
# GUI #
# ############## #



# ##### #
# TYPES #
# ##### #
import glm


# Camera
camera = Camera()
camera.setPosition(glm.vec3(5.0, 5.0, 5.0))
camera.lookAt(glm.vec3(0.0, 0.0, 0.0))

def gui():
    # Configure imgui
    style = imgui.get_style()
    style.anti_aliased_lines = True
    style.anti_aliased_lines_use_tex = True
    style.anti_aliased_fill = True

    # ModernGL renderer
    global render_target
    if not render_target.initialized:
        render_target.setup()

    if not scene_layer.initialized:
        scene_layer.setup()

    imgui.text("RenderLayers example with imgui")    
    
    widget_size = imgui.get_content_region_avail()
    
    if imgui.begin_child("3d_viewport", widget_size):
        image_width, image_height = int(widget_size.x), int(widget_size.y)
        camera.setAspectRatio(image_width / image_height)

        avail = imgui.get_content_region_avail()
        imgui.set_cursor_pos_x(imgui.get_cursor_pos_x() + avail.x - 100)  # 100 is the button width
        imgui.button("Orbit", (100,100))
        if imgui.is_item_hovered():
            imgui.set_mouse_cursor(imgui.MouseCursor_.hand)

        if imgui.is_item_active():
            delta = imgui.get_mouse_drag_delta(lock_threshold=0.0)
            camera.orbit(-delta.x * 0.5, -delta.y * 0.5)
            imgui.reset_mouse_drag_delta()
        

        # Render Scene
        gl_size = widget_size * imgui.get_io().display_framebuffer_scale
        render_target.resize(int(gl_size.x), int(gl_size.y))
        with render_target:
            render_target.clear(0.1, 0.1, 0.1, 0.0)  # Clear with dark gray background
            scene_layer.render(camera)

        # Display the framebuffer texture in ImGui
        imgui.set_cursor_pos(imgui.ImVec2(0,0))
        image_ref = imgui.ImTextureRef(int(render_target.color_texture.glo))
        imgui.image(
            image_ref,
            imgui.ImVec2(widget_size.x, widget_size.y),
            imgui.ImVec2(0, 1), # flip vertically
            imgui.ImVec2(1, 0) 
        )

        # Draw 3D grid
        view = camera.viewMatrix()
        projection = glm.perspective(math.radians(camera.fovy), camera.aspect_ratio, 0.1, 100.0)
        viewport = (0, 0, int(widget_size.x), int(widget_size.y))


        
    imgui.end_child()



if __name__ == "__main__":
    immapp.run(gui, window_title="RenderLayers example with imgui", window_size=(800, 800))

