# ############ #
# Hot Reloader #
# ############ #


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

if __name__ == "__main__":
    ModuleHotReloader([solver]).start_file_watchers()