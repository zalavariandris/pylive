from imgui_bundle import imgui

def setup():
    pass

def draw():
    imgui.begin("Demo Sketch Window")
    imgui.text("This is a demo Sketch!")
    imgui.end()