from typing import *

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *



class ThreadPoolWatcher(QObject):
    """
    A QObject-based model to monitor QThreadPool.globalInstance()
    and emit signals when the active thread count changes.
    """
    activeThreadsCountChanged = Signal(int)  # Emits the current number of active threads
    idleChanged = Signal()           # Emits when the thread pool becomes idle

    def __init__(self, parent=None, poll_intervall_ms=10):
        super().__init__(parent)
        self.thread_pool = QThreadPool.globalInstance()
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.check_thread_pool)
        self.poll_timer.start(poll_intervall_ms)  # Poll every 500ms

        self._last_active_threads = self.thread_pool.activeThreadCount()

    def check_thread_pool(self):
        """
        Periodically checks the state of the thread pool and emits signals on changes.
        """
        current_active_threads = self.thread_pool.activeThreadCount()

        if current_active_threads != self._last_active_threads:
            self.activeThreadsCountChanged.emit(current_active_threads)
            self._last_active_threads = current_active_threads

        if current_active_threads == 0 and self._last_active_threads != 0:
            self.idleChanged.emit()

    def isIdle(self):
        return self.thread_pool.activeThreadCount() == 0

    def activeThreadsCount(self):
        return self.thread_pool.activeThreadCount()



class ThreadPoolCounterWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Global QThreadPool Tracker")

        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0,0,0,0)
        self.counter_label = QLabel("current_thread_count:")
        
        mainLayout.addWidget(self.counter_label)
        self.setLayout(mainLayout)

        self.watcher = ThreadPoolWatcher(self)
        self.watcher.activeThreadsCountChanged.connect(self.onActiveThreadsChanged)

        self.update_ui()

    def onActiveThreadsChanged(self):
        self.update_ui()

    def update_ui(self):
        if self.watcher.isIdle():
            self.counter_label.setText(f"Threadpool: Idle")
        else:
            self.counter_label.setText(f"Threadpool: {self.watcher.activeThreadsCount()}")



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    watcher = ThreadPoolWatcher()

    class Task(QRunnable):
        """
        A simple QRunnable for demonstration.
        """
        def __init__(self, name):
            super().__init__()
            self.name = name

        def run(self):
            import time
            time.sleep(1)  # Simulate work

    # create dummy tasks
    for i in range(10):
        task = Task(f"Task-{i+1}")
        QThreadPool.globalInstance().start(task)

    window = QWidget()
    window.setLayout(QVBoxLayout())
    window.layout().addWidget(ThreadPoolCounterWidget())
    btn = QPushButton("add new thread")
    btn.pressed.connect(lambda: QThreadPool.globalInstance().start( Task(f"Task-{i+1}") ))
    window.layout().addWidget(btn)
    window.show()


    sys.exit(app.exec())
