class OpenGLTextureItem(QGraphicsItem):
    def __init__(self, texture_id, texture_size):
        super().__init__()
        self._texture_id = texture_id
        self._texture_size = texture_size

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._texture_size.width(), self._texture_size.height())
    
    def setTexture(self, texture_id: int, texture_size: QSize):
        """Set the OpenGL texture ID and size."""
        self._texture_id = texture_id
        self._texture_size = texture_size
        self.update()

    def paint(self, painter: QPainter, option, widget=None):
        if not QOpenGLContext.currentContext():
            return

        painter.beginNativePainting()

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self._texture_id)

        glBegin(GL_QUADS)
        glTexCoord2f(0, 1); glVertex2f(0, 0)
        glTexCoord2f(1, 1); glVertex2f(self._texture_size.width(), 0)
        glTexCoord2f(1, 0); glVertex2f(self._texture_size.width(), self._texture_size.height())
        glTexCoord2f(0, 0); glVertex2f(0, self._texture_size.height())
        glEnd()

        glBindTexture(GL_TEXTURE_2D, 0)
        glDisable(GL_TEXTURE_2D)

        painter.endNativePainting()

