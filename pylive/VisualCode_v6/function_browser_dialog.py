from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

import sys
import inspect


class PyObjectItem:
    def __init__(self, obj:object, parent:Self|None=None):
        self._obj = obj
        self._children = []
        self._parent = parent
        if parent:
            parent._children.append(self)

    def child(self, row:int):
        return self._children[row] if 0 <= row < len(self._children) else None

    def child_count(self)->int:
        return len(self._children)

    def row(self)->int:
        return self._parent._children.index(self) if self._parent else 0

    def obj(self):
        return self._obj


class FunctionsTreeModel(QAbstractItemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.root_item = PyObjectItem("Python Modules")
        self._populate_tree()

    def _populate_tree(self):
        # global_values = {obj for obj in globals().values() if inspect.ismodule(obj)}

        for obj in globals().values():
            if inspect.ismodule(obj):
                module = obj
                module_item = PyObjectItem(module, self.root_item)
                
                # # # Add classes
                # for name, obj in inspect.getmembers(module, predicate=inspect.isclass):
                #     PyObjectItem(obj=obj, parent=module_item)
                
                # Add functions
                for name, obj in inspect.getmembers(module, predicate=callable):
                    PyObjectItem(obj=obj, parent=module_item)
            elif inspect.isfunction(obj):
                func = obj
                function_item = PyObjectItem(func, self.root_item)

    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()
        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        print("parent called")

        child_item = index.internalPointer()
        parent_item = child_item._parent
        if parent_item == self.root_item:
            return QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return self.root_item.child_count()
        return parent.internalPointer().child_count()

    def columnCount(self, parent=QModelIndex()):
        return 1

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        item = index.internalPointer()
        if role == Qt.ItemDataRole.DisplayRole:
            try:
                return item.obj().__name__
            except AttributeError:
                return f"{item.obj()}"
        return None


class FunctionsBrowserWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Imported Modules Tree")
        self.setGeometry(100, 100, 800, 600)
        
        layout = QVBoxLayout()
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter modules, classes, or functions...")
        layout.addWidget(self.filter_edit)
        
        self.tree_view = QTreeView()
        layout.addWidget(self.tree_view)
        
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        
        self.model = FunctionsTreeModel()
        self.proxy_model = QSortFilterProxyModel()

        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.sort(0, Qt.SortOrder.AscendingOrder)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        
        self.tree_view.setModel(self.proxy_model)
        self.filter_edit.textChanged.connect(self.updateFilter)
    
    def updateFilter(self, text):
        self.proxy_model.setFilterFixedString(text)
        self.expandMatchingItems()
    
    def expandMatchingItems(self):
        def expand_recursively(index):
            if not index.isValid():
                return
            self.tree_view.setExpanded(index, True)
            for i in range(self.proxy_model.rowCount(index)):
                child_index = self.proxy_model.index(i, 0, index)
                expand_recursively(child_index)
        
        root_index = self.proxy_model.index(0, 0, QModelIndex())
        expand_recursively(root_index)


class FunctionsBrowserDialog(QDialog):
    def updateFilter(self, text):
        self.filteredmodel.setFilterWildcard(text)
        if text:
            self._treeview.expandAll()
        else:
            self._treeview.collapseAll()
        self._adjust_dialog_size()

    def __init__(self,title="Choose an Option", parent:QWidget|None=None):
        super().__init__(parent=parent)
        self.setWindowTitle(title)
        self.setModal(True)
        # Create layout
            
        self._allow_empty_selection = False

        # Setup Search
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Search...")

        # Setup List
        source_model = FunctionsTreeModel()
        self.filteredmodel = QSortFilterProxyModel()
        self.filteredmodel.setSourceModel(source_model)
        self.filteredmodel.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filteredmodel.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.filteredmodel.sort(0, Qt.SortOrder.AscendingOrder)
        self.filteredmodel.setRecursiveFilteringEnabled(True)
        self.line_edit.textChanged.connect(self.updateFilter)

        self._treeview = QTreeView()
        self._treeview.setHeaderHidden(True)
        self._treeview.setModel(self.filteredmodel)
        self._treeview.setSelectionMode(QListView.SelectionMode.SingleSelection)

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
        main_layout.addWidget(self._treeview)
        main_layout.addLayout(button_layout)

        main_layout.setStretch(0,0)
        main_layout.setStretch(1,10)
        main_layout.setStretch(2,0)

        self.setLayout(main_layout)

        self.line_edit.setFocus()

        # Select the first item by default
        self._treeview.setCurrentIndex(self.filteredmodel.index(0, 0))

        # Adjust the dialog size based on the content
        self.line_edit.textChanged.connect(self._adjust_dialog_size)
        # self.filteredmodel.modelReset.connect(lambda: self._adjust_dialog_size())
        # self.filteredmodel.rowsInserted.connect(lambda: self._adjust_dialog_size())
        # self.filteredmodel.rowsRemoved.connect(lambda: self._adjust_dialog_size())
        self._adjust_dialog_size()

        # Enable event filter for keyboard navigation
        self.line_edit.installEventFilter(self)

        self.adjustSize()

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)

    def autoExpandMatches(self, parent:QModelIndex=QModelIndex()):
        """
        Expands all parent items that have children matching the filter
        
        Args:
            view: QTreeView instance
            proxy_model: QSortFilterProxyModel with recursive filtering enabled
            parent: The parent index to start from (None for root)
        """
        if not parent.isValid() is None:
            parent = self.filteredmodel.index(0, 0, parent).parent()
        
        # Check if this parent has any children
        row_count = self.filteredmodel.rowCount(parent)
        has_matching_child = False
        
        # Check each child
        for row in range(row_count):
            child_index = self.filteredmodel.index(row, 0, parent)
            
            # Recursively process this child's children
            if self.filteredmodel.hasChildren(child_index):
                child_has_match = self.autoExpandMatches(child_index)
                if child_has_match:
                    has_matching_child = True
            
            # If this child passes the filter directly, mark parent for expansion
            source_row = self.filteredmodel.mapToSource(child_index).row()
            source_parent = self.filteredmodel.mapToSource(parent)
            if self.filteredmodel.filterAcceptsRow(source_row, source_parent):
                has_matching_child = True
        
        # If this parent has any matching children, expand it
        if has_matching_child and parent.isValid():
            self._treeview.expand(parent)
        
        return has_matching_child

    def setAllowEmptySelection(self, value:bool):
        self._allow_empty_selection = value

    def allowEmptySelection(self)->bool:
        return self._allow_empty_selection

    def sizeHint(self) -> QSize:
        return QSize(300,50)

    def _adjust_dialog_size(self):
        """Adjust the height of the list view and the dialog dynamically based on content."""
        total_height = self.calculate_tree_height(self._treeview.rootIndex())
        self._treeview.setFixedHeight(min(total_height, 500))
        self.adjustSize()  # Resize the dialog based on its content (line edit, listview, buttons)

    def calculate_tree_height(self, parent_index: QModelIndex):
        """Recursively calculates height of visible rows, including expanded children."""
        total_height = 0
        model = self._treeview.model()
        row_count = model.rowCount(parent_index)

        for row in range(row_count):
            index = model.index(row, 0, parent_index)
            total_height += self._treeview.sizeHintForRow(row)

            # If expanded, add child row heights
            if self._treeview.isExpanded(index):
                total_height += self.calculate_tree_height(index)

        return total_height

    def eventFilter(self, obj, event:QEvent):
        if obj == self.line_edit and event.type() == event.Type.KeyPress:
            current_index = self._treeview.currentIndex()
            if event.key() == Qt.Key.Key_Up:
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
            first_index = self._treeview.model().index(0,0)
            self._treeview.setCurrentIndex(first_index)

        else:

            # Calculate new row index
            new_row = current_index.row() + direction
            if 0 <= new_row < row_count:
                new_index = self.filteredmodel.index(new_row, 0)
                self._treeview.setCurrentIndex(new_index)
                self._treeview.scrollTo(new_index)  # Ensure visibility of the selection
            elif new_row<0 and self._allow_empty_selection:
                self._treeview.setCurrentIndex(QModelIndex())

    def selectedOption(self)->QModelIndex:
        return self._treeview.currentIndex()

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
    def getFunction(parent:QWidget|None=None)->str|None:
        """Static method to open dialog and return selected option."""
        dialog = FunctionsBrowserDialog(parent=parent)
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            indexes = dialog._treeview.selectedIndexes()
            return indexes[0].data()
        else:
            return None



if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    selected = FunctionsBrowserDialog.getFunction()
    print(selected)
    sys.exit(app.exec())
