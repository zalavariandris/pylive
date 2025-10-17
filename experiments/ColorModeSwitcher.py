import sys
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

# List of QPalette color roles and their names
# docs: https://doc.qt.io/qt-6/qpalette.html#details
color_roles = {
	# central roles
	"Window": QPalette.ColorRole.Window,
	"WindowText": QPalette.ColorRole.WindowText,
	"Base": QPalette.ColorRole.Base,
	"AlternateBase": QPalette.ColorRole.AlternateBase,
	"ToolTipBase": QPalette.ColorRole.ToolTipBase,
	"ToolTipText": QPalette.ColorRole.ToolTipText,
	"PlaceholderText": QPalette.ColorRole.PlaceholderText,
	"Text": QPalette.ColorRole.Text,
	"Button": QPalette.ColorRole.Button,
	"ButtonText": QPalette.ColorRole.ButtonText,
	"BrightText": QPalette.ColorRole.BrightText,
	

	# bevel and shadow effects
	"Light": QPalette.ColorRole.Light,
	"Midlight": QPalette.ColorRole.Midlight,
	"Dark": QPalette.ColorRole.Dark,
	"Mid": QPalette.ColorRole.Mid,
	"Shadow": QPalette.ColorRole.Shadow,

	# selected, marked
	"Highlight": QPalette.ColorRole.Highlight,
	"Accent": QPalette.ColorRole.Accent,
	"HighlightedText": QPalette.ColorRole.HighlightedText
}

# Iterate over active, inactive, and disabled states
color_groups = {
	"Active": QPalette.ColorGroup.Active,
	"Inactive": QPalette.ColorGroup.Inactive,
	"Disabled": QPalette.ColorGroup.Disabled
}

dark_color_scheme = {
    "Active": {
        "Window": "rgba(30, 30, 30, 255)",
        "WindowText": "rgba(255, 255, 255, 255)",
        "Base": "rgba(45, 45, 45, 255)",
        "AlternateBase": "rgba(0, 26, 104, 255)",
        "ToolTipBase": "rgba(60, 60, 60, 255)",
        "ToolTipText": "rgba(212, 212, 212, 255)",
        "PlaceholderText": "rgba(255, 255, 255, 128)",
        "Text": "rgba(255, 255, 255, 255)",
        "Button": "rgba(60, 60, 60, 255)",
        "ButtonText": "rgba(255, 255, 255, 255)",
        "BrightText": "rgba(153, 235, 255, 255)",
        "Light": "rgba(120, 120, 120, 255)",
        "Midlight": "rgba(90, 90, 90, 255)",
        "Dark": "rgba(30, 30, 30, 255)",
        "Mid": "rgba(40, 40, 40, 255)",
        "Shadow": "rgba(0, 0, 0, 255)",
        "Highlight": "rgba(0, 120, 212, 255)",
        "Accent": "rgba(0, 120, 212, 255)",
        "HighlightedText": "rgba(255, 255, 255, 255)"
    },
    "Inactive": {
        "Window": "rgba(30, 30, 30, 255)",
        "WindowText": "rgba(255, 255, 255, 255)",
        "Base": "rgba(45, 45, 45, 255)",
        "AlternateBase": "rgba(0, 26, 104, 255)",
        "ToolTipBase": "rgba(60, 60, 60, 255)",
        "ToolTipText": "rgba(212, 212, 212, 255)",
        "PlaceholderText": "rgba(255, 255, 255, 128)",
        "Text": "rgba(255, 255, 255, 255)",
        "Button": "rgba(60, 60, 60, 255)",
        "ButtonText": "rgba(255, 255, 255, 255)",
        "BrightText": "rgba(153, 235, 255, 255)",
        "Light": "rgba(120, 120, 120, 255)",
        "Midlight": "rgba(90, 90, 90, 255)",
        "Dark": "rgba(30, 30, 30, 255)",
        "Mid": "rgba(40, 40, 40, 255)",
        "Shadow": "rgba(0, 0, 0, 255)",
        "Highlight": "rgba(30, 30, 30, 255)",
        "Accent": "rgba(30, 30, 30, 255)",
        "HighlightedText": "rgba(255, 255, 255, 255)"
    },
    "Disabled": {
        "Window": "rgba(30, 30, 30, 255)",
        "WindowText": "rgba(157, 157, 157, 255)",
        "Base": "rgba(30, 30, 30, 255)",
        "AlternateBase": "rgba(52, 52, 52, 255)",
        "ToolTipBase": "rgba(255, 255, 220, 255)",
        "ToolTipText": "rgba(0, 0, 0, 255)",
        "PlaceholderText": "rgba(255, 255, 255, 128)",
        "Text": "rgba(157, 157, 157, 255)",
        "Button": "rgba(60, 60, 60, 255)",
        "ButtonText": "rgba(157, 157, 157, 255)",
        "BrightText": "rgba(153, 235, 255, 255)",
        "Light": "rgba(120, 120, 120, 255)",
        "Midlight": "rgba(90, 90, 90, 255)",
        "Dark": "rgba(30, 30, 30, 255)",
        "Mid": "rgba(40, 40, 40, 255)",
        "Shadow": "rgba(0, 0, 0, 255)",
        "Highlight": "rgba(0, 120, 212, 255)",
        "Accent": "rgba(157, 157, 157, 255)",
        "HighlightedText": "rgba(255, 255, 255, 255)"
    }
}

