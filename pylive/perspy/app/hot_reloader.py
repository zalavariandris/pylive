# ############ #
# Hot Module Reloader #
# ############ #

from loguru import logger

import watchfiles
import importlib
import threading
class HotModuleReloader:
    def __init__(self, modules_to_watch: list = []):
        self.modules_to_watch = modules_to_watch
        self.watcher_threads = []

    def watch_module_file(self, module):
        path = module.__file__
        for changes in watchfiles.watch(path):
            logger.info(f"File changed: {changes}")
            try:
                importlib.reload(module)
                logger.info(f"Reloaded {module.__name__}")
            except Exception as e:
                logger.error(f"Error reloading {module.__name__}: {e}")

    def start_file_watchers(self):
        
        for module in self.modules_to_watch:
            t = threading.Thread(
                target=self.watch_module_file,
                args=(module,),
                daemon=True
            )
            t.start()
            self.watcher_threads.append(t)