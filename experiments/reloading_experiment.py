from reloading import reloading
from imgui_bundle import imgui, immapp


@reloading
def gui():
    imgui.text("Hello, world!")

if __name__ == "__main__":
    immapp.run(gui)