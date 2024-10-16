from PySide6.QtWidgets import QApplication
def getWidgetByName(name:str):

	app = QApplication.instance()
	if not app:
		raise Exception("No QApplication instance!")

	# find widget
	for widget in QApplication.allWidgets():
		if widget.objectName() == name:
			return widget
	return None