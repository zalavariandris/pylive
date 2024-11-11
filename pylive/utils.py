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

def group_consecutive_numbers(data):
	from itertools import groupby
	from operator import itemgetter

	ranges =[]

	for k,g in groupby(enumerate(data),lambda x:x[0]-x[1]):
		group = (map(itemgetter(1),g))
		group = list(map(int,group))
		ranges.append((group[0],group[-1]))
	return ranges