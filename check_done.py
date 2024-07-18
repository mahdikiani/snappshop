from pathlib import Path
import os
import json

dones = set()
filepath = Path("db") / "done.txt"


def check_done(item_str: str, filepath: Path = filepath):
    global dones
    if not dones:
        if filepath.exists():
            with open(filepath) as f:
                dones = {l.strip() for l in f.readlines()}

    return item_str in dones


def add_done(item_str: str, filepath: Path = filepath):
    global dones

    if item_str in dones:
        return

    dones.add(item_str)

    with open(filepath, "a") as f:
        print(item_str, file=f)
