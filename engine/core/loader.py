"""
CSV/JSON loader with small in-memory caches.
"""

import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
SETTINGS_PATH = os.path.join(PROJECT_ROOT, "config", "settings.json")


def _resolve_filepath(filepath: str) -> str:
    return filepath if os.path.isabs(filepath) else os.path.join(PROJECT_ROOT, filepath)


class Loader:
    _cache = {}
    _json_cache = {}

    @staticmethod
    def load(filepath: str) -> list[dict]:
        filepath = _resolve_filepath(filepath)
        if filepath in Loader._cache:
            return Loader._cache[filepath]
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Khong tim thay file: {filepath}")
        with open(filepath, encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        Loader._cache[filepath] = rows
        return rows

    @staticmethod
    def load_by_id(filepath: str, id_field: str = "id") -> dict:
        rows = Loader.load(filepath)
        return {row[id_field]: row for row in rows}

    @staticmethod
    def load_json(filepath: str) -> dict:
        if filepath in Loader._json_cache:
            return Loader._json_cache[filepath]
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Khong tim thay file: {filepath}")
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        Loader._json_cache[filepath] = data
        return data

    @staticmethod
    def load_settings() -> dict:
        return Loader.load_json(SETTINGS_PATH)

    @staticmethod
    def clear_cache():
        Loader._cache.clear()
        Loader._json_cache.clear()
