import sys
import pyglet
#from PyQt5 import QtGui
#from PyQt5 import QtCore, QtWidgets
#from PyQt5.QtOpenGL import QGLWidget as OpenGLWidget
from PySide6 import QtGui
from PySide6 import QtCore, QtWidgets
from PySide6.QtOpenGLWidgets import QOpenGLWidget as OpenGLWidget
from pyglet.gl import glClear, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT
import random


"""An example showing how to use pyglet in QT, utilizing the OGLWidget.

   Since this relies on the QT Window, any events called on Pyglet Window
   will NOT be called.
    
   This includes mouse, keyboard, tablet, and anything else relating to the Window
   itself. These must be handled by QT itself.
   
   This just allows user to create and use pyglet related things such as sprites, shapes,
   batches, clock scheduling, sound, etc.           
"""

class MainWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.setWindowTitle("Pyglet and QT Example")
        self.shapes = []

        width, height = 640, 480
        self.opengl = PygletWidget(width, height)
        self.sprite_button = QtWidgets.QPushButton('Create Rectangle', self)
        self.sprite_button.clicked.connect(self.create_sprite_click)

        self.clear_sprite_button = QtWidgets.QPushButton('Clear Shapes', self)
        self.clear_sprite_button.clicked.connect(self.clear_sprite_click)
        
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addWidget(self.opengl)
        mainLayout.addWidget(self.sprite_button)
        mainLayout.addWidget(self.clear_sprite_button)
        self.setLayout(mainLayout)

    def create_sprite_click(self):
        gl_width, gl_height = self.opengl.size().width(), self.opengl.size().height()
        
        width = random.randint(50, 100)
        height = random.randint(50, 100)
        
        x = random.randint(0, gl_width-width)
        y = random.randint(0, gl_height-height)
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        shape = pyglet.shapes.Rectangle(x, y, width, height, color=color, batch=self.opengl.batch)
        shape.opacity = random.randint(100, 255)
        self.shapes.append(shape)
        
    def clear_sprite_click(self):
        for shape in self.shapes:
            shape.delete()
            
        self.shapes.clear()


class PygletWidget(OpenGLWidget):
    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.setMinimumSize(width, height)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._pyglet_update)
        self.timer.setInterval(0)
        self.timer.start()

    def _pyglet_update(self):
        # Tick the pyglet clock, so scheduled events can work.
        pyglet.clock.tick()  
        
        # Force widget to update, otherwise paintGL will not be called.
        self.update()  # self.updateGL() for pyqt5

    def paintGL(self):
        """Pyglet equivalent of on_draw event for window"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        self.batch.draw()

    def initializeGL(self):
        """Call anything that needs a context to be created."""
        self.batch = pyglet.graphics.Batch()
        size = self.size()
        w, h = size.width(), size.height()
        
        self.projection = pyglet.window.Projection2D()
        self.projection.set(w, h, w, h)


if __name__ == '__main__':    
    app = QtWidgets.QApplication(sys.argv)    
    window = QtWidgets.QMainWindow()
    ui = MainWidget(window)    
    ui.show()  # Calls initializeGL. Do not do any GL stuff before this is called.
    app.exec() # exec_ in 5.