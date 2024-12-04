from typing import *

import re



def split_cells(script:str)->List[str]:
	"""
	returns a dict where the key is the first line,
	and the value si the cell content
	"""
	cell_pattern = r"#\s*%%" # Define a regex pattern to match the cell markers (`# %%`)
	
	cells = [[]]
	Scope="TEXT"
	for lineno, line in enumerate(script.split("\n")):
		if line:
			code = line.split("#")[-1]
			CodeHasDocstring = code.count('"""')%2==1 or code.count("'''")%2==1
			CodeIsEmpty = False if len(line)>0 else True
			CodeIsComment= line.lstrip() and line.lstrip()[0] == "#"
			CodeIsHeading = re.match(cell_pattern, line.lstrip())

			if not CodeIsEmpty:
				if Scope == "TEXT":
					if CodeIsHeading and lineno!=0:
						cells.append([])
					elif CodeHasDocstring:
						Scope = "DOCSTRING"
				elif Scope == "DOCSTRING":
					if CodeHasDocstring:
						Scope = "TEXT"


		cells[-1].append(line)

	return ["\n".join(cell) for cell in cells]

def cell_at_line(cells:List[str], lineno:int):
	linecount = 0
	for i, content in enumerate(cells):
		linecount+=len(content.split("\n"))
		if linecount>lineno:
			return i
	raise IndexError(f"Line number {lineno} out of range,")

if __name__ == "__main__":
	from textwrap import dedent
	from PySide6.QtCore import *
	from PySide6.QtGui import *
	from PySide6.QtWidgets import *
	from pylive.QtScriptEditor.script_edit import ScriptEdit
	app = QApplication()

	window = QWidget()
	layout = QHBoxLayout()
	window.setLayout(layout)

	editor = ScriptEdit()
	layout.addWidget(editor)

	cells_view = QPlainTextEdit()
	cells_view.setReadOnly(True)
	layout.addWidget(cells_view)

	def update_cells():
		script = editor.toPlainText()
		cells = [
			cell for cell in 
			re.split(r"(?=#.*%%.+\n)", script, flags=re.MULTILINE)
		]
		
		text = ""
		
		for i, cell in enumerate(cells):
			text+=dedent(f"""{i}.---------
			{cell}""")
		cells_view.setPlainText(text)

	editor.textChanged.connect(update_cells)

	editor.setPlainText(dedent('''\
#%% setup
from PySide6.QtWidgets import *
from pylive.QtLiveApp import display

#%% update
print(f"Print this {28} to the console!")

display("""\\
Display this *text* or any *QWidget* in the preview area.
""")'''))

	window.show()

	app.exec()