import typing
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError
from typing import List, Optional, Tuple

from PySide6.QtCore import Signal, QStringListModel, Qt, QObject
from PySide6.QtWidgets import QTextEdit, QApplication

import rope.base.project
from rope.contrib import codeassist
from pylive.QtScriptEditor.components.completer_for_textedit import TextEditCompleter


class RopeWorkerTask:
    """Encapsulates the rope task for the ThreadPoolExecutor."""
    def __init__(self, project, source_code: str, offset: int):
        self.project = project
        self.source_code = source_code
        self.offset = offset

    def run(self):
        """Perform the rope code assist task."""
        proposals = codeassist.code_assist(
            self.project,
            source_code=self.source_code,
            offset=self.offset
        )
        return codeassist.sorted_proposals(proposals)


class AsyncRopeCompleter(TextEditCompleter):
    def __init__(self, textedit: QTextEdit, rope_project):
        super().__init__(textedit)
        self.rope_project = rope_project
        self._thread_pool = ThreadPoolExecutor(max_workers=2)
        self._active_futures: List[Future] = []

        # Cleanup on widget destruction
        self.destroyed.connect(self.cleanup_workers)

    def cancelAllTasks(self):
        """Cancel all running tasks in the thread pool."""
        for future in self._active_futures:
            if not future.done():
                future.cancel()

        # Clear completed or canceled futures
        self._active_futures = [
            future for future in self._active_futures if not future.done()
        ]

    def requestCompletions(self):
        """Request completions using a thread pool."""
        # Cancel previous tasks
        self.cancelAllTasks()

        # Prepare a new task
        source_code = self.text_edit.toPlainText()
        offset = self.text_edit.textCursor().position()

        rope_task = RopeWorkerTask(self.rope_project, source_code, offset)

        # Submit task to the thread pool
        future = self._thread_pool.submit(rope_task.run)
        self._active_futures.append(future)

        # Attach callback
        future.add_done_callback(self._handle_completion)

    def _handle_completion(self, future: Future):
        """Handle the result of a completed task."""
        if future.cancelled():
            return  # Ignore canceled tasks

        try:
            proposals = future.result()  # Get the result
            self._update_completion_model(proposals)
        except Exception as e:
            self._handle_worker_error(e)

    def _update_completion_model(self, new_proposals):
        """Update completion model with new proposals."""
        if not isinstance(self.model(), QStringListModel):
            print("Error: Completion model is not of type QStringListModel")
            return

        try:
            completion_model = typing.cast(QStringListModel, self.model())
            completion_model.setStringList([proposal.name for proposal in new_proposals])
        except Exception as e:
            print(f"Error updating completion model: {e}")

    def _handle_worker_error(self, error: Exception):
        """Handle errors from workers."""
        print(f"Rope worker error: {error}")

    def cleanup_workers(self):
        """Clean up all running tasks and the thread pool."""
        self.cancelAllTasks()
        if hasattr(self, '_thread_pool'):
            self._thread_pool.shutdown(wait=True)


def main():
    app = QApplication([])
    editor = QTextEdit()

    rope_project = rope.base.project.Project('.')
    completer = AsyncRopeCompleter(editor, rope_project)

    editor.setWindowTitle("QTextEdit with Non-Blocking Rope Assist Completer")
    editor.resize(600, 400)
    editor.show()

    app.exec()


if __name__ == "__main__":
    main()
