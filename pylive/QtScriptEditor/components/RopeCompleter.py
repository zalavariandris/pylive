from typing import *

from PySide6.QtWidgets import *
from PySide6.QtGui import *
from PySide6.QtCore import *

from rope.contrib import codeassist
import rope.base.project
class RopeCompleter(QCompleter):
    def __init__(self, rope_project, document: QTextDocument, parent=None):
        super().__init__(parent=parent)
        self.rope_project = rope_project
        self.document = document
        self.proposals_model = QStringListModel([], parent=self)  # Model for proposals
        self.setModel(self.proposals_model)

    def setCompletionPrefix(self, prefix: str) -> None:
        # Retrieve the entire source code from the document
        source_code = self.document.toPlainText()
        

        # Ensure the prefix is valid
        # if not source_code[offset-len(prefix):offset] == prefix:
        #     raise IndexError("Document does not match the provided prefix")
        offset = len(prefix)
        print("offset", offset)

        # Get proposals from Rope
        proposals = codeassist.code_assist(self.rope_project, source_code=source_code, offset=offset)
        proposals = codeassist.sorted_proposals(proposals)  # Sorting proposals

        # Debugging: Show proposals in the console
        # print("Proposals:")
        # for proposal in proposals:
        #     print("-", proposal)

        # Update the model of the QCompleter
        self.proposals_model.setStringList([str(proposal.name) for proposal in proposals])
        super().setCompletionPrefix("")