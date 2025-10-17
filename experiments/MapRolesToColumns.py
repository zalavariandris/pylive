from PySide6.QtCore import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


# The source model: a list model where each row has multiple roles (DisplayRole, EditRole, etc.)
class ListModel(QAbstractItemModel):
    def __init__(self, data=None):
        super().__init__()
        self.data_storage = [
            ("Node 1", "Editable Node 1", "Tooltip for Node 1"),
            ("Node 2", "Editable Node 2", "Tooltip for Node 2"),
            ("Node 3", "Editable Node 3", "Tooltip for Node 3"),
        ]
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.data_storage)
    
    def columnCount(self, parent=QModelIndex()):
        return 1  # This model has only one column
    
    def data(self, index: QModelIndex, role: int):
        if not index.isValid():
            return None
        
        row = index.row()
        
        # Return data for each role (DisplayRole, EditRole, TooltipRole)
        if role == Qt.DisplayRole:
            return self.data_storage[row][0]  # Display data for column 0
        elif role == Qt.EditRole:
            return self.data_storage[row][1]  # Editable data for column 1
        elif role == Qt.ToolTipRole:
            return self.data_storage[row][2]  # Tooltip data for column 2
        
        return None


# The proxy model that transforms the data into a table format
class MapListToTable(QIdentityProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def columnCount(self, parent=QModelIndex()):
        # This proxy model should have as many columns as the roles we want to display.
        return 3  # We have three roles: DisplayRole, EditRole, ToolTipRole

    def mapToSource(self, proxyIndex):
        row, col = proxyIndex.row(), proxyIndex.column()
        print("map to source", row, col)
        return proxyIndex

    def mapFromSource(self, sourceIndex:QModelIndex):
        row, col = sourceIndex.row(), sourceIndex.column()
        print("map from source", row, col)
        return sourceIndex
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        """Provide headers for each column based on roles."""
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section == 0:
                    return "Display Data"  # Column 0 will show 'Display Data'
                elif section == 1:
                    return "Editable Data"  # Column 1 will show 'Editable Data'
                elif section == 2:
                    return "Tooltip Data"  # Column 2 will show 'Tooltip Data'
        
        return super().headerData(section, orientation, role)
    
    def data(self, index: QModelIndex, role: int):
        """Map roles to columns in the proxy model."""
        row = index.row()
        column = index.column()
        
        # Map the proxy model index to the source model index
        source_index = self.mapToSource(index)
        
        if column == 0:
            # Display the data for DisplayRole
            if role == Qt.DisplayRole:
                return self.sourceModel().data(source_index, Qt.DisplayRole)
            elif role == Qt.EditRole:
                return self.sourceModel().data(source_index, Qt.EditRole)
            elif role == Qt.ToolTipRole:
                return self.sourceModel().data(source_index, Qt.ToolTipRole)
        
        elif column == 1:
            # Display the data for EditRole
            if role == Qt.DisplayRole:
                return self.sourceModel().data(source_index, Qt.EditRole)
            elif role == Qt.EditRole:
                return self.sourceModel().data(source_index, Qt.EditRole)
            elif role == Qt.ToolTipRole:
                return self.sourceModel().data(source_index, Qt.ToolTipRole)
        
        elif column == 2:
            # Display the data for ToolTipRole
            if role == Qt.DisplayRole:
                return self.sourceModel().data(source_index, Qt.ToolTipRole)
            elif role == Qt.EditRole:
                return self.sourceModel().data(source_index, Qt.EditRole)
            elif role == Qt.ToolTipRole:
                return self.sourceModel().data(source_index, Qt.ToolTipRole)
        
        return None


# Example usage
if __name__ == "__main__":
    app = QApplication([])

    # Example data with each row having (Display, Edit, Tooltip)

    
    # Create the source model
    list_model = ListModel()
    
    # Create the proxy model
    proxy_model = MapListToTable()
    proxy_model.setSourceModel(list_model)
    
    # Create the table view and set the proxy model
    table_view = QTableView()
    table_view.setModel(proxy_model)
    
    # Set up the UI layout
    layout = QVBoxLayout()
    layout.addWidget(table_view)
    
    # Create a simple window
    window = QWidget()
    window.setLayout(layout)
    window.setWindowTitle("List Model with Proxy Model for Table")
    window.resize(400, 300)
    window.show()
    
    app.exec_()
