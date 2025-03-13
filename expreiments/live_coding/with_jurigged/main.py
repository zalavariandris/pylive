# import jurigged
import ast
from unittest import result
import textual

expr = "[item for item in item]"

def parse_expression(expr:str):
	return f"parse: {expr}"



# if __name__ == "__main__":
# 	import time
# 	while True:
# 		time.sleep(1)
# 		result = parse_expression(expr)
# 		print(result+"\n")

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label


class StopwatchApp(App):
    """A Textual app to manage stopwatches."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Label(parse_expression(expr))
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = StopwatchApp()
    app.run()
