from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *

def format(color: str, style: str = '') -> QTextCharFormat:
	"""Return a QTextCharFormat with the given attributes."""
	_format = QTextCharFormat()
	_format.setForeground(QColor(color))
	if 'bold' in style:
		_format.setFontWeight(QFont.Bold)
	if 'italic' in style:
		_format.setFontItalic(True)
	return _format


# Syntax styles that can be shared by all languages
import re
def hsl_to_qcolor(hsl_string):
	# Extract values from HSL string
	match = re.match(r'hsla?\((\d+),\s*(\d+)%,\s*(\d+)%(?:,\s*([\d.]+))?\)', hsl_string)
	if match:
		h, s, l, a = match.groups()
		h, s, l = int(h), int(s), int(l)
		a = float(a) if a else 1.0
		return QColor.fromHslF(h / 360, s / 100, l / 100, a)
	else:
		raise ValueError(f"Invalid HSL string: {hsl_string}")

colors = {
	"black":        hsl_to_qcolor("hsl(0, 0%, 0%)"),
	"blue":         hsl_to_qcolor("hsl(210, 50%, 60%)"),
	"blue-vibrant": hsl_to_qcolor("hsl(210, 60%, 60%)"),
	"blue2":        hsl_to_qcolor("hsla(210, 13%, 40%, 0.7)"),
	"blue3":        hsl_to_qcolor("hsl(210, 15%, 22%)"),
	"blue4":        hsl_to_qcolor("hsl(210, 13%, 45%)"),
	"blue5":        hsl_to_qcolor("hsl(180, 36%, 54%)"),
	"blue6":        hsl_to_qcolor("hsl(221, 12%, 69%)"),
	"green":        hsl_to_qcolor("hsl(114, 31%, 68%)"),
	"grey":         hsl_to_qcolor("hsl(0, 0%, 20%)"),
	"orange":       hsl_to_qcolor("hsl(32, 93%, 66%)"),
	"orange2":      hsl_to_qcolor("hsl(32, 85%, 55%)"),
	"orange3":      hsl_to_qcolor("hsl(40, 94%, 68%)"),
	"pink":         hsl_to_qcolor("hsl(300, 30%, 68%)"),
	"red":          hsl_to_qcolor("hsl(357, 79%, 65%)"),
	"red2":         hsl_to_qcolor("hsl(13, 93%, 66%)"),
	"white":        hsl_to_qcolor("hsl(0, 0%, 100%)"),
	"white2":       hsl_to_qcolor("hsl(0, 0%, 97%)"),
	"white3":       hsl_to_qcolor("hsl(219, 28%, 88%)")
}

# Updated color scheme for Python components (based on VSCode's default theme)
STYLES = {
	'keyword': format('#569CD6', 'bold'),         # Blue for Python keywords
	'builtin': format('#4FC1FF'),                 # Light blue for built-in functions
	'self': format('#9CDCFE'),                    # Cyan for 'self'
	'defclass': format('#4EC9B0', 'bold'),        # Light blue for class and def
	'comment': format('#6A9955', 'italic'),       # Green for comments
	'string': format('#D69D85'),                  # Red/Brown for strings
	'string2': format('#D69D85'),                 # Same for multi-line strings
	'numbers': format('#B5CEA8'),                 # Orange for numbers
	'operator': format('#D4D4D4'),                # Light gray for operators
	'brace': format('#D4D4D4'),                   # Light gray for braces
	'decorator': format('#DCDCAA'),               # Orange for decorators
	'exception': format('#C586C0', 'bold'),       # Dark purple for exceptions
	'function_call': format('#DCDCAA'),           # Yellowish for function calls
	'class_name': format('#4EC9B0', 'bold'),      # Light blue for class names
	'import': format('#569CD6', 'bold'),          # Blue for import keyword
	'module': format('#9CDCFE', 'italic'),        # Cyan italic for imported modules
	'variable': format('#9CDCFE'),                # Cyan for variable assignments
}

