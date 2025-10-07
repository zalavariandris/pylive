from edifice import CustomWidget, PropsDiff
from PySide6.QtWidgets import QPushButton, QFileDialog

class FileInput(CustomWidget[QPushButton]):
    def __init__(self, path="", on_change=None, **kwargs):
        super().__init__(**kwargs)
        self._register_props(
            {
                "path": path,
                "on_change": on_change,
            }
        )

    def create_widget(self):
        button = QPushButton("Select File...")
        def on_click():
            file_path, _ = QFileDialog.getOpenFileName(button, "Select a file", self.props["path"])
            if file_path and self.props["on_change"]:
                self.props["on_change"](file_path)
        button.pressed.connect(on_click)
        return button

    def update(self, widget: QPushButton, diff_props: PropsDiff):
        # This function should update the widget
        match diff_props.get("path"):
            case _propold, propnew:
                widget.setText(propnew)