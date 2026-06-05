"""
Inventory tab.
"""

from ui.renderer import Renderer

TYPE_NAMES = {
    "pill": "Dan duoc",
    "material": "Linh thao",
    "artifact": "Phap bao",
}


class InventoryTab:
    def __init__(self, item_system):
        self.items = item_system

    def run(self, player: dict) -> bool:
        self.items.ensure_inventory(player)
        changed = False
        while True:
            Renderer.clear()
            Renderer.title("Túi Đồ")
            self._draw_inventory(player)
            options = ["Sử dụng vật phẩm", "Quay lại"]
            choice = Renderer.menu(options)
            if choice == 1:
                return changed
            changed = self._use_item(player) or changed

    def _draw_inventory(self, player: dict):
        if not player["inventory"]:
            Renderer.line("Túi đồ đang trống.")
            Renderer.line()
            return
        for item_type, label in TYPE_NAMES.items():
            rows = [
                (item_id, qty)
                for item_id, qty in player["inventory"].items()
                if self.items.items.get(item_id, {}).get("type") == item_type
            ]
            if not rows:
                continue
            Renderer.title(label)
            for item_id, qty in rows:
                item = self.items.items[item_id]
                Renderer.line(f"{item['name_vn']} x{qty} - {item['description']}")
            Renderer.line()

    def _use_item(self, player: dict) -> bool:
        usable = self.items.get_usable(player)
        if not usable:
            Renderer.line("Không có vật phẩm có thể dùng.")
            Renderer.pause()
            return False
        options = [
            f"{item['name_vn']} | {item['effect_type']} +{item['effect_value']} | {item['description']}"
            for item in usable
        ] + ["Hủy"]
        choice = Renderer.menu(options)
        if choice == len(usable):
            return False
        item = usable[choice]
        if not Renderer.confirm(f"Dùng {item['name_vn']}?"):
            return False
        Renderer.line(self.items.use_item(player, item["id"]))
        Renderer.pause()
        return True
