# TODO embe qtconsol

from ast import MatchSingleton, iter_child_nodes
from typing import *
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

from pylive.live_preview_widgets.file_textdocument_link import FileTextDocumentLink
from pylive.QtScriptEditor.components.pygments_syntax_highlighter import PygmentsSyntaxHighlighter
from pathlib import Path
import ast

import traceback
class ExceptionLabel(QLabel):
	def __init__(self, err:Exception, parent=None):
		super().__init__(parent=parent)

		self.setAutoFillBackground(True)

		self.setStyleSheet("""\
			padding: 0 2;
			border-radius: 3;
			background-color: {level_color};
			margin: 0;
			color: rgba(255,255,255,220);
		""".format(level_color='rgba(200,0,0,100)'))
		self.setWindowOpacity(0.5)

		if isinstance(err, SyntaxError):
			self.setText( str(err) )
		else:
			tb = traceback.TracebackException.from_exception(err)
			last_frame = tb.stack[-1]
			formatted_traceback = ''.join(tb.format())
			self.setText(formatted_traceback)

		self.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)

class LivePreview_QWidget(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setWindowTitle("LivePreview - QWidget")
		self.filepath = None
		""" """
		self._config = dict()

		textedit = QPlainTextEdit()
		font = textedit.font()
		font.setFamilies(["monospace", "Operator Mono Book"])
		# font.setPointSize(10)
		font.setWeight(QFont.Weight.Medium)
		font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
		textedit.setFont(font)
		### TextEdit Behaviour ###
		textedit.setWordWrapMode(QTextOption.WrapMode.NoWrap)
		self.highlighter = PygmentsSyntaxHighlighter(textedit.document())

		textedit.setTabStopDistance(textedit.fontMetrics().horizontalAdvance(" ")*4)
		textedit.setReadOnly(True)
		mainLayout = QVBoxLayout()
		mainLayout.setContentsMargins(0,0,0,0)
		self.setLayout(mainLayout)
		splitter = QSplitter()
		splitter.addWidget(textedit)
		mainLayout.addWidget(splitter)

		self.preview_pane = QWidget()
		self.preview_pane.setLayout(QVBoxLayout())

		# Create QComboBox (Dropdown)
		self.widget_list = QStringListModel([])

		splitter.addWidget(self.preview_pane)
		splitter.setSizes([splitter.width()//splitter.count() for i in range(splitter.count())])
		mainLayout.addWidget(splitter)

		self.document:QTextDocument = textedit.document()
		self.watcher = QFileSystemWatcher()
		self.watcher.fileChanged.connect(lambda:
			self.fileChangedEvent())

		self._filepath:Path|None=None

		self.document.contentsChanged.connect(lambda: (
			self.updateWidgetsPreviews()
		))

	def setFilePath(self, filePath:str|Path):
		if path:=self.filePath():
			self.watcher.removePath(str(path)) 

		if filePath:
			self.watcher.addPath(str(filePath))
		self._filepath = Path(filePath)
		self.fileChangedEvent()

	def filePath(self)->Path|None:
		return self._filepath


	def updateWidgetsPreviews(self):
		code = self.document.toPlainText()
		ctx = {'__builtins__': __builtins__}

		def clearWidgetPreviews():
			# clear layout
			while self.preview_pane.layout().count()>0:
				item = self.preview_pane.layout().takeAt(0)
				if widget:=item.widget():
					widget.deleteLater()

		def showException(exc):
			clearWidgetPreviews()
			placeholder = ExceptionLabel(err)
			placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
			self.preview_pane.layout().addWidget(placeholder)

		
		# update widget list on document change
		source = self.document.toPlainText()
		filepath = str( self.filePath() )

		try:
			tree = ast.iter_child_nodes(ast.parse(code, filepath))
		except SyntaxError as err:
			showException(err)
			return
		except Exception as err:
			showException(err)
			return

		try:
			code = compile(source, filepath, mode="exec")
		except Exception as err:
			showException(err)
			return

		try:
			exec(code, ctx)
		except Exception as err:
			showException(err)
			return

		# collect widget classes from file (and only from this file)
		widget_classes = []
		for node in tree:
			if isinstance(node, ast.ClassDef):
				print(ctx[node.name])
				if issubclass(ctx[node.name], QWidget):
					widget_classes.append(ctx[node.name])

		clearWidgetPreviews()

		for widget_class in widget_classes:
			self.preview_pane.layout().addWidget(widget_class())
		
		if self.preview_pane.layout().count() == 0:
			placeholder = QLabel("[preview area]")
			placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
			self.preview_pane.layout().addWidget(placeholder)


	def fileChangedEvent(self):
		if self.filePath():
			with open(str(self.filePath()), 'r') as file:
				data = file.read()
				self.document.setPlainText(data)
				self.document.setModified(False)
		else:
			self.document.setPlainText("")
			self.document.setModified(False)

	def sizeHint(self) -> QSize:
		return QSize(720,500)


if __name__ == "__main__":
	import sys
	app = QApplication(sys.argv)
	window = LivePreview_QWidget()
	window.setFilePath("C:/dev/src/pylive/assets/livepreview_qwidget_example_script.py")
	window.show()
	sys.exit(app.exec())
