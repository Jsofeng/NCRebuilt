from __future__ import annotations
import json
from pathlib import Path #allows us to use <fileName> / <fileName> / <fileName>

NC_DIR = ".neuralcommit" #constant ROOT DIR FOR ALL DIRECTORIES CREATED

def find_repo(start: Path | None = None) -> Path: #This function finds the root folder of a NeuralCommit repo (if you do nc add <filename> it will find dir and add it to that one).
    current = (start or Path.cwd()).resolve() 

    """
    
    If the caller gives us a starting path, use that.
    Otherwise, use the current terminal directory.
    .resolve() turns it into a full absolute path.
    
    """

    for path in [current, *current.parents]: #splits all the directories based on "/"
        if (path / NC_DIR).is_dir(): #If this folder contains .neuralcommit, this is the repo root.
            return path
        
    raise FileNotFoundError("not a NeuralCommit repository; run `nc init` first")


def nc_path(repo: Path) -> Path: #helper instead of writing repo / ".neuralcommit" do repo / NC_DIR 
    return repo / NC_DIR


def load_config(repo: Path) -> Path:
    config_path = nc_path(repo) / "config.json"
    return json.loads(config_path.read_text(encoding="utf-8")) #reads it as a string then converts json text to pythonic dict

def write_json(path: Path, payload: dict | list) -> None: #creates the directories/files needed and dumps the "payload aka data" into those 
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8") #index turns in to pretty json - sort keys sorts all keys in alphabetical order 


def read_json(path: Path, default):
    if not path.exists():
        return default
    
    return json.loads(path.read_text(encoding='utf-8')) # read_text() -> Open the file, read the bytes, decode them from UTF-8 into a Python string.

