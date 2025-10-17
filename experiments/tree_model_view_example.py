from PySide6.QtCore import Qt, QAbstractItemModel, QModelIndex
from PySide6.QtWidgets import QApplication, QTreeView, QMainWindow
import sys

class TreeNode:
    def __init__(self, data, parent=None):
        self._data = data
        self.parent = parent
        self.children = []
    
    def append_child(self, child):
        child.parent = self
        self.children.append(child)
    
    def child(self, row):
        return self.children[row] if 0 <= row < len(self.children) else None
    
    def child_count(self):
        return len(self.children)
    
    def column_count(self):
        return len(self._data)
    
    def row(self):
        return self.parent.children.index(self) if self.parent else 0
    
    def data(self, column):
        return self._data[column] if 0 <= column < len(self._data) else None

class TreeModel(QAbstractItemModel):
    def __init__(self, root_data, parent=None):
        super().__init__(parent)
        self.root_node = TreeNode(root_data)
    
    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            return self.root_node.child_count()
        return parent.internalPointer().child_count()
    
    def columnCount(self, parent=QModelIndex()):
        return self.root_node.column_count()
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        return index.internalPointer().data(index.column())
    
    def index(self, row, column, parent=QModelIndex()):
        if not parent.isValid():
            parent_node = self.root_node
        else:
            parent_node = parent.internalPointer()
        
        child_node = parent_node.child(row)
        if child_node:
            return self.createIndex(row, column, child_node)
        return QModelIndex()
    
    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        
        child_node = index.internalPointer()
        parent_node = child_node.parent
        
        if parent_node == self.root_node:
            return QModelIndex()
        
        return self.createIndex(parent_node.row(), 0, parent_node)

class TreeModelExample(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("QTreeView with QAbstractItemModel")
        self.setGeometry(100, 100, 400, 300)
        
        self.tree_view = QTreeView(self)
        self.setCentralWidget(self.tree_view)
        
        # Create model
        self.model = TreeModel(["Name", "Description"])
        
        # Populate tree
        root = self.model.root_node
        parent_item = TreeNode(["Parent Node", "Root Description"], root)
        parent_item.append_child(TreeNode(["Child 1", "First child node"], parent_item))
        parent_item.append_child(TreeNode(["Child 2", "Second child node"], parent_item))
        root.append_child(parent_item)
        
        self.tree_view.setModel(self.model)
        self.tree_view.expandAll()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TreeModelExample()
    window.show()
    sys.exit(app.exec())