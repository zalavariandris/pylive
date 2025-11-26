import watchfiles
import importlib
from imgui_bundle import imgui, immapp

import importlib.util
import sys
from pathlib import Path

def load_module_from_file(path):
    path = Path(path)
    module_name = path.stem   # e.g. "myscript" from "myscript.py"

    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return module

class ModuleHotReloader:
    def __init__(self, modules_to_watch: list = []):
        self.modules_to_watch = modules_to_watch
        self.watcher_threads = []

    def watch_module_file(self, module):
        import watchfiles, importlib
        path = module.__file__
        for changes in watchfiles.watch(path):
            print(f"File changed: {changes}")
            try:
                importlib.reload(module)
                print(f"Reloaded {module.__name__}")
            except Exception as e:
                print(f"Error reloading {module.__name__}: {e}")
                import traceback
                traceback.print_exc()

    def start_file_watchers(self):
        import threading
        for module in self.modules_to_watch:
            t = threading.Thread(
                target=self.watch_module_file,
                args=(module,),
                daemon=True
            )
            t.start()
            self.watcher_threads.append(t)

def start(module_filepath: str):
    # Dynamically import the module
    sketch_demo = load_module_from_file(module_filepath)

    # ---------------------------
    # GUI LOOP
    # ---------------------------
    hot_reloader = ModuleHotReloader([sketch_demo])
    hot_reloader.start_file_watchers()

    def gui():
        try:
            sketch_demo.draw()
        except SyntaxError as e:
            imgui.begin("Error")
            imgui.text(f"Syntax Error in sketch_demo.py: {e}")
            imgui.end()
        except Exception as e:
            imgui.begin("Error")
            imgui.text(f"Error in sketch_demo.py: {e}")
            imgui.end()

    immapp.run(gui)

if __name__ == "__main__":
    start("imsketch/sketch_demo.py")