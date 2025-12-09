from loguru import logger
from imgui_bundle import imgui, immapp


def gui():
    imgui.text("Hello, World!")

if __name__ == "__main__":
    immapp.run(gui)