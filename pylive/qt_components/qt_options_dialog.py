### todo: Support arbitrary QAbstractItemModel


from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class QOptionDialog(QDialog):
    def __init__(self, source_model:QAbstractItemModel, title="Choose an Option", parent:QWidget|None=None):
        super().__init__(parent=parent)
        self.setWindowTitle(title)
        self.setModal(True)

        # Remove the title bar but keep the frame
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.CustomizeWindowHint)

        # self.setSizeGripEnabled(False)
        # self.setWindowFlags(self.windowFlags() | Qt.MSWindowsFixedSizeDialogHint)

        # Prevent resizing by setting a fixed size policy (will not be resizable by the user)
        # self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # self.setStyleSheet("background: transparent;")
        # self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

        # Create layout
            
        self._allow_empty_selection = False

        # Setup Search
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Search...")

        # Setup List
        
        self.filteredmodel = QSortFilterProxyModel()
        self.filteredmodel.setSourceModel(source_model)
        self.filteredmodel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.line_edit.textChanged.connect(self.filteredmodel.setFilterWildcard)

        self._listview = QListView()
        self._listview.setModel(self.filteredmodel)
        self._listview.setSelectionMode(QListView.SelectionMode.SingleSelection)

        # OK and Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        # Connect buttons
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        main_layout = QVBoxLayout()

        main_layout.addWidget(self.line_edit)
        main_layout.addWidget(self._listview)
        main_layout.addLayout(button_layout)
        main_layout.setStretch(0,0)
        main_layout.setStretch(1,10)
        main_layout.setStretch(2,0)

        self.setLayout(main_layout)

        self.line_edit.setFocus()

        # Select the first item by default
        self._listview.setCurrentIndex(self.filteredmodel.index(0, 0))

        # Adjust the dialog size based on the content
        # self.line_edit.textChanged.connect(self._adjust_dialog_size)
        self.filteredmodel.modelReset.connect(lambda: self._adjust_dialog_size())
        self.filteredmodel.rowsInserted.connect(lambda: self._adjust_dialog_size())
        self.filteredmodel.rowsRemoved.connect(lambda: self._adjust_dialog_size())
        self._adjust_dialog_size()

        # Enable event filter for keyboard navigation
        self.line_edit.installEventFilter(self)

        self.adjustSize()

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)


    def setAllowEmptySelection(self, value:bool):
        self._allow_empty_selection = value

    def allowEmptySelection(self)->bool:
        return self._allow_empty_selection

    def sizeHint(self) -> QSize:
        return QSize(300,50)

    def _adjust_dialog_size(self):
        """Adjust the height of the list view and the dialog dynamically based on content."""
        row_count = self.filteredmodel.rowCount()
        if row_count > 0:
            # Get the height of one row and multiply by the number of rows
            row_height = self._listview.sizeHintForRow(0)
            max_visible_rows = 10  # Limit maximum visible rows
            visible_rows = min(row_count, max_visible_rows)
            list_height = row_height * visible_rows + 4  # Add a small margin
            self._listview.setMinimumHeight(list_height)
        else:
            self._listview.setMinimumHeight(0)


        self.adjustSize()  # Resize the dialog based on its content (line edit, listview, buttons)

    def eventFilter(self, obj, event:QEvent):
        if obj == self.line_edit and event.type() == event.Type.KeyPress:
            current_index = self._listview.currentIndex()
            if event.key() == Qt.Key.Key_Up:
                # Move up in the list
                self._move_selection(current_index, direction=-1)
                return True
            elif event.key() == Qt.Key.Key_Down:
                # Move down in the list
                self._move_selection(current_index, direction=1)
                return True
            # elif not current_index.isValid() and self.filteredmodel.rowCount()>0:
            #     self._move_selection(QModelIndex())
            #     return True

        return super().eventFilter(obj, event)

    def _move_selection(self, current_index, direction):
        """Move selection up or down based on direction."""

        row_count = self.filteredmodel.rowCount()
        if row_count == 0:
            return

        if not current_index.isValid():
            first_index = self._listview.model().index(0,0)
            self._listview.setCurrentIndex(first_index)

        else:

            # Calculate new row index
            new_row = current_index.row() + direction
            if 0 <= new_row < row_count:
                new_index = self.filteredmodel.index(new_row, 0)
                self._listview.setCurrentIndex(new_index)
                self._listview.scrollTo(new_index)  # Ensure visibility of the selection
            elif new_row<0 and self._allow_empty_selection:
                self._listview.setCurrentIndex(QModelIndex())

    def selectedOption(self)->QModelIndex:
        return self._listview.currentIndex()

    def filterText(self)->str:
        return self.line_edit.text()
    # def optionValue(self)->str:
    #     """Return the selected option or None if no option is selected."""
    #     indexes = self.listview.selectedIndexes()
    #     if indexes:
    #         return indexes[0].data()
    #     return None

    # def textValue(self):
    #     return self.line_edit.text()

    @staticmethod
    def getOption(options:list[str], parent:QWidget|None=None)->str|None:
        """Static method to open dialog and return selected option."""
        options_model = QStringListModel([f"{item}" for item in options])
        dialog = QOptionDialog(options_model, parent=parent)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            indexes = dialog._listview.selectedIndexes()
            return indexes[0].data()
        else:
            return None


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    options = ["print", "Path.read_text", "Path.write_text", "sample_function"]
    selected = QOptionDialog.getOption(options)
    print(selected)
    sys.exit(app.exec())



