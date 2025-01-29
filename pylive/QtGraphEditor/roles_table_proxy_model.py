
class FieldsProxyTableModel(QAbstractTableModel):
    def __init__(self, source_model, parent=None):
        super().__init__(parent)
        self.source_model = source_model  # Set the original model as the source

    def rowCount(self, parent=None):
        return self.source_model.rowCount(parent)

    def columnCount(self, parent=None):
        return 2  # Two columns: Name and Value

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        # Get the underlying field item from the source model
        field = self.source_model._fields[index.row()]

        # Return data based on the column
        if index.column() == 0:  # First column: Name
            if role == Qt.ItemDataRole.DisplayRole:
                return field.name
        elif index.column() == 1:  # Second column: Value
            if role == Qt.ItemDataRole.DisplayRole:
                return field.value

        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False

        # Get the underlying field item from the source model
        field = self.source_model._fields[index.row()]

        # Ensure only the "value" column is editable
        if index.column() == 1:  # Second column: Value
            field.value = value  # Update the value in the source model

            # Emit the dataChanged signal to notify the view about the update
            self.dataChanged.emit(index, index, [role])
            return True

        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        flags = self.source_model.flags(index)

        # Allow editing only for the "value" column
        if index.column() == 1:  # Second column: Value
            flags |= Qt.ItemFlag.ItemIsEditable

        return flags