class PythonSyntaxHighlighter(QSyntaxHighlighter):
	"""Syntax highlighter for the Python language, now matching VSCode default colors and enhanced patterns."""
	
	keywords = [
		'and', 'assert', 'async', 'await', 'break', 'class', 'continue', 'def',
		'del', 'elif', 'else', 'except', 'exec', 'finally', 'for', 'from', 'global',
		'if', 'import', 'in', 'is', 'lambda', 'not', 'or', 'pass', 'print', 'raise',
		'return', 'try', 'while', 'with', 'yield', 'None', 'True', 'False'
	]

	builtins = [
		'abs', 'all', 'any', 'bin', 'bool', 'bytearray', 'bytes', 'callable', 'chr', 
		'classmethod', 'compile', 'complex', 'delattr', 'dict', 'dir', 'divmod', 
		'enumerate', 'eval', 'filter', 'float', 'format', 'frozenset', 'getattr', 
		'globals', 'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
		'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max', 'memoryview', 
		'min', 'next', 'object', 'oct', 'open', 'ord', 'pow', 'property', 'range', 
		'repr', 'reversed', 'round', 'set', 'setattr', 'slice', 'sorted', 'staticmethod', 
		'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'
	]

	operators = [
		'=', '==', '!=', '<', '<=', '>', '>=', '\+', '-', '\*', '/', '//', '%', '\*\*',
		'\+=', '-=', '\*=', '/=', '%=', '\^', '\|', '\&', '\~', '>>', '<<'
	]

	braces = [
		'\{', '\}', '\(', '\)', '\[', '\]'
	]

	def __init__(self, parent: QTextDocument) -> None:
		super().__init__(parent)

		# Multi-line strings (expression, flag, style)
		self.tri_single = (QRegularExpression("'''"), 1, STYLES['string2'])
		self.tri_double = (QRegularExpression('"""'), 2, STYLES['string2'])

		rules = []

		# Keyword, operator, and brace rules
		rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
			for w in PythonSyntaxHighlighter.keywords]
		# rules += [(r'%s' % o, 0, STYLES['operator'])
		# 	for o in PythonSyntaxHighlighter.operators]
		# rules += [(r'%s' % b, 0, STYLES['brace'])
		# 	for b in PythonSyntaxHighlighter.braces]



		# All other rules
		rules += [
			# 'self'
			(r'\bself\b', 0, STYLES['self']),

			# 'def' followed by an identifier (class or function name)
			(r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
			(r'\bclass\b\s*(\w+)', 1, STYLES['class_name']),

			# Function calls (e.g., func_name())
			(r'(\b\w+)(?=\()', 1, STYLES['function_call']),

			# Variable assignment (e.g., var_name =)
			(r'\b(\w+)\s*(?==)', 1, STYLES['variable']),

			# Numeric literals
			(r'\b[+-]?[0-9]+[lL]?\b', 0, STYLES['numbers']),
			(r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
			(r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),

			# Double-quoted string, possibly containing escape sequences
			(r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
			# Single-quoted string, possibly containing escape sequences
			(r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

			# From '#' until a newline (comments)
			(r'#[^\n]*', 0, STYLES['comment']),

			# Decorators (e.g. @decorator)
			(r'@\w+', 0, STYLES['decorator']),

			# Exception names (e.g. "raise ValueError")
			(r'\braise\b\s*(\w+)', 1, STYLES['exception']),

			# Imports (e.g. "import module")
			(r'\bimport\b', 0, STYLES['import']),
			(r'\bfrom\b\s+(\w+)', 1, STYLES['module']),  # From-import pattern
			(r'\bimport\b\s+(\w+)', 1, STYLES['module']), # module names in import statements
		]

		# Build a QRegularExpression for each pattern
		self.rules = [(QRegularExpression(pat), index, fmt) for (pat, index, fmt) in rules]

	def highlightBlock(self, text):
		"""Apply syntax highlighting to the given block of text.
		"""
		self.tripleQuotesWithinStrings = []
		# Do other syntax formatting
		for expression, nth, format in self.rules:
			iterator = expression.globalMatch(text)
			while iterator.hasNext():
				match = iterator.next()
				index = match.capturedStart(nth)
				length = match.capturedLength(nth)
				if index >= 0 and length > 0:
					self.setFormat(index, length, format)

		self.setCurrentBlockState(0)

		# Do multi-line strings
		in_multiline = self.match_multiline(text, *self.tri_single)
		if not in_multiline:
			in_multiline = self.match_multiline(text, *self.tri_double)

	def match_multiline(self, text, delimiter, in_state, style):
		"""Do highlighting of multi-line strings. ``delimiter`` should be a
		``QRegularExpression`` for triple-single-quotes or triple-double-quotes, and
		``in_state`` should be a unique integer to represent the corresponding
		state changes when inside those strings. Returns True if we're still
		inside a multi-line string when this function is finished.
		"""
		# If inside triple-single quotes, start at 0
		if self.previousBlockState() == in_state:
			start = 0
			add = 0
		# Otherwise, look for the delimiter on this line
		else:
			match = delimiter.match(text)
			start = match.capturedStart()
			# Move past this match
			add = match.capturedLength()

		# As long as there's a delimiter match on this line...
		while start >= 0:
			# Look for the ending delimiter
			match = delimiter.match(text, start + add)
			end = match.capturedStart()
			# Ending delimiter on this line?
			if end >= add:
				length = end - start + add + match.capturedLength()
				self.setCurrentBlockState(0)
			# No; multi-line string
			else:
				self.setCurrentBlockState(in_state)
				length = len(text) - start + add
			# Apply formatting
			self.setFormat(start, length, style)
			# Look for the next match
			match = delimiter.match(text, start + length)
			start = match.capturedStart()

		# Return True if still inside a multi-line string, False otherwise
		if self.currentBlockState() == in_state:
			return True
		else:
			return False




