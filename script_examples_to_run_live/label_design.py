#%% setup
from PySide6.QtWidgets import *
from pylive.QtLiveApp import display

#%% update
print(f"Print this {29} to the console!")
lbl = QLabel("Hello My Label")
lbl.setStyleSheet("""
    padding: 10px;
    border-radius: 10px;
    background-color: palette(highlight);
    background-color: rgba(141,122,178,154);
""")
lbl.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
display(lbl)
