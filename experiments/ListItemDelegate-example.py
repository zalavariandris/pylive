from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *


# Custom delegate to provide a QLineEdit for editing
class MyItemDelegate(QStyledItemDelegate):
	def createEditor(self, parent, option, index):
		"""
		Create and return a custom editor widget (QLineEdit in this case).
		"""
		print(parent)
		editor = QLineEdit(parent)
		editor.setStyleSheet("background-color: lightyellow;")  # Custom styling
		return editor

	def setEditorData(self, editor, index):
		"""
		Set the editor's initial value based on the model's data for the given index.
		"""
		value = index.data(Qt.EditRole)
		if isinstance(editor, QLineEdit):
			editor.setText(value)

	def setModelData(self, editor, model, index):
		"""
		Save the editor's data back to the model when editing is complete.
		"""
		if isinstance(editor, QLineEdit):
			model.setData(index, editor.text(), Qt.EditRole)

	def updateEditorGeometry(self, editor, option, index):
		"""
		Position the editor to fit in the item rectangle.
		"""
		editor.setGeometry(option.rect)

	def paint(self, painter, option, index):
		"""
		Customizes the rendering of cells in the view.
		"""
		# Start by saving the painter state
		painter.save()

		# Draw a custom background for the selected state
		if QStyle.StateFlag.State_Selected in option.state:
			painter.fillRect(option.rect, QColor(200, 200, 255))  # Light blue

		# Retrieve the data to display
		text = index.data(Qt.DisplayRole)

		# Set custom font and text color
		font = QFont("Arial", 12, QFont.Bold if index.column() == 0 else QFont.Normal)
		painter.setFont(font)
		text_color = QColor(0, 100, 0) if index.column() == 0 else QColor(50, 50, 50)
		painter.setPen(text_color)

		# Draw the text, centered vertically
		painter.drawText(option.rect, Qt.AlignVCenter | Qt.AlignLeft, text)

		# Draw a border around the cell
		painter.setPen(QColor(0, 0, 0))  # Black border
		painter.drawRect(option.rect)

		# Restore the painter state
		painter.restore()

	def sizeHint(self, option, index):
		"""
		Customize the size of the item.
		"""
		return super().sizeHint(option, index)


# Main application setup
def main():
	app = QApplication([])

	# Create the main window
	window = QWidget()
	window.setWindowTitle("PySide6 Custom Delegate Example")
	window.resize(400, 300)

	# Create a table view
	table_view = QTableView()
	table_view.setEditTriggers(QAbstractItemView.DoubleClicked)

	# Create a model and populate it with data
	model = QStandardItemModel(3, 2)
	model.setHorizontalHeaderLabels(["Column 1", "Column 2"])
	model.setItem(0, 0, model.itemFromIndex(model.index(0, 0)))
	model.setData(model.index(0, 0), "Item 1")
	model.setData(model.index(1, 0), "Item 2")
	model.setData(model.index(2, 0), "Item 3")
	model.setData(model.index(0, 1), "Value 1")
	model.setData(model.index(1, 1), "Value 2")
	model.setData(model.index(2, 1), "Value 3")

	# Set the model to the table view
	table_view.setModel(model)

	# Set a custom delegate to the table view
	delegate = MyItemDelegate()
	table_view.setItemDelegate(delegate)

	# Create a layout and add the table view
	layout = QVBoxLayout(window)
	layout.addWidget(table_view)

	# Show the main window
	window.show()

	# Start the application loop
	app.exec()


if __name__ == "__main__":
	main()
