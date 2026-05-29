from __future__ import annotations

import hashlib #SHA-256 (Secure Hash Algorithm 256-bit) is a highly secure cryptographic hash function used to turn digital data of any size into an irreversible
from pathlib import Path

#step by step
#1. __init__
#2 put_file()
#3 put_bytes()
#4 get_bytes()

class ObjectStore:
    
    def __init__(self, root: Path):
        self.root = root
        self.objects = root / "objects"
        self.objects.mkdir(parents=True, exist_ok=True) # parents=True means create missing parent folders too.

    def put_bytes(self, data: bytes) -> str: #This stores raw bytes and returns their hash.
        digest = hashlib.sha256(data).hexdigest() #This creates a SHA-256 hash.
        target = self.objects / digest[:2] / digest[2:] 

        """
        Structure we want
        .neuralcommit/
            └── objects/
                └── 84/
                    └── 8b246a3708574a97a2af2990690e6c0b4c72ee61bba3b6e1af6ca15ed378f9
        """

        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data) #Write the actual file contents.

        return digest
    
    def put_file(self, path: Path) -> str: #creates a hash for the path
        return self.put_bytes(path.read_bytes())
    
    def get_bytes(self, digest: str) -> bytes: #decodes the bytes
        return (self.objects / digest[:2] / digest[2:]).read_bytes()


