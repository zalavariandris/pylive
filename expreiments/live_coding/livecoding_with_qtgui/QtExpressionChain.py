from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

class ExpressionChainView(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setWindowTitle("ExpressionChain")

		self.chainmodel = QStandardItemModel()
		self.chainmodel.setHorizontalHeaderLabels(["name", "expression", "result"])
		self.selectionmodel = QItemSelectionModel(self.chainmodel)

		self.chainview = QTableView()
		self.chainview.setModel(self.chainmodel)
		self.chainview.setSelectionModel(self.selectionmodel)

		self.toolbar = QToolBar()
		add_action = QAction("add", parent=self)
		self.toolbar.addAction(add_action)
		remove_action = QAction("remove", parent=self)
		self.toolbar.addAction(remove_action)


		@add_action.triggered.connect
		def add_block():
			items = [QStandardItem(text) for text in ["", "", ""]]
			self.chainmodel.appendRow(items)

		@remove_action.triggered.connect
		def remove_selected_blocks():
			# get selected indices from the selectin model
			selected_indexes = self.selectionmodel.selectedIndexes() # Get the selected indexes from the node selection model
			# collect rows
			rows_to_remove = sorted(set(index.row() for index in selected_indexes), reverse=True)

			# Remove the node rows from (starting from the last one, to avoid shifting indices)
			for row in reversed(rows_to_remove):
				self.chainmodel.removeRow(row)

			self.selectionmodel.clearSelection()

		self.setLayout(QVBoxLayout())
		self.layout().setMenuBar(self.toolbar)
		self.layout().addWidget(self.chainview)

		# evaluate on change
		def on_item_change(item:QStandardItem):
			if item.column() == 2:
				return
			else:
				self.evaluate_chain()


		self.chainmodel.rowsInserted.connect(self.evaluate_chain)
		self.chainmodel.rowsRemoved.connect(self.evaluate_chain)
		self.chainmodel.rowsMoved.connect(self.evaluate_chain)
		self.chainmodel.itemChanged.connect(on_item_change)

	def evaluate_chain(self):
		print("evaluating chain...")
		# collect chain from model
		chain = []
		for row in range(self.chainmodel.rowCount()):
			index = self.chainmodel.index(row, 0)
			name = index.data()
			expr = index.siblingAtColumn(1).data()
			chain.append( (name, expr) )\

		# evaluate chain		
		global_vars = {}
		local_vars = {}
		for lineno, (name, expr) in enumerate(chain):
			result_index = self.chainmodel.index(lineno, 2)
			if expr:
				try:
					result = eval(expr, global_vars, local_vars)
					local_vars[name] = result

					print(f"{lineno+1:3}. {expr:20.20} {result}")
					
					self.chainmodel.setData(result_index, str(result), Qt.EditRole)
				except Exception as err:
					self.chainmodel.setData(result_index, str(err), Qt.EditRole)
					print(err) # set the result to the error message



			

if __name__ == "__main__":
	import sys
	import subprocess
	app = QApplication(sys.argv)
	window = ExpressionChainView()
	window.show()
	sys.exit(app.exec())