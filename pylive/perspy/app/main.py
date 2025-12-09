# Standard library imports
import os
os.environ['PYTHONUTF8'] = '1'

from pathlib import Path
import locale

# Third-party imports
from loguru import logger

# Local application imports
from pylive.perspy.core import solver
import ui

# ########### #
# Application #
# ########### #

from pylive.perspy.app.app import PerspyApp

if __name__ == "__main__":
    from imgui_bundle import immapp
    from imgui_bundle import hello_imgui
    from hello_imgui_config import create_my_runner_params
    from pylive.perspy.app.hot_reloader import HotModuleReloader

    app = PerspyApp()
    assets_folder = Path(__file__).parent / "assets"
    assert assets_folder.exists(), f"Assets folder not found: {assets_folder.absolute()}"
    logger.info(f"setting assets folder: {assets_folder.absolute()}")
    hello_imgui.set_assets_folder(str(assets_folder.absolute()))
    runner_params = create_my_runner_params(app.draw_gui, app.setup_gui, app.on_file_drop, "Perspy v0.5.0")
    HotModuleReloader([solver, ui.viewer]).start_file_watchers()
    hello_imgui.run(runner_params)

