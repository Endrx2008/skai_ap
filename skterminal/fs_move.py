from config import SKAI_HOME
from pathlib import Path
import shutil


def move_file(filename: str, destination: str) -> str:
    """
    Moves a file to a subfolder inside skai_home.
    - filename:    name of the file (can include current subfolder, e.g. "sub/file.txt")
    - destination: target subfolder name (e.g. "hy")

    The destination folder must already exist.
    """
    if not filename or not destination:
        return "Error: both filename and destination folder are required."

    src_name = Path(filename).name
    dest_dir = SKAI_HOME / Path(destination).name

    matches = list(SKAI_HOME.rglob(src_name))
    matches = [m for m in matches if m.is_file()]

    if not matches:
        return f"File '{src_name}' not found anywhere in skai_home."

    src = matches[0]

    if not dest_dir.exists():
        return f"Destination folder '{dest_dir.name}' does not exist. Create it first."

    if not dest_dir.is_dir():
        return f"'{dest_dir.name}' is a file, not a folder."

    target = dest_dir / src_name

    if target.exists():
        return f"A file named '{src_name}' already exists in '{dest_dir.name}'."

    shutil.move(str(src), str(target))
    return f"✅ Moved '{src_name}' → '{dest_dir.name}/{src_name}'."
