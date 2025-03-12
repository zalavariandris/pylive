from typing import *

import pandoc
from pathlib import Path

def root():
    return Path("C:/Users/andris/iCloudDrive/iCloud~md~obsidian/DisszertacioNotes/WEB edition")

def join(folder:Path, file:Path):
    return folder / file

def read_text(path:Path):
    return path.read_text(encoding="utf-8")

def markdown_to_html(text):
    return text

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *

def dummy(required: str, optional:str="hello", *args, **kwargs):
    return f"inputs: {required}, {optional}, {args}, {kwargs}"

def main():
    import sys
    from PySide6.QtWebView import QtWebView
    from PySide6.QtWebEngineWidgets import QWebEngineView
    QtWebView.initialize()
    app = QApplication(sys.argv)
    web_view = QWebEngineView()
        
    # Set custom HTML content
    html_content = """
    <html>
    <head><title>Custom Page</title></head>
    <body><h1>Welcome to PySide6 WebView</h1><p>This is a custom HTML page.</p></body>
    </html>
    """
    web_view.setHtml(html_content)

    web_view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


