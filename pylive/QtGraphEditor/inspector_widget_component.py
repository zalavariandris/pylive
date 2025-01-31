from typing import *

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

from PySide6.QtSvg import QSvgRenderer

### DATA ###
import sys

from dataclasses import dataclass


def svg_to_pixmap(svg_path, size=(32, 32)):
    renderer = QSvgRenderer(str(svg_path))
    pixmap = QPixmap(size[0], size[1])
    pixmap.fill(Qt.GlobalColor.transparent)  # Ensure transparency
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


class TileWidget(QWidget):
    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)

        self._avatar = QLabel("Py")
        self._heading = QLabel("Py")
        self._subheading = QLabel("Py")

        layout = QGridLayout()
        layout.addWidget(self._avatar,     0, 0, 1, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self._heading,    0, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)   
        layout.addWidget(self._subheading, 1, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)  

        self.setLayout(layout)

    def setAvatar(self, avatar:str):
        self._avatar.setText(avatar)

    def setHeading(self, heading:str):
        self._heading.setText(heading)

    def setSubheading(self, subheading:str):
        self._subheading.setText(subheading)


class InspectorWidget(QWidget):

    def __init__(self, parent:QWidget|None=None):
        super().__init__(parent=parent)

        ### HEADER AREA
        def create_heading_tile(avatar: QWidget, heading:QWidget, subheading: QWidget):
            layout = QGridLayout()
            layout.addWidget(avatar,     0, 0, 1, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(heading,    0, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)   
            layout.addWidget(subheading, 1, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)  

            tile = QWidget()
            tile.setLayout(layout)
            return tile

        avatar = QLabel("Py")
        heading = QLabel("Heading")
        subheading = QLabel("Subheading")
        header = create_heading_tile(avatar, heading, subheading)

        ### BODY
        def create_heading_tile(avatar: QWidget, heading:QWidget, subheading: QWidget):
            layout = QGridLayout()
            layout.addWidget(avatar,     0, 0, 1, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(heading,    0, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)   
            layout.addWidget(subheading, 1, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)  

            tile = QWidget()
            tile.setLayout(layout)
            return tile

        avatar = QLabel("Py")
        heading = QLabel("Heading")
        subheading = QLabel("Subheading")
        header = create_heading_tile(avatar, heading, subheading)

        # self._header = TileWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(header)
        main_layout.addWidget(body)

        self.setLayout(main_layout)


    def setHeading(self, text:str):
        ...

    def setSubheading(self, text:str):
        ...

    def setAvatart(self, text:str):
        ...

    def setBodyWidget(self, model:QAbstractItemModel):
        ...

    def setFooterText(self, text:str):
        ...


    # def setTileHeading(self):
    #     self._tile_heading.

    #     self._node : NodeItem|None = None

    #     main_layout = QVBoxLayout()
    #     self._header_label = QLabel()
    #     self._fields_form = QFormLayout()

    #     self._fields_list = QListView()

    #     menubar = QMenuBar(self)
    #     add_field_action = QAction("add field", self)
    #     add_field_action.triggered.connect(lambda: self._add_new_field())
    #     menubar.addAction(add_field_action)
    #     remove_field_action = QAction("remove field", self)
    #     remove_field_action.triggered.connect(lambda: self._remove_selected_field())
    #     menubar.addAction(remove_field_action)

    #     main_layout.setMenuBar(menubar)
    #     main_layout.addWidget(self._header_label)
    #     main_layout.addWidget(self._fields_list)
    #     # main_layout.addLayout(self._fields_form)


    #     self.setLayout(main_layout)
    
    # def setNode(self, node:NodeItem):
    #     definitions_model = node.definition.model()
    #     definition_name = definitions_model.data(node.definition, Qt.ItemDataRole.DisplayRole)
    #     self._header_label.setText(f"<h1>{node.name}</h1><p>{definition_name}</p>")
    #     self._fields_list.setModel(node.fields)
    #     self._node = node



    #     # for row in range(node.fields.rowCount()):
    #     #     index = node.fields.index(row, 0)
    #     #     name = index.data(Qt.ItemDataRole.DisplayRole)
    #     #     value = FieldsListModel.Roles.Value
    #     #     self._fields_form.addRow(name, QLabel(f"{value}"))

    # @Slot()
    # def _add_new_field(self):
    #     if not self._node:
    #         return False
    #     print("add new field")
    #     field_item = FieldItem("new field", "no value")
    #     self._node.fields.insertFieldItem(self._node.fields.rowCount(), field_item)


    # @Slot()
    # def _remove_selected_field(self):
    #     if not self._node:
    #         return False

if __name__ == "__main__":
    app = QApplication()


    
    inspector = InspectorWidget()
    main_layout = QVBoxLayout()
    main_layout.addWidget(inspector)
    window = QWidget()
    window.setLayout(main_layout)
    window.show()
    app.exec()