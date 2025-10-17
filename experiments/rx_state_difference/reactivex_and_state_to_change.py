from typing import *

from PySide6.QtCore import *
from PySide6.QtWidgets import *
import reactivex as rx
from reactivex import operators as ops
from pylive.utils.diff import diff_dict, diff_list
from pylive.utils.diff import diff_set
from bidict import bidict
def uuid(length=6):
    import random, string
    return ''.join(random.choices(string.ascii_uppercase, k=length))


if __name__ == "__main__":
    model = rx.subject.BehaviorSubject(set())
    model.subscribe(print)

    selection=None
    def select(item:str):
        global selection
        selection = item

    def add_item(item:str):
        model.on_next(model.value | {item})
        return item

    def remove_item(item:str):
        model.on_next({_ for _ in model.value if _ != item})


    app = QApplication()

    window = QWidget()
    layout = QVBoxLayout()
    window.setLayout(layout)

    song_list = QListWidget()
    editors:dict[str, QListWidgetItem] = {}
    def update_list_widget(change):
        print(change)
        for song in change.removed:
            editor = editors[song]
            row = song_list.indexFromItem(editor).row()
            song_list.takeItem(row)
            del editors[song]

        for song in change.added:
            editor = QListWidgetItem(f"{song}")
            song_id = f"{song}"
            editor.setData(Qt.ItemDataRole.UserRole, song_id)
            song_list.addItem(editor)
            editors[song] = editor

    song_list.currentItemChanged.connect(lambda current, prev: select(current.data(Qt.ItemDataRole.UserRole)))

    # Subscribe to pairwise changes in the model
    model.pipe(
        ops.pairwise(), 
        ops.map(lambda pair: diff_set(*pair)
    )).subscribe(update_list_widget)

    add_btn = QPushButton("+")
    add_btn.clicked.connect(lambda: select(add_item(uuid())))
    rmv_btn = QPushButton("-")
    rmv_btn.clicked.connect(lambda: remove_item(selection))
    layout.addWidget(add_btn)
    layout.addWidget(rmv_btn)
    layout.addWidget(song_list)

    print("...")

    window.show()
    app.exec()