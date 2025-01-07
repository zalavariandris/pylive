import sys

from typing import *

from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.QtLiveApp.live_script_skeleton import LiveScriptWindow, Placeholder
from pylive.QtScriptEditor.components.textedit_completer import (
    TextEditCompleter,
)
from pylive.QtScriptEditor.script_edit import ScriptEdit

import logging

logger = logging.getLogger(__name__)

from io import StringIO

from pylive.QtScriptEditor.cell_support import cell_at_line, split_cells

from pylive.QtScriptEditor.components.async_jedi_completer import (
    AsyncJediCompleter,
)
from pylive.QtTerminal.terminal_with_exec import Terminal
from pylive.QtLiveApp.file_link import FileLink

import logging

logger = logging.getLogger(__name__)


from pylive.QtScriptEditor.cell_support import Cell, split_cells, cell_at_line

from dataclasses import dataclass


class ScriptEditWithCells(ScriptEdit):
    cellsContentChanged = Signal(list)  # List[int]

    def __init__(self, parent=None):
        super().__init__(parent)

        self._cells = []
        self.textChanged.connect(lambda: self.updateCells())
        self.updateCells()

    def updateCells(self):
        ### Cells support ###
        cells = split_cells(self.toPlainText(), strip=True)

        # find changed cells
        indexes_changed = []
        from itertools import zip_longest

        for i, cell in enumerate(cells):
            current = self._cells[i] if i < len(self._cells) else None
            if current != cell:
                if (
                    current is None
                    or current.content.strip() != cell.content.strip()
                ):
                    indexes_changed.append(i)

        # update
        self._cells = cells
        self.cellsContentChanged.emit(sorted(indexes_changed))

        # update cell bars
        self.lineNumberArea.clearBars()
        for cell in cells:
            self.lineNumberArea.insertBar(
                cell.lineno, cell.lineno + cell.lineCount() - 1
            )

    def cell(self, idx: int) -> Cell:
        cell = self._cells[idx]
        assert isinstance(cell, Cell)
        return cell

    def cellCount(self):
        return len(self._cells)

    def cellAtCursor(self):
        cursor = self.textCursor()

        blockNumber = cursor.blockNumber()  # 0 index
        return cell_at_line(self._cells, blockNumber + 1)


import ast
from pathlib import Path


class LiveScriptWithExec(LiveScriptWindow):
    @override
    def setupUI(self):
        super().setupUI()

        ### Console widget ###
        terminal = Terminal()
        self.setTerminal(terminal)
        terminal.exceptionThrown.connect(
            lambda exc: self.editor().linter.lintException(exc, "underline")
        )

        terminal.setContext({"__name__": "__live__"})

        ### Script Editor
        editor = ScriptEditWithCells()
        self.setEditor(editor)
        self.editor().cellsContentChanged.connect(
            lambda indexes: self.execute_cells(indexes)
        )

        ### File link
        self.fileLink = FileLink(editor.document())
        self.fileLink.filePathChanged.connect(self.updateWindowTitle)
        editor.document().modificationChanged.connect(self.updateWindowTitle)

        ### File Menu ###
        filemenu = self.fileLink.createFileMenu()
        if self.menuBar().actions():
            self.menuBar().insertMenu(self.menuBar().actions()[0], filemenu)
        else:
            self.menuBar().addMenu(filemenu)

        restart_action = QAction("restart", self)
        restart_action.triggered.connect(lambda: self.restart())
        self.menuBar().addAction(restart_action)

        ### update widet title
        self.updateWindowTitle()

        ### add shift enter behaviour
        editor.installEventFilter(self)

    def restart(self):
        import os
        import sys

        print("ARGTV:", sys.argv)
        if self.fileLink.filepath:
            argv = [arg for arg in sys.argv]
            if len(argv) > 1:
                argv[1] = self.fileLink.filepath
            else:
                argv.append(self.fileLink.filepath)
            os.execl(sys.executable, os.path.abspath(__file__), *argv)
        else:
            os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        # run cell on +hift+Enter
        if watched == self.editor() and event.type() == QEvent.Type.KeyPress:
            keypress = cast(QKeyEvent, event)
            if keypress.key() in {Qt.Key.Key_Return, Qt.Key.Key_Enter}:
                if keypress.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    cell = self.editor().cellAtCursor()
                    self.execute_cells([cell])
                    return True

        return super().eventFilter(watched, event)

    @override
    def editor(self) -> ScriptEditWithCells:
        return cast(ScriptEditWithCells, super().editor())

    def execute_cells(self, indexes: List[int]):
        self.editor().linter.clear()
        for cell_idx in indexes:
            logger.info(f"execute_cell: {cell_idx}")

            # first_line = self.editor().cell(cell).split("\n")[0]

            # prepend empty lines, so when an exception occures, the linnumber will match the while script lines
            cell_line_offset = 0
            for i in range(cell_idx):
                cell_source = self.editor().cell(cell_idx).content
                line_count = len(cell_source.split("\n"))
                cell_line_offset += line_count
            cell_source = self.editor().cell(cell_idx).content
            cell_source = "\n" * cell_line_offset + cell_source

            logger.info("executing code...")

            terminal = cast(Terminal, self.terminal())
            terminal.clear()

            if cell_source.strip():
                self._current_cell = cell_idx
                terminal.execute(cell_source)
            self.statusBar().showMessage(f"cells executed {indexes}")

            logger.info("code executed!")

    def updateWindowTitle(self):
        file_title = "untitled"
        if self.fileLink.filepath:
            file_title = Path(self.fileLink.filepath).name

        modified_mark = ""
        if self.editor().document().isModified():
            modified_mark = "*"

        self.setWindowTitle(
            f"{file_title} {modified_mark} - LiveScript (using exec)"
        )

    def closeEvent(self, event):
        DoCloseFile = self.fileLink.closeFile()
        if not DoCloseFile:
            event.ignore()
            return

        event.accept()


if __name__ == "__main__":
    # configure logging
    import logging

    log_format = "%(levelname)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    # create livecsript app
    app = QApplication(sys.argv)

    window = LiveScriptWithExec.instance()
    live = LiveScriptWindow.instance()
    live = LiveScriptWindow.instance()
    window.show()

    if len(sys.argv) > 1:
        window.fileLink.openFile(sys.argv[1])
    else:
        # set initial code
        from textwrap import dedent

        script = dedent(
            '''\
            #%% setup
            from PySide6.QtWidgets import *
            from pylive.QtLiveApp import display

            #%% update
            print(f"Print this {42} to the console!")

            display("""\\
            Display this *text*
            or any *QWidget* 
            in the preview area.

            (here is a nubmer for dragging 10)
            """)
        '''
        )
        window.editor().setPlainText(script)

    # launch QApp
    sys.exit(app.exec())
