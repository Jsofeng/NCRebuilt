from __future__ import annotations

import hashlib
import math
import sqlite3
from collections import Counter
from pathlib import Path

"""
leading underscore = Internal/private helper. Not meant to be used outside 
"""

def _tokens(text: str) -> list[str]:
    return [part.lower() for part in "".join(c if c.isalnum() else " " for c in text).split()] #turns all words into lowercase (only characters that are alphanumerical otherwise replace that with a space then finally splits them all )

"""
This is the vector embedding generator.
Turns text into numbers.
"""

def _embed(text: str) -> dict[str, float]:
    counts = Counter(_tokens(text)) #creates a frequency hashmap
    norm = math.sqrt(
        sum(
            value * value 
            for value in counts.values()
        )
    ) or 1.0 #protect against zero division

    return { key: value / norm for key, value in counts.items()} #sets the new values back to the dict

#This compares semantic similarity.
"""
compares two separate dicts
0 → unrelated
1 → identical
"""
def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    return sum(value * b.get(key, 0.0) for key, value in a.items())



class VectorIndex:
    def __init__(self):
        pass