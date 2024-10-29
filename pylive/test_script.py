from datetime import datetime
from pylive.LiveScript import display
from textwrap import dedent

print("\033c")

str = dedent("""\
		hello
		bumbum
""")

from textwrap import dedent, indent

def toggle_comment(txt):
	original_lines = txt.split("\n")
	original_first_line = original_lines[0]
	txt = dedent(txt)
	lines = txt.split("\n")
	first_line = lines[0]
	common_indent = original_first_line[:-len(first_line)]
	lines_with_comment = [f"#{line}" for line in txt.split("\n")]
	txt = "\n".join(lines_with_comment)
	txt = indent(txt, common_indent)
	

	return txt

commented = toggle_comment(str)
print(commented)