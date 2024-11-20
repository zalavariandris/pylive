
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from typing import *

import rope.base.project
from rope.contrib import codeassist
from pylive.QtScriptEditor.components.completer_for_textedit import TextEditCompleter
import threading

class RopeWorkerTask(QRunnable):
    """Encapsulates the rope task for the QThreadPool."""
    def __init__(self, project, source_code: str, offset: int, callback):
        super().__init__()
        self.project = project
        self.source_code = source_code
        self.offset = offset
        self.callback = callback

    def run(self):
        """Perform the rope code assist task and invoke the callback."""
        # Check and print the thread details
        # make sure the current 
        app = QCoreApplication.instance()
        IsSeperateThread = app and QThread.currentThread() != app.thread()
        if not IsSeperateThread:
            print("warning: RopeTask does not run in a seperate thread")

        try:
            proposals = codeassist.code_assist(
                self.project,
                source_code=self.source_code,
                offset=self.offset
            )
            sorted_proposals = codeassist.sorted_proposals(proposals)
            self.callback(sorted_proposals)
        except Exception as e:
            print(e)
            self.callback([], error=e)


class AsyncRopeCompleter(TextEditCompleter):
    def __init__(self, textedit: QTextEdit, rope_project):
        super().__init__(textedit)
        self.rope_project = rope_project
        self._thread_pool = QThreadPool.globalInstance()
        self._active_tasks: List[RopeWorkerTask] = []

        # Cleanup on widget destruction
        self.destroyed.connect(self.cleanup_workers)

    def cancelAllTasks(self):
        """Cancel all running tasks by tracking task status."""
        self._active_tasks.clear()  # Clear the list of active tasks

    def requestCompletions(self):
        """Request completions using QThreadPool."""
        # Cancel previous tasks
        self.cancelAllTasks()

        # Prepare a new task
        source_code = self.text_edit.toPlainText()
        offset = self.text_edit.textCursor().position()

        def completion_callback(proposals, error=None):
            if error:
                self._handle_worker_error(error)
            else:
                self._update_completion_model(proposals)

        rope_task = RopeWorkerTask(self.rope_project, source_code, offset, completion_callback)
        self._active_tasks.append(rope_task)

        # Start the task in the thread pool
        self._thread_pool.start(rope_task)

    def _update_completion_model(self, new_proposals):
        """Update completion model with new proposals."""
        if not isinstance(self.model(), QStringListModel):
            print("Error: Completion model is not of type QStringListModel")
            return

        try:
            completion_model = cast(QStringListModel, self.model())
            completion_model.setStringList([proposal.name for proposal in new_proposals])
        except Exception as e:
            print(f"Error updating completion model: {e}")

    def _handle_worker_error(self, error: Exception):
        """Handle errors from workers."""
        print(f"Rope worker error: {error}")

    def cleanup_workers(self):
        """Clean up all running tasks."""
        self.cancelAllTasks()


def main():
    from pylive.thread_pool_tracker import ThreadPoolCounterWidget
    app = QApplication([])
    editor = QTextEdit()

    rope_project = rope.base.project.Project('.')
    window = QWidget()
    mainLayout = QVBoxLayout()
    mainLayout.setContentsMargins(0,0,0,0)
    window.setLayout(mainLayout)

    completer = AsyncRopeCompleter(editor, rope_project)

    mainLayout.addWidget(editor)
    mainLayout.addWidget(ThreadPoolCounterWidget())
    window.setWindowTitle("QTextEdit with Non-Blocking Rope Assist Completer")
    window.resize(600, 400)
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
