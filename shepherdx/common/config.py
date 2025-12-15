import os

from pathlib import Path

class Config:
    static_path: Path = Path("static/").absolute()
    editor_path: Path = Path("static/editor/").absolute()
    docs_path: Path = Path("static/docs/").absolute()

    def __init__(self):
        pass
