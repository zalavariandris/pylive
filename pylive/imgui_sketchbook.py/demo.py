from imgui_bundle import imgui
def gui():
    imgui.begin("Hello, ImGui!")
    imgui.text("This is a simple asd window.")
    imgui.end()

if __name__ == "__main__":
    import sketchbook
    
    app = sketchbook.Sketchbook(__file__)
    app.start()