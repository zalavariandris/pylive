import sys
import inspect
from collections import defaultdict
from typing import Dict, List, Tuple, Any, Optional, Union, Callable, DefaultDict

from PySide6.QtCore import QPersistentModelIndex, Qt, QSortFilterProxyModel, QModelIndex, QAbstractItemModel
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QTreeView, QLineEdit, QLabel)


class FunctionsModel(QAbstractItemModel):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.modules: List[str] = []
        self.module_functions: DefaultDict[str, List[Tuple[str, Callable]]] = defaultdict(list)
        self.load_modules()
        
    


class FunctionsBrowser(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.model: FunctionsModel = FunctionsModel()
        self.proxy_model: QSortFilterProxyModel = QSortFilterProxyModel()
        self.tree_view: QTreeView = QTreeView()
        self.search_edit: QLineEdit = QLineEdit()
        self.status_label: QLabel = QLabel()
        self.setup_ui()
        
    def setup_ui(self) -> None:
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create title
        title_label = QLabel("Python Functions Browser")
        title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        layout.addWidget(title_label)
        
        # Create search box
        self.search_edit.setPlaceholderText("Search functions...")
        layout.addWidget(self.search_edit)
        
        # Create tree view
        self.tree_view.setAlternatingRowColors(True)
        layout.addWidget(self.tree_view)
        
        # Create proxy model for filtering
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setRecursiveFilteringEnabled(True)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        
        # Set proxy model on tree view
        self.tree_view.setModel(self.proxy_model)
        
        # Connect search box to filter
        self.search_edit.textChanged.connect(self.filter_functions)
        
        # Add status label
        self.status_label.setText(f"Loaded {len(self.model.modules)} modules")
        layout.addWidget(self.status_label)
        
    def filter_functions(self, text: str) -> None:
        try:
            self.proxy_model.setFilterFixedString(text)
            
            # Expand all items when filtering is active
            if text:
                self.tree_view.expandAll()
            else:
                self.tree_view.collapseAll()
                
            # Update status
            visible_count = self.count_visible_items()
            self.status_label.setText(f"Showing {visible_count} results of {len(self.model.modules)} modules")
        except Exception as e:
            self.status_label.setText(f"Error filtering: {str(e)}")
            
    def count_visible_items(self) -> int:
        """Count visible items in the filtered view"""
        count = 0
        for i in range(self.proxy_model.rowCount()):
            count += 1  # Count the module
            idx = self.proxy_model.index(i, 0)
            count += self.proxy_model.rowCount(idx)  # Count its functions
        return count


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    main_window = QMainWindow()
    main_window.setWindowTitle("Python Functions Browser")
    main_window.resize(800, 600)
    
    browser = FunctionsBrowser()
    main_window.setCentralWidget(browser)
    
    main_window.show()
    sys.exit(app.exec())