light_color_scheme = {
    "Active": {
        "Window": "rgba(243, 243, 243, 255)",
        "WindowText": "rgba(0, 0, 0, 228)",
        "Base": "rgba(255, 255, 255, 179)",
        "AlternateBase": "rgba(0, 0, 0, 9)",
        "ToolTipBase": "rgba(243, 243, 243, 255)",
        "ToolTipText": "rgba(0, 0, 0, 228)",
        "PlaceholderText": "rgba(0, 0, 0, 128)",
        "Text": "rgba(0, 0, 0, 228)",
        "Button": "rgba(255, 255, 255, 179)",
        "ButtonText": "rgba(0, 0, 0, 228)",
        "BrightText": "rgba(255, 255, 255, 255)",
        "Light": "rgba(255, 255, 255, 255)",
        "Midlight": "rgba(255, 255, 255, 255)",
        "Dark": "rgba(120, 120, 120, 255)",
        "Mid": "rgba(160, 160, 160, 255)",
        "Shadow": "rgba(0, 0, 0, 255)",
        "Highlight": "rgba(0, 120, 212, 255)",
        "Accent": "rgba(0, 120, 212, 255)",
        "HighlightedText": "rgba(255, 255, 255, 255)"
    },
    "Inactive": {
        "Window": "rgba(243, 243, 243, 255)",
        "WindowText": "rgba(0, 0, 0, 228)",
        "Base": "rgba(255, 255, 255, 179)",
        "AlternateBase": "rgba(0, 0, 0, 9)",
        "ToolTipBase": "rgba(243, 243, 243, 255)",
        "ToolTipText": "rgba(0, 0, 0, 228)",
        "PlaceholderText": "rgba(0, 0, 0, 128)",
        "Text": "rgba(0, 0, 0, 228)",
        "Button": "rgba(255, 255, 255, 179)",
        "ButtonText": "rgba(0, 0, 0, 228)",
        "BrightText": "rgba(255, 255, 255, 255)",
        "Light": "rgba(255, 255, 255, 255)",
        "Midlight": "rgba(255, 255, 255, 255)",
        "Dark": "rgba(120, 120, 120, 255)",
        "Mid": "rgba(160, 160, 160, 255)",
        "Shadow": "rgba(0, 0, 0, 255)",
        "Highlight": "rgba(0, 120, 212, 255)",
        "Accent": "rgba(240, 240, 240, 255)",
        "HighlightedText": "rgba(0, 0, 0, 255)"
    },
    "Disabled": {
        "Window": "rgba(243, 243, 243, 255)",
        "WindowText": "rgba(0, 0, 0, 228)",
        "Base": "rgba(255, 255, 255, 179)",
        "AlternateBase": "rgba(0, 0, 0, 9)",
        "ToolTipBase": "rgba(243, 243, 243, 255)",
        "ToolTipText": "rgba(0, 0, 0, 228)",
        "PlaceholderText": "rgba(0, 0, 0, 128)",
        "Text": "rgba(0, 0, 0, 228)",
        "Button": "rgba(255, 255, 255, 179)",
        "ButtonText": "rgba(0, 0, 0, 228)",
        "BrightText": "rgba(255, 255, 255, 255)",
        "Light": "rgba(255, 255, 255, 255)",
        "Midlight": "rgba(255, 255, 255, 255)",
        "Dark": "rgba(120, 120, 120, 255)",
        "Mid": "rgba(160, 160, 160, 255)",
        "Shadow": "rgba(0, 0, 0, 255)",
        "Highlight": "rgba(0, 120, 212, 255)",
        "Accent": "rgba(120, 120, 120, 255)",
        "HighlightedText": "rgba(255, 255, 255, 255)"
    }
}

