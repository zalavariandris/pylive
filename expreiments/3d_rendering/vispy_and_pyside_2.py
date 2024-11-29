# -*- coding: utf-8 -*-
# vispy: testskip
# -----------------------------------------------------------------------------
# Copyright (c) Vispy Development Team. All Rights Reserved.
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
"""
This is a very simple example that demonstrates using a shared context
between two Qt widgets.
"""

# XXX THIS IS CURRENTLY BROKEN

from PySide6 import QtWidgets, QtCore  # can also use pyside
from functools import partial

from vispy.app import Timer
from vispy.scene.visuals import Text
from vispy.scene.widgets import ViewBox
from vispy.scene import SceneCanvas
from vispy import scene
from vispy.visuals.transforms import STTransform
import vispy

def on_resize(canvas, vb, event):
    vb.pos = 1, 1
    vb.size = (canvas.size[0] - 2, canvas.size[1] - 2)


class Window(QtWidgets.QWidget):
    def __init__(self):
        super(Window, self).__init__()
        layout = QtWidgets.QBoxLayout(QtWidgets.QBoxLayout.LeftToRight, self)
        self.resize(500, 200)
        self.setLayout(layout)

        canvas = vispy.app.Canvas(keys='interactive')

        @canvas.connect
        def on_draw(event):
            vispy.gloo.set_clear_color((0.2, 0.4, 0.6, 1.0))
            vispy.gloo.clear()

        layout.addWidget(canvas.native)


if __name__ == '__main__':
    qt_app = QtWidgets.QApplication([])
    window = Window()
    window.show()
    qt_app.exec()