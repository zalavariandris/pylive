

from typing import Any, List, Tuple, Dict
from imgui_bundle import imgui, immapp, imgui_ctx

# Local application imports
from pylive import imx

# Configure logging to see shader compilation logs
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@immapp.static(
    my_point=imgui.ImVec2(50,50))
def gui():
    imgui.begin("MyPlotWindow", None)
    _, gui.my_point.x = imgui.slider_float("x", gui.my_point.x, 0, 100)
    _, gui.my_point.y = imgui.slider_float("y", gui.my_point.y, 0, 100)
    if imx.myplot.begin_plot("my_plot", (100,100), None):
        imx.myplot.setup_orthographic(0,0,100,100)
        _, gui.my_point = imx.myplot.point_handle("origin", gui.my_point)
    imx.myplot.end_plot()
    imgui.end()
    

if __name__ == "__main__":
    immapp.run(gui, window_title="imx(my imgui extensions)", window_size=(1200, 1200), with_implot3d=True)

