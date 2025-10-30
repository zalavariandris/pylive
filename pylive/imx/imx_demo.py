

import math
from typing import Any, List, Tuple, Dict
import glm
from imgui_bundle import imgui, immapp, imgui_ctx
from imgui_bundle.immapp import icons_fontawesome_6 as fa

# Local application imports
from pylive import imx

# Configure logging to see shader compilation logs
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import colors

line_handle = imx.comp(imx.viewport.point_handle)
lines_handle = imx.comp(line_handle)

from pylive.glrenderer.utils.camera import Camera

@immapp.static(
    my_point=imgui.ImVec2(50,50),
    first_vanishing_lines = [
        (imgui.ImVec2(62,40), imgui.ImVec2(16,64)),
        (imgui.ImVec2(77,42), imgui.ImVec2(57,84))

    ],
    second_vanishing_lines = [
        (imgui.ImVec2(38,42), imgui.ImVec2(83,61)),
        (imgui.ImVec2(30,45), imgui.ImVec2(72,82)),
    ],
    fovy_degrees = 45.0,
    camera=Camera().setPosition(glm.vec3(1,2,-5)).lookAt(glm.vec3(0,0,0))
)
def gui():
    imgui.begin("MyPlotWindow", None)
    _, gui.fovy_degrees = imgui.slider_float("Vertical Field of View", gui.fovy_degrees, 0, 180, "%.1f°")
    if imx.viewport.begin_viewport("my_plot", None):
        
        # 1. Draw 2D GUI Overlay
        sensor_size = glm.vec2(160, 90)  # in mm
        imx.viewport.setup_orthographic(0,0,sensor_size.x,sensor_size.y)

        _, gui.first_vanishing_lines = lines_handle("z", gui.first_vanishing_lines, color=colors.BLUE )
        for line in gui.first_vanishing_lines:
            imx.viewport.draw_line(line[0], line[1], color=colors.BLUE)

        _, gui.second_vanishing_lines = lines_handle("x", gui.second_vanishing_lines, color=colors.RED )
        for line in gui.second_vanishing_lines:
            imx.viewport.draw_line(line[0], line[1], color=colors.RED)

        # 2. Draw 3D Scene
        # setup view projection
        
        w, h = imgui.get_window_size()
        widget_aspect = w / h
        sensor_aspect = sensor_size.x / sensor_size.y
        

        fovy = math.radians(gui.fovy_degrees)
        # Compute the fovy needed to fit the sensor width in the widget
        required_fovy = 2 * glm.atan(glm.tan(fovy / 2) * (sensor_aspect / widget_aspect))
        # Use the larger fovy to ensure full fit (overscan if needed)
        overscan_fovy = max(fovy, required_fovy)
        
        # projection = glm.perspective(overscan_fovy, widget_aspect, 0.1, 100.0)
        # view = glm.lookAt(glm.vec3(5,5,5), glm.vec3(0,0,0), glm.vec3(0,1,0))
        # imx.viewer.setup_view_projection(view, projection)

        gui.camera.setAspectRatio(widget_aspect)
        gui.camera.setFoVY(math.degrees(overscan_fovy))
        gui.camera.lookAt(glm.vec3(0,0,0))
        imx.viewport.setup_view_projection(glm.scale(glm.vec3(-1,-1,1)) * gui.camera.viewMatrix(), gui.camera.projectionMatrix())


        # draw grid
        imx.viewport.draw_grid()
        # draw axes
        imx.viewport.draw_line((0,0,0), (1,0,0), colors.RED)
        imx.viewport.draw_line((0,0,0), (0,1,0), colors.GREEN)
        imx.viewport.draw_line((0,0,0), (0,0,1), colors.BLUE)

        # imx.viewer.draw_lines([(tl, br)], color=colors.YELLOW)

        # screen_pos = imx.viewer.project((0, 0, 0))
        # imx.viewer.draw_grid3D(size=10, step=1, color=colors.DARK_GRAY)
        # imx.viewer.draw_axes(...)
        # imx.viewer.draw_sphere(...)
        # imx.viewer.draw_trimesh(...)

        # draw margins
        imx.viewport.setup_orthographic(0,0,sensor_size.x,sensor_size.y)
        imx.viewport.draw_margins(imgui.ImVec2(0,0), imgui.ImVec2(sensor_size.x,sensor_size.y))

        # dl.idx_buffer.extend(my_cached_draw_list.idx_buffer)

        # Toolbar: Floating Bar
        style = imgui.get_style()
        imgui.set_cursor_pos(imgui.ImVec2(imgui.get_window_size().x - 36-style.window_padding.x , 0+style.window_padding.y))
        _, touch_delta = imx.touch_pad(f"{fa.ICON_FA_ROTATE}", imgui.ImVec2(36,36))
        if _:
            gui.camera.orbit(touch_delta.x * 0.5, -touch_delta.y * 0.5)

    imx.viewport.end_viewport()
    imgui.set_cursor_pos(imgui.ImVec2(0,0))


    imgui.end()
    

if __name__ == "__main__":
    immapp.run(gui, window_title="imx(my imgui extensions)", window_size=(1200, 1200), with_implot3d=True)
