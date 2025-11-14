from imgui_bundle import immapp

import watchfiles
import importlib
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

# ModuleHotReloader([solver, ui.viewer]).start_file_watchers()

from imgui_bundle import imgui
import threading

class Sketchbook:
    def __init__(self, script:str, gui_function_name:str='gui'):
        self._gui = lambda: imgui.text("No GUI defined yet.")

        self.watch_thread = threading.Thread(
            target=self.watching,
            args=(),
            daemon=True
        )

        self._script = script
        self._gui_function_name = gui_function_name
        self._hot_reload=True

        self._module = None

    def watching(self):
        for changes in watchfiles.watch(self._script):
            print(f"File changed: {changes}")
            try:
                exec(open(self._script).read(), self._module.__dict__)
                importlib.reload(self._module)
                print(f"Reloaded {self._module.__name__}")
                self._gui = getattr(self._module, self._gui_function_name, self._gui)
            except Exception as e:
                print(f"Error reloading {self._module.__name__}: {e}")
                import traceback
                traceback.print_exc()

    def frame(self):
        self._gui()

    def start(self):
        import importlib.util
        import sys

        spec = importlib.util.spec_from_file_location(self._script, self._script)
        self._module = importlib.util.module_from_spec(spec)
        sys.modules[self._module.__name__] = self._module
        spec.loader.exec_module(self._module)
        # self._module = importlib.import_module("sketch")
        self._gui = getattr(self._module, self._gui_function_name, self._gui)

        self.watch_thread.start()
        immapp.run(self.frame)