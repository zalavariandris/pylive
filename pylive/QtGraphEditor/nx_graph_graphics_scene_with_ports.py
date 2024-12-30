
class PinWidget(QGraphicsItem):
    def __init__(self, text:str, parent:QGraphicsItem|None=None):
        super().__init__(parent=parent)
        # store relations
        self._parent_node: NodeWidget | None = None
        self._edges:list[EdgeWidget] = []

        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)
        self.radius:float = 3.5
        self._isHighlighted:bool = False

    def destroy(self):
        for edge in reversed(self._edges):
            edge.destroy()
        self._edges = []

        if self._parent_node:
            self._parent_node.removeOutlet(self)
        self.scene().removeItem(self)

    def itemChange(self, change, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                for edge in self._edges:
                    edge.updatePosition()

        return super().itemChange(change, value)

    def shape(self):
        r = self.radius+3
        path = QPainterPath()
        path.addEllipse(QPointF(), r, r)
        return path

    def boundingRect(self) -> QRectF:
        r = self.radius+3
        return QRectF(-r, -r, r*2, r*2)

    def pen(self):
        palette = QApplication.instance().palette()
        if self.scene():
            palette = self.scene().palette()

        pen = QPen(palette.text().color())
        

        if self.isSelected() or self.parentItem().isSelected():
            pen.setColor(palette.highlight().color())  # Color for selected

        if self.isHighlighted():
            pen.setColor(palette.accent().color())  # Color for hover

        return pen

    def brush(self):
        palette = QApplication.instance().palette()
        if self.scene():
            palette = self.scene().palette()

        baseColor = palette.base().color()
        baseColor.setAlpha(255)
        brush = QBrush(baseColor)
        return brush

    def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
        # Check the item's state
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawEllipse(QPointF(0,0), self.radius, self.radius)

        # painter.drawPath(self.shape())
        # painter.drawRect(self.boundingRect())

    def setHighlighted(self, value):
        self._isHighlighted = value
        self.update()

    def isHighlighted(self):
        return self._isHighlighted

    def hoverEnterEvent(self, event):
        self.setHighlighted(True)

    def hoverLeaveEvent(self, event):
        self.setHighlighted(False)



class OutletWidget(PinWidget):
    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        event.accept()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
            return
        print("start drag event")

        # start connection
        connect = Connect(self)
        connect.exec()
        
        graphscene = cast(DAGScene, self.scene())
        if connect.target():
            edge = EdgeWidget(connect.source(), connect.target())
            graphscene.addEdge(edge)

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        return super().mouseReleaseEvent(event)

    @override
    def sceneEvent(self, event: QEvent) -> bool:
        if event.type() == ConnectionEnterType:
            self.connectionEnterEvent(cast(ConnectionEvent, event))
        elif event.type() == ConnectionLeaveType:
            self.connectionLeaveEvent(cast(ConnectionEvent, event))
        elif event.type() == ConnectionMoveType:
            self.connectionMoveEvent(cast(ConnectionEvent, event))
        elif event.type() == ConnectionDropType:
            self.connectionDropEvent(cast(ConnectionEvent, event))
        else:
            ...

        return super().sceneEvent(event)

    def connectionEnterEvent(self, event:ConnectionEvent) -> None:
        inlet = event.source()
        if inlet.parentItem()!=self.parentItem():
            event.setAccepted(True)
            self.setHighlighted(True)
            return
        event.setAccepted(False)

    def connectionLeaveEvent(self, event:ConnectionEvent)->None:
        self.setHighlighted(False)

    def connectionMoveEvent(self, event:ConnectionEvent)->None:
        ...
    
    def connectionDropEvent(self, event:ConnectionEvent):
        if event.source().parentItem()!=self.parentItem():
            self.setHighlighted(False)
            event.setAccepted(True)

        event.setAccepted(False)


class InletWidget(PinWidget):
    ...
    # def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     event.accept()

    # def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     if QLineF(event.screenPos(), event.buttonDownScreenPos(Qt.MouseButton.LeftButton)).length() < QApplication.startDragDistance():
    #         return
    #     print("start drag event")

    #     # start connection
    #     connect = Connect(self, direction='backward')
    #     connect.exec()
        
    #     graphscene = cast(DAGScene, self.scene())
    #     if connect.source():
    #         edge = EdgeWidget(connect.source(), connect.target())
    #         graphscene.addEdge(edge)

    # def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
    #     return super().mouseReleaseEvent(event)

    # @override
    # def sceneEvent(self, event: QEvent) -> bool:
    #     if event.type() == ConnectionEnterType:
    #         self.connectionEnterEvent(cast(ConnectionEvent, event))
    #     elif event.type() == ConnectionLeaveType:
    #         self.connectionLeaveEvent(cast(ConnectionEvent, event))
    #     elif event.type() == ConnectionMoveType:
    #         self.connectionMoveEvent(cast(ConnectionEvent, event))
    #     elif event.type() == ConnectionDropType:
    #         self.connectionDropEvent(cast(ConnectionEvent, event))
    #     else:
    #         ...

    #     return super().sceneEvent(event)

    # def connectionEnterEvent(self, event:ConnectionEvent) -> None:
    #     outlet = event.source()
    #     if outlet.parentItem()!=self.parentItem():
    #         event.setAccepted(True)
    #         self.setHighlighted(True)
    #         return
    #     event.setAccepted(False)

    # def connectionLeaveEvent(self, event:ConnectionEvent)->None:
    #     self.setHighlighted(False)

    # def connectionMoveEvent(self, event:ConnectionEvent)->None:
    #     ...
    
    # def connectionDropEvent(self, event:ConnectionEvent):
    #     if event.source().parentItem()!=self.parentItem():
    #         self.setHighlighted(False)
    #         event.setAccepted(True)

    #     event.setAccepted(False)


class NodeWidgetWithPorts(QGraphicsItem):
    """A widget that holds multiple TextWidgets arranged in a layout."""
    def __init__(
        self,
        title="Node",
        parent=None,
    ):
        super().__init__(parent)
        self._title = title
        # Enable selection and movement
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsWidget.GraphicsItemFlag.ItemIsFocusable, True)
        self.setFlag(
            QGraphicsItem.GraphicsItemFlag.ItemSendsScenePositionChanges
        )
        self.setAcceptHoverEvents(True)

        # Define the bounding geometry
        self._inlets:list[InletWidget] = []
        self._outlets:list[OutletWidget] = []
        self._edges:list[EdgeWidget] = []

    @override
    def sceneEventFilter(self, watched: QGraphicsItem, event: QEvent) -> bool:
        if watched in self._inlets:
            print(event)
        if watched in self._outlets:
            print(event)

        return super().sceneEventFilter(watched, event)

    @override
    def boundingRect(self) -> QRectF:
        try:
            fm = QFontMetrics( self.scene().font() )
        except AttributeError:
            fm = QFontMetrics(QApplication.instance().font())

        text_width = fm.horizontalAdvance(self._title)
        text_height = fm.height()
        return QRectF(0,0,text_width+8, text_height+4)

    def destroy(self):
        while self._inlets:
            self._inlets[0].destroy()  # Always remove first

        while self._outlets:
            self._outlets[0].destroy()  # Always remove first

        self.scene().removeItem(self)

    def itemChange(self, change, value):
        match change:
            case QGraphicsItem.GraphicsItemChange.ItemScenePositionHasChanged:
                print("update edges")
                for edge in self._edges:
                    edge.updatePosition()

            case QGraphicsItem.GraphicsItemChange.ItemSceneChange:
                if self.scene():
                    for port in self._inlets+self._outlets:
                        port.removeSceneEventFilter(self)
            case QGraphicsItem.GraphicsItemChange.ItemSceneHasChanged:
                if self.scene():
                    for port in self._inlets+self._outlets:
                        port.installSceneEventFilter(self)
                self.updatePins()

            case QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
                for pin in self._inlets+self._outlets:
                    pin.update()

        return super().itemChange(change, value)

    def brush(self):
        palette = QApplication.instance().palette()
        if self.scene():
            palette = self.scene().palette()

        baseColor = palette.base().color()
        baseColor.setAlpha(255)
        brush = QBrush(baseColor)
        return brush

    def pen(self):
        palette = QApplication.instance().palette()
        if self.scene():
            palette = self.scene().palette()

        pen = QPen(palette.dark().color(), 1)

        if self.isSelected():
            pen.setColor( palette.highlight().color() )
        return pen

    def paint(self, painter:QPainter, option:QStyleOptionGraphicsItem, widget=None):
        painter.setBrush(self.brush())
        painter.setPen(self.pen())
        painter.drawRoundedRect(self.boundingRect(), 4, 4)
        
        fm = QFontMetrics( self.scene().font() )
        painter.drawText(4,fm.height()-1,self._title)

    def title(self):
        return self._title

    def setTitle(self, text: str):
        self._title = text
        self.update()

    def addInlet(self, inlet: InletWidget):
        inlet._parent_node = self
        inlet.setParentItem(self)
        self._inlets.append(inlet)
        self.updatePins()
        if self.scene():
            inlet.installSceneEventFilter(self)

    def removeInlet(self, inlet: InletWidget):
        inlet._parent_node = None
        inlet.scene().removeItem(inlet)
        self._inlets.remove(inlet)
        self.updatePins()
        inlet.removeSceneEventFilter(self)

    def addOutlet(self, outlet: OutletWidget):
        outlet._parent_node = self
        outlet.setParentItem(self)
        self._outlets.append(outlet)
        self.updatePins()
        outlet.installSceneEventFilter(self)

    def removeOutlet(self, outlet: OutletWidget):
        outlet._parent_node = None
        self._outlets.remove(outlet)
        outlet.scene().removeItem(outlet)
        self.updatePins()

    def updatePins(self):
        inletCount = len(self._inlets)
        for idx, inlet in enumerate(self._inlets):
            inlet.setPos(idx/inletCount+(inletCount-1)/2*self.boundingRect().width()+self.boundingRect().width()/2, 0)

        outletCount = len(self._outlets)
        for idx, outlet in enumerate(self._outlets):
            outlet.setPos(idx/outletCount+(outletCount-1)/2*self.boundingRect().width()+self.boundingRect().width()/2, self.boundingRect().height())
