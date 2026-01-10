import os

from pathlib import Path

class Config:
    static_path: Path = Path("static/").absolute()
    editor_path: Path = Path("static/editor/").absolute()
    docs_path: Path = Path("static/docs/").absolute()

    user_src_path: Path = Path("user/projects")
    user_cur_path: Path = Path("user/current")
    user_main_path: Path = user_cur_path / Path("main.py")

    blocks_path: Path = user_src_path / "blocks.json";

    team_logo_path: Path = Path("user/team_logo.jpg");

    def __init__(self):
        os.makedirs(self.user_cur_path, exist_ok=True)
