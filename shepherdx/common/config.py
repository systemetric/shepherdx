import os

from pathlib import Path

class Config:
    static_path: Path = Path("static/").absolute()
    editor_path: Path = Path("static/editor/").absolute()
    docs_path: Path = Path("static/docs/").absolute()

    user_src_path: Path = Path("usercode/projects")
    user_cur_path: Path = Path("usercode/current")

    blocks_path: Path = user_src_path / "blocks.json";

    def __init__(self):
        pass
