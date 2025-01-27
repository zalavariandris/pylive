from typing import *

def read_text(path:str):
    from pathlib import Path
    return Path(path).read_text()

def parse_md(text:str)->str:
    ...

def merge_chapters(*markdowns:Iterable[str])->str:
    return "\n".join(*markdowns)

def create_reference_footnotes(md:str)->str:
    ...

def seperate_chapters(md:str)->list[str]:
    return md.split("\n")

def extract_references(md:str)->str:
    ...
def make_bibliography(md:str, bib:str):
    ...

def template(title:str, abstract:str, prologue:str, chapters:list[str]):
    ...

"""graph
nodes:
- ...
edges:
- ...
"""