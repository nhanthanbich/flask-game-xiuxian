"""
save_manager.py
Hệ thống lưu game: tối đa 5 slot độc lập.
Mỗi slot = saves/slot_{N}.json gồm: player + time + metadata.
"""

import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLAUDE_ROOT = os.path.dirname(os.path.dirname(BASE_DIR))
SAVE_DIR = os.path.join(CLAUDE_ROOT, "saves")
MAX_SLOTS = 5
LEGACY_SAVE = "player.json"


class SaveManager:

    # ── Đường dẫn ────────────────────────────────────────────────────────
    @staticmethod
    def _path(slot: int) -> str:
        return os.path.join(SAVE_DIR, f"slot_{slot}.json")

    @staticmethod
    def _legacy_path() -> str:
        return os.path.join(SAVE_DIR, LEGACY_SAVE)

    # ── Lưu ──────────────────────────────────────────────────────────────
    @staticmethod
    def save(slot: int, player: dict, time_data: dict, world_state: dict | None = None):
        """Lưu vào slot (1-5). Ghi đè nếu đã tồn tại."""
        os.makedirs(SAVE_DIR, exist_ok=True)
        data = {
            "meta": {
                "saved_at":   datetime.now().strftime("%d/%m/%Y %H:%M"),
                "player_name": player.get("name", "???"),
                "realm_id":   player.get("realm_id", ""),
                "game_time":  time_data.get("display_short", ""),
            },
            "player": player,
            "time":   time_data,
            "world_state": world_state or {},
        }
        with open(SaveManager._path(slot), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ── Load ─────────────────────────────────────────────────────────────
    @staticmethod
    def load(slot: int) -> dict | None:
        """Load slot. Trả về None nếu chưa có."""
        path = SaveManager._path(slot)
        if not os.path.exists(path):
            if slot == 1 and os.path.exists(SaveManager._legacy_path()):
                with open(SaveManager._legacy_path(), encoding="utf-8") as f:
                    data = json.load(f)
                player = data.get("player", {})
                time_data = data.get("time", {})
                return {
                    "meta": {
                        "saved_at": "legacy",
                        "player_name": player.get("name", "???"),
                        "realm_id": player.get("realm_id", ""),
                        "game_time": "",
                    },
                    "player": player,
                    "time": time_data,
                }
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # ── Kiểm tra ─────────────────────────────────────────────────────────
    @staticmethod
    def exists(slot: int) -> bool:
        if slot == 1 and os.path.exists(SaveManager._legacy_path()):
            return True
        return os.path.exists(SaveManager._path(slot))

    @staticmethod
    def any_save() -> bool:
        return any(SaveManager.exists(i) for i in range(1, MAX_SLOTS + 1))

    # ── Danh sách slot ───────────────────────────────────────────────────
    @staticmethod
    def slot_list() -> list[dict]:
        """
        Trả về list 5 phần tử, mỗi phần tử:
          { slot, empty, name, realm_id, game_time, saved_at }
        """
        result = []
        for i in range(1, MAX_SLOTS + 1):
            if SaveManager.exists(i):
                data = SaveManager.load(i)
                meta = data.get("meta", {})
                result.append({
                    "slot":      i,
                    "empty":     False,
                    "name":      meta.get("player_name", "???"),
                    "realm_id":  meta.get("realm_id", ""),
                    "game_time": meta.get("game_time", ""),
                    "saved_at":  meta.get("saved_at", ""),
                })
            else:
                result.append({"slot": i, "empty": True})
        return result

    # ── Xóa ──────────────────────────────────────────────────────────────
    @staticmethod
    def delete(slot: int):
        path = SaveManager._path(slot)
        if os.path.exists(path):
            os.remove(path)
