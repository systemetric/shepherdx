import os

from pathlib import Path

class Config:
    static_path: Path = Path("static/").absolute()
    editor_path: Path = Path("static/editor/").absolute()
    docs_path: Path = Path("static/docs/").absolute()

    user_src_path: Path = Path("user/projects")
    user_cur_path: Path = Path("user/current")
    user_main_name: Path = Path("main.py")
    user_main_path: Path = user_cur_path / user_main_name

    blocks_path: Path = user_src_path / "blocks.json";

    team_logo_path: Path = Path("user/team_logo.jpg");
    game_logo_path: Path = Path("user/game_logo.jpg");

    tmp_store_path: Path = Path("/run/user/1000/shepherd")
    tmp_graphic: Path = tmp_store_path / "image.jpg"
    tmp_log: Path = tmp_store_path / "log.txt"

    arena_usb_path: Path = Path("/media/ArenaUSB")

    start_button_pin: int = 26
    start_button_bounce_time: int = 1000

    round_length: int = 180
    kill_delay: int = 5

    def __init__(self):
        os.makedirs(self.user_cur_path, exist_ok=True)
        os.makedirs(self.tmp_store_path, exist_ok=True)
