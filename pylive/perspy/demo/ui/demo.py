
class App:
    def draw_gui(self):
        pass

    def setup_gui(self):
        pass

    def on_file_drop(self, file_paths):
        pass

if __name__ == "__main__":
    from imgui_bundle import immapp
    from imgui_bundle import hello_imgui
    from pylive.perspy.demo.hello_imgui_config import create_my_runner_params
    app = App()
    # assets_folder = Path(__file__).parent / "assets"
    # assert assets_folder.exists(), f"Assets folder not found: {assets_folder.absolute()}"
    # print("setting assets folder:", assets_folder.absolute())
    # hello_imgui.set_assets_folder(str(assets_folder.absolute()))
    runner_params = create_my_runner_params(app.draw_gui, app.setup_gui, app.on_file_drop, "Perspy v0.5.0")
    hello_imgui.run(runner_params)

