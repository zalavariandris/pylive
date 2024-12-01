from typing import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class CloseToolbarButton(QToolButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hovered = False  # Flag to track hover state
        self.setFixedSize(50, 20)

    def enterEvent(self, event):
        self.hovered = True  # Set hover state to True
        self.update()        # Trigger a repaint
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False  # Set hover state to False
        self.update()         # Trigger a repaint
        super().leaveEvent(event)

    def paintEvent(self, event: QPaintEvent):
        # Call the base class paintEvent
        # super().paintEvent(event)

        # Create a QPainter object
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background on hover
        if self.hovered:
            painter.setBrush(QBrush(QColor(200, 200, 200, 150)))  # Light gray with some transparency
            painter.setPen(Qt.NoPen)  # No border for the background
            painter.drawRect(self.rect())

        # Set pen for the "X"
        pen = QPen(QColor(0, 0, 0))  # Black color
        pen.setWidth(1.5)              # Line width
        painter.setPen(pen)

        # Calculate coordinates for the "X"
        rect = self.rect()
        margin = (11,3)
        x1, y1 = rect.left() + margin[0], rect.top() + margin[1]
        x2, y2 = rect.right() - margin[0], rect.bottom() - margin[1]
        x3, y3 = rect.left() + margin[0], rect.bottom() - margin[1]
        x4, y4 = rect.right() - margin[0], rect.top() + margin[1]

        # Draw the "X"
        painter.drawLine(x1, y1, x2, y2)
        painter.drawLine(x3, y3, x4, y4)

        # End painting
        painter.end()


class MiniToolbarButton(QToolButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.hovered = False  # Flag to track hover state
        self.setFixedSize(50, 20)

    def enterEvent(self, event):
        self.hovered = True  # Set hover state to True
        self.update()        # Trigger a repaint
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hovered = False  # Set hover state to False
        self.update()         # Trigger a repaint
        super().leaveEvent(event)

    def paintEvent(self, event: QPaintEvent):
        # Call the base class paintEvent
        # super().paintEvent(event)

        # Create a QPainter object
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background on hover
        if self.hovered:
            painter.setBrush(QBrush(QColor(200, 200, 200, 150)))  # Light gray with some transparency
            painter.setPen(Qt.NoPen)  # No border for the background
            painter.drawRect(self.rect())

        # Set pen for the "X"
        pen = QPen(QColor(0, 0, 0))  # Black color
        pen.setWidth(1.5)              # Line width
        painter.setPen(pen)

        # Calculate coordinates for the "X"
        rect = self.rect()
        margin = (11,3)
        x1, y1 = rect.left() + margin[0], rect.top() + margin[1]
        x2, y2 = rect.right() - margin[0], rect.bottom() - margin[1]
        x3, y3 = rect.left() + margin[0], rect.bottom() - margin[1]
        x4, y4 = rect.right() - margin[0], rect.top() + margin[1]

        # Draw the "X"
        painter.drawLine(x1, y1, x2, y2)
        painter.drawLine(x3, y3, x4, y4)

        # End painting
        painter.end()



class CustomTitleBar(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self._mousePressPosition = None
        title_bar_layout = QHBoxLayout(self)
        title_bar_layout.setContentsMargins(1, 1, 1, 1)
        title_bar_layout.setSpacing(10)
        self.title = QLabel(f"{self.__class__.__name__}", self)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet(
        """
        QLabel { margin-left: 48px; }
        """
        )

        # Title
        if title := parent.windowTitle():
            self.title.setText(title)
        title_bar_layout.addWidget(self.title)

        # Min button
        self.min_button = QToolButton(self)
        min_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarMinButton
        )
        self.min_button.setIcon(min_icon)
        self.min_button.clicked.connect(self.window().showMinimized)

        # Max button
        self.max_button = QToolButton(self)
        max_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarMaxButton
        )
        self.max_button.setIcon(max_icon)
        self.max_button.clicked.connect(self.window().showMaximized)

        # Close button
        self.close_button = QToolButton(self)
        close_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarCloseButton
        )
        self.close_button.setIcon(close_icon)
        self.close_button.clicked.connect(self.window().close)

        # Normal button
        self.normal_button = QToolButton(self)
        normal_icon = self.style().standardIcon(
            QStyle.StandardPixmap.SP_TitleBarNormalButton
        )
        self.normal_button.setIcon(normal_icon)
        self.normal_button.clicked.connect(self.window().showNormal)
        self.normal_button.setVisible(False)
        # Add buttons
        buttons = [
            self.min_button,
            self.normal_button,
            self.max_button,
            self.close_button,
        ]
        for button in buttons:
            button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            button.setFixedSize(QSize(32, 16))
            button.setStyleSheet(
                """QToolButton {
                    border: none;
                    padding: 2px;
                }
                QToolButton:hover {
                    background-color: rgba(0, 0, 0, 40%);  /* Dark transparent background on hover */
                }
                """
            )
            title_bar_layout.addWidget(button)

        parent.installEventFilter(self)

    def window_state_changed(self, state):
        if state == Qt.WindowState.WindowMaximized:
            self.normal_button.setVisible(True)
            self.max_button.setVisible(False)
        else:
            self.normal_button.setVisible(False)
            self.max_button.setVisible(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._mousePressPosition = event.position().toPoint()
        super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(self, event):
        if self._mousePressPosition is not None:
            delta = event.position().toPoint() - self._mousePressPosition
            self.window().move(
                self.window().x() + delta.x(),
                self.window().y() + delta.y(),
            )
        super().mouseMoveEvent(event)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._mousePressPosition = None
        super().mouseReleaseEvent(event)
        event.accept()


class WindowUnifiedTitlebar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowFlags(Qt.WindowType.CustomizeWindowHint)
        mainLayout = QVBoxLayout()
        mainLayout.setContentsMargins(0,0,0,0)
        self.setLayout(mainLayout)
        titlebar = CustomTitleBar(self)
        titlebar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        mainLayout.addWidget(titlebar)
        self._titlebar = titlebar
        mainLayout.addStretch()
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setWindowTitle("Title")

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            self._titlebar.window_state_changed(self.windowState())
        super().changeEvent(event)
        event.accept()

    def sizeHint(self) -> QSize:
        return QSize(640,505)

    def setWindowTitle(self, title:str):
        super().setWindowTitle(title)
        self._titlebar.title.setText(title)


if __name__ == "__main__":
    app = QApplication([])
    window = WindowUnifiedTitlebar()
    window.setStyleSheet("WindowUnifiedTitlebar{background: qlineargradient(x1:0 y1:0, x2:0 y2:1, stop:0 palette(window) stop:1 #44315f);}")
    window.show()

    # w = QWidget()
    # w.show()
    app.exec()