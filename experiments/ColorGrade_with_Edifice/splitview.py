from edifice import Element, QtWidgetElement, PropsDiff
from PySide6.QtWidgets import QSplitter
from PySide6.QtCore import Qt
from edifice.engine import _WidgetTree, _get_widget_children, CommandType

class SplitView(QtWidgetElement[QSplitter]):
    """
    A layout that splits its children and allows user-resizable panels.

    .. highlights::

        - Underlying Qt Widget: `QSplitter <https://doc.qt.io/qtforpython-6/PySide6/QtWidgets/QSplitter.html>`_

    .. rubric:: Props

    All **props** from :class:`QtWidgetElement` plus:

    Args:
        orientation:
            Orientation of the splitter: `QtCore.Qt.Horizontal` or `QtCore.Qt.Vertical`.
        sizes:
            Optional list of initial sizes for each widget (in pixels).

    .. rubric:: Usage

    .. code-block:: python

        SplitView(orientation=QtCore.Qt.Horizontal)
    """

    def __init__(
        self,
        orientation: Qt.Orientation = Qt.Orientation.Horizontal,
        sizes: list[int] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._register_props({
            "orientation": orientation,
            "sizes": sizes,
        })
        self._widget_children: list[QtWidgetElement] = []

    def _initialize(self):
        self.underlying = QSplitter(self.props["orientation"])
        self.underlying.setObjectName(str(id(self)))

    def _qt_update_commands(
        self,
        widget_trees: dict[Element, _WidgetTree],
        diff_props: PropsDiff,
    ):
        if self.underlying is None:
            self._initialize()

        assert self.underlying is not None
        commands = super()._qt_update_commands_super(widget_trees, diff_props, self.underlying)

        children = _get_widget_children(widget_trees, self)

        if children != self._widget_children:
            # Remove existing widgets
            for i in reversed(range(self.underlying.count())):
                widget = self.underlying.widget(i)
                self.underlying.widget(i).setParent(None)
                widget.deleteLater()

            # Add new children
            for child in children:
                assert child.underlying is not None
                self.underlying.addWidget(child.underlying)

            self._widget_children = children

            if self.props["sizes"]:
                commands.append(CommandType(self.underlying.setSizes, self.props["sizes"]))

        return commands
