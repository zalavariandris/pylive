import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtGui import QGuiApplication, QPalette
from PySide6.QtCore import Qt

class PaletteViewer(QWidget):
	def __init__(self):
		super().__init__()

		self.setWindowTitle("QGuiApplication Palette Colors")
		self.setLayout(QHBoxLayout())

		# Get the application palette
		palette = QGuiApplication.palette()

		# List of QPalette color roles and their names
		color_roles = [
			(QPalette.Window, "Window"),
			(QPalette.WindowText, "WindowText"),
			(QPalette.Base, "Base"),
			(QPalette.AlternateBase, "AlternateBase"),
			(QPalette.ToolTipBase, "ToolTipBase"),
			(QPalette.ToolTipText, "ToolTipText"),
			(QPalette.Text, "Text"),
			(QPalette.Button, "Button"),
			(QPalette.ButtonText, "ButtonText"),
			(QPalette.BrightText, "BrightText"),
			(QPalette.Highlight, "Highlight"),
			(QPalette.HighlightedText, "HighlightedText"),
		]

		# Iterate over active, inactive, and disabled states
		states = [
			(QPalette.Active, "Active"),
			(QPalette.Inactive, "Inactive"),
			(QPalette.Disabled, "Disabled")
		]

		# Create a section for each state
		for state, state_name in states:
			column = QWidget()
			column.setLayout(QVBoxLayout())
			state_label = QLabel(f"{state_name} State")
			column.layout().addWidget(state_label)

			for role, role_name in color_roles:
				color = palette.color(state, role)
				column.layout().addLayout(self.create_color_display(role_name, color))
			self.layout().addWidget(column)

	def create_color_display(self, role_name, color):
		"""
		Creates a layout with a colored rectangle and a label showing the color role name.
		"""
		h_layout = QHBoxLayout()

		# Create label to display color role name
		label = QLabel(role_name)
		label.setFixedWidth(150)

		# Create color rectangle
		color_label = QLabel()
		color_label.setFixedSize(100, 30)
		color_label.setStyleSheet(f"background-color: {color.name()}; border: 1px solid black;")

		h_layout.addWidget(label)
		h_layout.addWidget(color_label)
		h_layout.addStretch()

		return h_layout

if __name__ == "__main__":
	app = QApplication(sys.argv)
	viewer = PaletteViewer()
	viewer.show()
	sys.exit(app.exec())
