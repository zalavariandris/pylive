def open_livescript(filepath=None):
	from pylive.QtLiveScript import QLiveScript
	from PySide6.QtWidgets import QApplication

	import sys
	app = QApplication(sys.argv)
	window = QLiveScript()
	if filepath:
		window.openFile(filepath)
	window.show()
	sys.exit(app.exec())

if __name__ == "__main__":
	import sys
	import argparse
	parser = argparse.ArgumentParser(description="pylive command-line tool.")
	subparsers = parser.add_subparsers(dest="command", help="Available apps")

	# livecode subcommand
	livecode_parser = subparsers.add_parser('livescript', help='Run livecode app')
	livecode_parser.add_argument('filepath', nargs='?', help='Path to the file for livecode')

	# Parse the arguments
	args = parser.parse_args()
	
	# Route to the correct app
	if args.command == 'livescript':
		open_livescript(args.filepath)