from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

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
			print("codeassist:", err)