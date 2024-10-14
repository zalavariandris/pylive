import sys
from PySide6.QtGui import *
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from typing import List, Tuple
from ScriptEditor import ScriptEditor

class MiniTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    def sizeHint(self):
        width = self.verticalHeader().size().width()
        height = self.horizontalHeader().size().height()
        return QSize(134,height)


class GraphDetailsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._model = None

        policy = QSizePolicy.Minimum

        # create node details editor


        # node data editors
        self.id_label =  QLabel()
        self.name_edit = QLineEdit()
        self.posx_edit = QSpinBox()
        self.posx_edit.setRange(-9999, 9999)
        self.posy_edit = QSpinBox()
        self.posy_edit.setRange(-9999, 9999)
        self.script_editor = ScriptEditor()

        ### Inlets Table ###
        self.inlets_sheet_editor = MiniTableView()

        
        ### Outlets Table ###
        self.outlets_sheet_editor = MiniTableView()

        self.setLayout(QFormLayout())
        # self.layout().setFieldGrowthPolicy(QFormLayout.FieldsStayAtSizeHint)
        self.layout().addRow("Name:", self.name_edit)
        self.layout().addRow("Pos X:", self.posx_edit)
        self.layout().addRow("Pos Y:", self.posy_edit)
        self.layout().addRow("Inlets:", self.inlets_sheet_editor)
        self.layout().addRow("Script:", self.script_editor)

        self.mapper = QDataWidgetMapper()

        @self.script_editor.textChanged.connect
        def update_model():
            cursor = self.script_editor.textCursor()
            self.mapper.submit()
            self.script_editor.setTextCursor(cursor)

        # self.setLayout(QVBoxLayout())
        # self.layout().addWidget(self.id_label)
        # self.layout().addWidget(self.name_edit)
        # self.layout().addWidget(self.posx_edit)
        # self.layout().addWidget(self.posy_edit)
        # self.layout().addWidget(self.inlets_sheet_editor)
        # self.layout().addWidget(self.outlets_sheet_editor)


    def model(self):
        return self._model

    def setModel(self, graphmodel):
        self._model = graphmodel

        # mapper
        
        self.mapper.setModel(graphmodel.nodes)
        self.mapper.addMapping(self.id_label, 0)
        self.mapper.addMapping(self.name_edit, 1)
        self.mapper.addMapping(self.posx_edit, 2)
        self.mapper.addMapping(self.posy_edit, 3)
        self.mapper.addMapping(self.script_editor, 4)

        self.mapper.setSubmitPolicy(QDataWidgetMapper.AutoSubmit)

        # inlets list
        self.selected_node_inlets = QSortFilterProxyModel()  # Node column is 1 (for node name)
        self.selected_node_inlets.setSourceModel(graphmodel.inlets)
        self.inlets_sheet_editor.setModel(self.selected_node_inlets)
        self.selected_node_inlets.setFilterKeyColumn(1)

        # outlets list
        self.selected_node_outlets = QSortFilterProxyModel()  # Node column is 1 (for node name)
        self.selected_node_outlets.setSourceModel(graphmodel.outlets)
        self.outlets_sheet_editor.setModel(self.selected_node_outlets)
        self.selected_node_outlets.setFilterKeyColumn(1)

        # set no rows
        self.setCurrentModelIndex(QModelIndex())
        
    def setCurrentModelIndex(self, index):
        if index.isValid():
            self.mapper.setCurrentModelIndex(index)  # Update the mapper's current index
            node_name = self._model.nodes.itemFromIndex(index).text()  # Get the selected node's name
            self.selected_node_inlets.setFilterFixedString(node_name) # update inlet filters
            self.selected_node_outlets.setFilterFixedString(node_name) # update outlet filters
        else:
            # clear widgets
            self.name_edit.setText("")
            self.selected_node_inlets.setFilterFixedString("SOMETHING CMPLICATED ENOUGHT NOT TO MATC ANY NODE NAMES") # update inlet filters
            self.selected_node_outlets.setFilterFixedString("SOMETHING CMPLICATED ENOUGHT NOT TO MATC ANY NODE NAMES") # update outlet filters

        self.layout().invalidate()
