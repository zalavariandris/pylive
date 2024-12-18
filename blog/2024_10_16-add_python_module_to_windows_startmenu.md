# Launch your module from the window startmenu

## create a runnable python module
At the top level of your package create a `__main__.py` file.
This is the entry pont for runnable modules.

in the _main guard_ parse the command ilne arguments if your module uses them.

then simply start your application.

Im using it within pylive to open the little applications inside that package.

for example to open a QApplication let say with a file dropped on to the
shortcut:

```python
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
	parser = argparse.ArgumentParser(description="My command-line tool.")

	# livecode subcommand
	parser.add_argument('filepath', nargs='?', help='Path to the file for livecode')

	# Parse the arguments
	args = parser.parse_args()

	# open the QApplication
	app = QApplication(sys.argv)
	window = MyApp()
	if filepath:
		window.openFile(args.filepath)
	window.show()
	sys.exit(app.exec())
		open_livescript()
```

## test the module from the terminal
in the root package directory, run in the terminal
```bash
python -m <yout_package> <path_to_file>
```

even better if using a _venv_.

```
path\to\your\venv\Scripts\python.exe -m <your_package> <path_to_file>
```
use the `pythonw.exe` if you dont need the consol window.

## create a shortcut to start your module

Create a shortcut, and simply paste the same command above.
The only ceavat is that the path to the venv python must be a full path.

---

There might be a workaround to the full path issue,
- using a .bat file,
- or calling the python.exe from the `cmd`

see: <https://superuser.com/questions/644407/using-relative-paths-for-windows-shortcuts>