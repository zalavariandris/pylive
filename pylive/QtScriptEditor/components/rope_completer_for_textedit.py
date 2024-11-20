from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from typing import *

from pylive.QtScriptEditor.components.completer_for_textedit import WordCompleter

import rope.base.project
from rope.base import libutils
import rope.base.project
from rope.contrib import codeassist

class RopeAssistStringModel(QStringListModel):
	def __init__(self, project, parent=None):
		super().__init__(parent=parent)
		self.rope_project = project

	def starting_offset(self, source_code:str, offset:int):
		return codeassist.starting_offset(source_code, offset)

	def updateProposals(self, source_code:str, offset:int):
		"""update proposals based on current offset"""
		if offset > len(source_code):
			raise IndexError(f"Offset {offset} is greater than text length {len(source_code)}")

		try:
			# fetch proposal
			proposals = codeassist.code_assist(self.rope_project, source_code=source_code, offset=offset)
			proposals = codeassist.sorted_proposals(proposals) # Sorting proposals; for changing the order see pydoc

			# update proposals
			self.setStringList([proposal.name for proposal in proposals])
		except Exception as err:
			self.setStringList([])

class RopeCompleter(WordCompleter):
	def __init__(self, textedit:QTextEdit, project:rope.base.project.Project):
		super().__init__(textedit)
		self.rope_project = project
		self.rope_assist_model = RopeAssistStringModel(self.rope_project)
		self.setModel(self.rope_assist_model)

	@override
	def updateCompletionList(self):
		self.rope_assist_model.updateProposals(
			self.text_edit.toPlainText(), 
			self.text_edit.textCursor().position()
		)




if __name__ == "__main__":
	#create app
	app = QApplication([])

	# create completing editor
	editor = QTextEdit()
	rope_project = rope.base.project.Project('.')
	completer = RopeCompleter(editor, rope_project)
	editor.setWindowTitle("QTextEdit with Custom Completer")
	editor.resize(600, 400)

	# placeholder
	words = [completer.model().index(row,0).data() for row in range(completer.model().rowCount())]
	editor.setPlaceholderText("Start typing...\n\neg.: " + ", ".join(words))
	
	# show window
	editor.show()

	#run app
	app.exec()