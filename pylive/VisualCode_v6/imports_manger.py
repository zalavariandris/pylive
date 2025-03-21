from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


from pylive.VisualCode_v6.py_graph_model import PyGraphModel
class ImportsManager(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)
        self.imports_list = QListWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h1>Imports manager</h1>"))
        self.new_import_edit = QLineEdit()
        layout.addWidget(self.new_import_edit)
        layout.addWidget(self.imports_list)
        self.delete_button = QPushButton("remove")
        layout.addWidget(self.delete_button)
        self.setLayout(layout)

        self._model:PyGraphModel|None = None

        self.completer = QCompleter(self.new_import_edit)
        packages = self._listAvailablePackages()
        packages_modell = QStringListModel(packages)
        self.completer.setModel(packages_modell)
        self.new_import_edit.setCompleter(self.completer)

        self._connections = []

    def setModel(self, model:PyGraphModel|None):
        if self._model:
            for signal, slot in self._connections:
                signal.disconnect(slot)
        if model:
            def appendImport(module_name):
                assert self._model
                self.new_import_edit.clear()
                current_imports = [_ for _ in self._model.imports()]
                current_imports.append(module_name)
                self._model.setImports(current_imports)

            def removeSelectedImports():
                assert self._model
                selected_packages = [item.text() for item in self.imports_list.selectedItems()]
                current_imports = self._model.imports()
                new_imports = [pkg for pkg in current_imports if pkg not in selected_packages]
                self._model.setImports(new_imports)

            self._connections = [
                (model.importsReset, self.refreshImports),
                (self.new_import_edit.returnPressed, lambda: appendImport(self.new_import_edit.text())),
                (self.delete_button.pressed, lambda: removeSelectedImports())
            ]
            for signal, slot in self._connections:
                signal.connect(slot)

        self._model = model
        self.refreshImports()

    def _listAvailablePackages(self):
        import pkgutil
        return [module.name 
            for module in pkgutil.iter_modules() 
            if not module.name.startswith("_")
        ]

    def refreshImports(self):
        assert self._model
        self.imports_list.clear()
        for row, module_name in enumerate(self._model.imports()):
            self.imports_list.insertItem(row, QListWidgetItem(module_name))


if __name__ == "__main__":
    app = QApplication([])
    window = ImportsManager()
    window.show()
    app.exec()