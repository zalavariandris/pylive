"""
Entry point for pylive command-line tool.

Usage:
	python -m pylive livescript [filepath]
	python -m pylive imsketch [filepath]
"""

def open_livescript(filepath=None):
	from pylive.QtLiveApp.live_script_with_exec import LiveAppWithExec
	from PySide6.QtWidgets import QApplication

	import sys
	app = QApplication(sys.argv)
	window = LiveAppWithExec.instance()
	if filepath:
		window.fileLink.openFile(filepath)
	window.show()
	sys.exit(app.exec())

def parse_args():
	import sys
	import argparse
	parser = argparse.ArgumentParser(description="pylive command-line tool.")
	subparsers = parser.add_subparsers(dest="command", help="Available apps")

	# livecode subcommand
	livecode_parser = subparsers.add_parser('livescript', help='Run livecode app')
	livecode_parser.add_argument('filepath', nargs='?', help='Path to the file for livecode')

	# livecode subcommand
	imsketch_parser = subparsers.add_parser('imsketch', help='Run imsketch app')
	imsketch_parser.add_argument('filepath', nargs='?', help='Path to the file for livecode')

	# Parse the arguments
	args = parser.parse_args()

	return args


if __name__ == "__main__":
	args = parse_args()

	# Route to the correct app
	if args.command == 'livescript':
		open_livescript(args.filepath)

	if args.command == 'imsketch':
		from imsketch.main_v3 import start
		start(args.filepath)