from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

from vispy.scene import SceneCanvas
import math
import vispy
vispy.use('PySide6')

class Canvas(vispy.app.Canvas):
    def __init__(self, *args, **kwargs):
        vispy.app.Canvas.__init__(self, *args, **kwargs)
        self._timer = vispy.app.Timer('auto', connect=self.on_timer, start=True)
        self.tick = 0

    def on_draw(self, event):
        vispy.gloo.clear(color=True)

    def on_timer(self, event):
        self.tick += 1 / 60.0
        c = abs(math.sin(self.tick))
        vispy.gloo.set_clear_color((c, c, c, 1))
        self.update()

class Window(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        mainLayout = QVBoxLayout()
        canvas = Canvas(keys='interactive', always_on_top=True)

        mainLayout.addWidget(canvas.native)
        self.setLayout(mainLayout)

if __name__ == '__main__':
    appQt = QApplication([])
    window = Window()
    window.show()
    appQt.exec()