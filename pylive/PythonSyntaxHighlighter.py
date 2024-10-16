from PySide6.QtGui import QColor, QFont, QTextCharFormat
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


# Updated color scheme for all Python components (based on VSCode's default theme)
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
}

class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the Python language, now matching VSCode default colors."""
    
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
        rules += [(r'\b%s\b' % b, 0, STYLES['builtin'])
                  for b in PythonSyntaxHighlighter.builtins]
        rules += [(r'%s' % o, 0, STYLES['operator'])
                  for o in PythonSyntaxHighlighter.operators]
        rules += [(r'%s' % b, 0, STYLES['brace'])
                  for b in PythonSyntaxHighlighter.braces]

        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),

            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

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
        ]

        # Build a QRegularExpression for each pattern
        self.rules = [(QRegularExpression(pat), index, fmt) for (pat, index, fmt) in rules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text."""
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
        """Do highlighting of multi-line strings."""
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        else:
            match = delimiter.match(text)
            start = match.capturedStart()
            add = match.capturedLength()

        while start >= 0:
            match = delimiter.match(text, start + add)
            end = match.capturedStart()
            if end >= add:
                length = end - start + add + match.capturedLength()
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            self.setFormat(start, length, style)
            match = delimiter.match(text, start + length)
            start = match.capturedStart()

        return self.currentBlockState() == in_state
