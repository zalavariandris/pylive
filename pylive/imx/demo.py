

from typing import Any, List, Tuple, Dict
from imgui_bundle import imgui, immapp, imgui_ctx

# Local application imports
from pylive import imx

# Configure logging to see shader compilation logs
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

import colors

line_handle = imx.comp(imx.viewer.point_handle)
lines_handle = imx.comp(line_handle)

@immapp.static(
    my_point=imgui.ImVec2(50,50),
    first_vanishing_lines = [
        (imgui.ImVec2(62,40), imgui.ImVec2(16,64)),
        (imgui.ImVec2(77,42), imgui.ImVec2(57,84))

    ],
    second_vanishing_lines = [
        (imgui.ImVec2(38,42), imgui.ImVec2(83,61)),
        (imgui.ImVec2(30,45), imgui.ImVec2(72,82)),
    ]
)
def gui():
    imgui.begin("MyPlotWindow", None)
    _, gui.my_point.x = imgui.slider_float("x", gui.my_point.x, 0, 100)
    _, gui.my_point.y = imgui.slider_float("y", gui.my_point.y, 0, 100)
    if imx.viewer.begin_viewport("my_plot", None):
        # draw 2d points
        imx.viewer.setup_orthographic(0,0,100,100)
        # single draggable 2D point handle
        _, gui.first_vanishing_lines = lines_handle("z", gui.first_vanishing_lines, color=colors.BLUE )
        imx.viewer.draw_lines(gui.first_vanishing_lines, color=colors.BLUE)

        _, gui.second_vanishing_lines = lines_handle("x", gui.second_vanishing_lines, color=colors.RED )
        imx.viewer.draw_lines(gui.second_vanishing_lines, color=colors.RED)

        # draw 3d scene
        imx.viewer.setup_perspective(fov_y_deg=60, aspect=1.0, near=0.1, far=100.0, fit_viewport=True)
        # imx.viewer.draw_grid3D(size=10, step=1, color=colors.DARK_GRAY)
        # imx.viewer.draw_axes(...)
        # imx.viewer.draw_sphere(...)
        # imx.viewer.draw_trimesh(...)

        # draw margins
        imx.viewer.setup_orthographic(0,0,100,100)
        imx.viewer.draw_margins(imgui.ImVec2(0,0), imgui.ImVec2(100,100))
        
    imx.viewer.end_viewport()
    
    imgui.end()
    

if __name__ == "__main__":
    immapp.run(gui, window_title="imx(my imgui extensions)", window_size=(1200, 1200), with_implot3d=True)
