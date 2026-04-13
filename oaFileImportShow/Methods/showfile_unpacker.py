# oaFileImportShow/Methods/showfile_unpacker.py
# Author: Anthony Peter Kuzub
# Version: 20260331.2330.2
#
# Description: Pure Rust showfile unpacker (No Python fallback).

import orjson
from .oaShowfileUnpacker_rs from oaRustCore import oa_showfile_unpacker_rs as oashowfileunpacker_rs

LOCAL_DEBUG = False

class ShowfileUnpacker:
    """
    High-performance secure showfile unpacker using Rust.
    MANDATORY Rust implementation.
    """
    @staticmethod
    def unpack(file_path: str):
        if LOCAL_DEBUG:
            print("📦🛠️🔗 [SHOW] Using PURE RUST unpacker.")
        raw_dict = oashowfileunpacker_rs.unpack_showfile(file_path)
        # Post-process strings into dictionaries if they are JSON
        processed = {}
        for name, content in raw_dict.items():
            try:
                processed[name] = orjson.loads(content)
            except Exception:
                processed[name] = content
        return processed
