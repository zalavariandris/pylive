from imgui_bundle import imgui, immapp

def gui():
    imgui.begin("Hello, ImGui!")
    imgui.text("This is a simple asd window.")
    imgui.end()

if __name__ == "__main__":
    immapp.run(gui, window_title="Sketchbook")