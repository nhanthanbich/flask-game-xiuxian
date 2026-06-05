"""
Inventory and item effects.
"""

from engine.core.loader import Loader
from engine.systems.technique import TechniqueSystem

ITEMS_PATH = "data/entities/items.csv"


class ItemSystem:
    def __init__(self):
        self.items = Loader.load_by_id(ITEMS_PATH)
        self.tech = TechniqueSystem()

    def ensure_inventory(self, player: dict):
        player.setdefault("inventory", {})

    def get_usable(self, player: dict) -> list[dict]:
        self.ensure_inventory(player)
        player_level = self.tech.get_realm_index(player["realm_id"])
        return [
            item for item_id, item in self.items.items()
            if player["inventory"].get(item_id, 0) > 0
            and self.tech.get_realm_index(item["req_realm"]) <= player_level
        ]

    def add_to_inventory(self, player: dict, item_id: str, qty: int = 1):
        self.ensure_inventory(player)
        if item_id not in self.items:
            raise KeyError(f"Unknown item: {item_id}")
        player["inventory"][item_id] = player["inventory"].get(item_id, 0) + qty

    def remove_from_inventory(self, player: dict, item_id: str, qty: int = 1) -> bool:
        self.ensure_inventory(player)
        if player["inventory"].get(item_id, 0) < qty:
            return False
        player["inventory"][item_id] -= qty
        if player["inventory"][item_id] <= 0:
            del player["inventory"][item_id]
        return True

    def use_item(self, player: dict, item_id: str) -> str:
        if item_id not in self.items:
            return "Vật phẩm không tồn tại."
        if not self.remove_from_inventory(player, item_id):
            return "Không có vật phẩm này trong túi."

        item = self.items[item_id]
        value = int(item["effect_value"])
        effect = item["effect_type"]

        if effect == "heal_hp":
            player["hp_bonus"] = player.get("hp_bonus", 0) + value
            return f"{item['name_vn']} bồi bổ thân thể, sinh lực tiềm năng +{value}."
        if effect == "heal_mp":
            player["mp_bonus"] = player.get("mp_bonus", 0) + value
            return f"{item['name_vn']} bổ sung linh lực, linh lực tiềm năng +{value}."
        if effect == "exp_boost":
            player["exp"] = player.get("exp", 0) + value
            return f"{item['name_vn']} hóa thành linh khí, nhận {value} exp."
        if effect == "stat_boost":
            player["stat_bonus"] = player.get("stat_bonus", 0) + value
            return f"{item['name_vn']} tăng cần cơ chiến đấu +{value}."
        return f"{item['name_vn']} không có tác dụng rõ ràng."
