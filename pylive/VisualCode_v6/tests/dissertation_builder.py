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

if __name__ == "__main__":
    ...