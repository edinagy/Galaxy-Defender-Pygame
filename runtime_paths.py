import os
import sys
from pathlib import Path


GAME_FOLDER_NAME = "GalaxyDefender"


def is_frozen():
    return bool(getattr(sys, "frozen", False))


def resource_root():
    if is_frozen():
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def resource_path(*parts):
    return resource_root().joinpath(*parts)


def user_data_root():
    override = os.environ.get("GALAXY_DEFENDER_DATA_DIR")
    if override:
        return Path(override)

    if not is_frozen():
        return resource_root() / "data"

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / GAME_FOLDER_NAME
    return Path.home() / f".{GAME_FOLDER_NAME.lower()}"


def user_data_path(filename):
    folder = user_data_root()
    folder.mkdir(parents=True, exist_ok=True)
    return folder / filename


def prepare_runtime_working_directory():
    os.chdir(resource_root())
