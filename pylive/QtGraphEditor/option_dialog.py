from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class OptionDialog(QDialog):
    def __init__(self, options, title="Choose an Option", parent=None):
        super().__init__(parent)
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


        self.options = options

        # Create layout
        self.layout = QVBoxLayout()

        # Setup Search
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Search...")
        self.layout.addWidget(self.line_edit)

        # Setup List
        self.optionsmodel = QStringListModel(options)
        self.filteredmodel = QSortFilterProxyModel()
        self.filteredmodel.setSourceModel(self.optionsmodel)
        self.filteredmodel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.line_edit.textChanged.connect(self.filteredmodel.setFilterWildcard)

        self.listview = QListView()
        self.listview.setModel(self.filteredmodel)
        self.listview.setSelectionMode(QListView.SelectionMode.SingleSelection)
        self.layout.addWidget(self.listview)

        # OK and Cancel buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        # Connect buttons
        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        self.layout.addLayout(button_layout)

        self.setLayout(self.layout)
        self.line_edit.setFocus()

        # Select the first item by default
        if options:
            self.listview.setCurrentIndex(self.filteredmodel.index(0, 0))

        # Adjust the dialog size based on the content
        self.line_edit.textChanged.connect(self.adjust_dialog_size)
        self.adjust_dialog_size()

        # Enable event filter for keyboard navigation
        self.line_edit.installEventFilter(self)

    def adjust_dialog_size(self):
        """Adjust the height of the list view and the dialog dynamically based on content."""
        row_count = self.filteredmodel.rowCount()
        if row_count > 0:
            # Get the height of one row and multiply by the number of rows
            row_height = self.listview.sizeHintForRow(0)
            max_visible_rows = 10  # Limit maximum visible rows
            visible_rows = min(row_count, max_visible_rows)
            list_height = row_height * visible_rows + 2  # Add a small margin
            self.listview.setFixedHeight(list_height)
        else:
            self.listview.setFixedHeight(0)

        # Adjust dialog size based on its content
        # self.setMinimumSize(QSize(30, 100))
        # self.setMaximumSize(QSize(400, 800))
        self.adjustSize()  # Resize the dialog based on its content (line edit, listview, buttons)
        # self.setMinimumSize(self.size())
        # self.setMaximumSize(self.size())
        # self.setFixedSize(self.size())

    def eventFilter(self, obj, event):
        if obj == self.line_edit and event.type() == event.Type.KeyPress:
            current_index = self.listview.currentIndex()
            if event.key() == Qt.Key.Key_Up:
                # Move up in the list
                self.move_selection(current_index, direction=-1)
                return True
            elif event.key() == Qt.Key.Key_Down:
                # Move down in the list
                self.move_selection(current_index, direction=1)
                return True
        return super().eventFilter(obj, event)

    def move_selection(self, current_index, direction):
        """Move selection up or down based on direction."""
        if not current_index.isValid():
            return

        row_count = self.filteredmodel.rowCount()
        if row_count == 0:
            return

        # Calculate new row index
        new_row = current_index.row() + direction
        if 0 <= new_row < row_count:
            new_index = self.filteredmodel.index(new_row, 0)
            self.listview.setCurrentIndex(new_index)
            self.listview.scrollTo(new_index)  # Ensure visibility of the selection

    def get_selected_option(self):
        """Return the selected option text or None if no option is selected."""
        indexes = self.listview.selectedIndexes()
        if indexes:
            return indexes[0].data()
        return None

    @staticmethod
    def getOption(options, parent=None):
        """Static method to open dialog and return selected option."""
        dialog = OptionDialog(options, parent)
        result = dialog.exec()
        return dialog.get_selected_option() if result == QDialog.DialogCode.Accepted else None


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    options = ["print", "Path.read_text", "Path.write_text", "sample_function"]
    selected = OptionDialog.getOption(options)
    print(selected)
    sys.exit(app.exec())




# from pylive import livescript
# livescript.display(OptionDialog([]))
if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	options = ["print", "Path.read_text", "Path.write_text", "sample_function"]
	selected = OptionDialog.getOption(options)
	print(selected)
	sys.exit(app.exec())