def QPaletteFromJson(data):
	import re
	palette = QPalette()
	rgba_pattern = r"rgba\((\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3}),\s*(\d{1,3})\)"
	for color_group_name, value in data.items():
		for color_role_name, rgba_string in value.items():
			match = re.match(rgba_pattern, rgba_string)
			if match:
				red, green, blue, alpha = match.groups()
				color = QColor(int(red), int(green), int(blue), int(alpha))
				palette.setColor(color_groups[color_group_name], color_roles[color_role_name], color)
			else:
				raise ValueError("Cant decode {rgba_string} tol color!")
	return palette

def QPaletteToJson(palette)->dict:
	data = {}
	for color_group_name, color_group in color_groups.items():
		data[color_group_name] = {}
		for color_role_name, color_role in color_roles.items():
			color = palette.color(color_group, color_role)
			rgba = f"rgba{color.red(), color.green(), color.blue(), color.alpha()}"
			data[color_group_name][color_role_name] = rgba
	return palette

import re
def read_palette(path:str)->QPalette:
	json_object = {}
	with open(path, 'r') as file:
		# Reading from json file
		json_object = json.load(file)

	return QPaletteFromJson(json_object)

import json
def write_palette(palette:QPalette, path:str):
	data = QPaletteToJson(palette)
	json_string = json.dumps(data, indent=4)
	with open(path, "w") as file:
		file.write(json_string)

dark_color_palette = QPaletteFromJson(dark_color_scheme)
light_color_palette = QPaletteFromJson(light_color_scheme)

class ColorModeSwitcher(QPushButton):
	def __init__(self, parent=None):
		super().__init__(icon=QIcon(), text="🌙", parent=parent)
		self.setCheckable(True)
		self.clicked.connect(self.toggleColorMode)

	def toggleColorMode(self):
		if self.isChecked():
			dark_color_palette = QPaletteFromJson(dark_color_scheme) # read_palette("system_dark_color_scheme.json")
			self.setText("🔆")
			QGuiApplication.setPalette(dark_color_palette)
		else:
			light_color_palette = QPaletteFromJson(light_color_scheme) # read_palette("system_light_color_scheme.json")
			self.setText("🌙")
			QGuiApplication.setPalette(light_color_palette)

class PaletteViewer(QWidget):
	def __init__(self, palette, parent=None):
		super().__init__(parent=parent)

		self.setWindowTitle("QGuiApplication Palette Colors")
		self.setLayout(QHBoxLayout())
		self.color_scheme_toggle = ColorModeSwitcher()

		self.layout().addWidget(self.color_scheme_toggle)

		# Create a section for each state
		for color_group_name, color_group in color_groups.items():
			# create column
			column = QWidget()
			layout = QVBoxLayout()
			column.setLayout(layout)
			# add header
			color_group_label = QLabel(f"{color_group_name}")
			color_group_label.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
			column.layout().addWidget(color_group_label)
			self.layout().addWidget(column)

			# add color swatches
			for color_role_name, color_role in color_roles.items():
				color = palette.color(color_group, color_role)
				layout.addLayout(self.create_color_display(color_role_name, color))


	def create_color_display(self, color_role_name, color):
		"""
		Creates a layout with a colored rectangle and a label showing the color role name.
		"""
		h_layout = QHBoxLayout()
		# Create label to display color role name
		label = QLabel(color_role_name)
		label.setFixedWidth(120)
		label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

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
	palette = QGuiApplication.palette()
	# write(palette, "system_dark_color_scheme.json")
	# palette = read("system_dark_color_scheme.json")
	print(palette.color(QPalette.ColorRole.Window))
	QGuiApplication.setPalette(palette)

	viewer = PaletteViewer(palette)
	viewer.show()

	sys.exit(app.exec())
