from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from typing import *

from pylive.QtScriptEditor.components.completer_for_textedit import TextEditCompleter

import rope.base.project
from rope.base import libutils
import rope.base.project
from rope.contrib import codeassist


class RopeCompleter(TextEditCompleter):
	def __init__(self, textedit: QTextEdit, rope_project):
		super().__init__(textedit)
		self.rope_project = rope_project

	@override
	def requestCompletions(self):
		source_code = self.text_edit.toPlainText()
		offset = self.text_edit.textCursor().position()

		proposals = codeassist.code_assist(
			self.rope_project, 
			source_code=source_code, 
			offset=offset
		)
		proposals = codeassist.sorted_proposals(proposals) # Sorting proposals; for changing the order see pydoc
		starting_offset = codeassist.starting_offset(source_code, offset)

		# update proposals
		string_list_model = cast(QStringListModel, self.model())
		string_list_model.setStringList([proposal.name for proposal in proposals])

	@override
	def insertCompletion(self, completion):
		"""
		Inserts the selected completion into the text at the cursor position.
		"""
		tc = self.text_edit.textCursor()
		tc.select(QTextCursor.SelectionType.WordUnderCursor)
		extra = len(completion) - len(tc.selectedText())
		tc.movePosition(QTextCursor.MoveOperation.Left)
		tc.movePosition(QTextCursor.MoveOperation.EndOfWord)
		tc.insertText(completion[-extra:])
		self.text_edit.setTextCursor(tc)


if __name__ == "__main__":
	#create app
	app = QApplication([])

	# create completing editor
	editor = QTextEdit()
	rope_project = rope.base.project.Project('.')
	completer = RopeCompleter(editor, rope_project)
	editor.setWindowTitle("QTextEdit with a non-blocking Rope Assist Completer")
	editor.resize(600, 400)

	# placeholder
	words = [completer.model().index(row,0).data() for row in range(completer.model().rowCount())]
	editor.setPlaceholderText("Start typing...\n\neg.: " + ", ".join(words))
	
	# show window
	editor.show()

	#run app
	app.exec()