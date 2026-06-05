"""
ui/tabs/techniques.py
Tab kỹ năng: xem slot, học kỹ năng mới, thay thế.
"""

from ui.renderer import Renderer
from engine.systems.technique import TechniqueSystem, MAX_SLOTS


class TechniqueTab:

    def __init__(self, technique: TechniqueSystem):
        self.tech = technique

    def run(self, player: dict) -> bool:
        """Trả về True nếu có thay đổi slot."""
        self.tech.ensure_slots(player)
        changed = False

        while True:
            Renderer.clear()
            Renderer.title("Công Pháp — Kỹ Năng")
            Renderer.line(f"Slot hiện tại ({MAX_SLOTS} ô):")
            Renderer.line()
            for line in self.tech.get_slot_display(player):
                Renderer.line(line)
            Renderer.line()

            options = ["Học kỹ năng mới", "Xóa kỹ năng trong slot", "Quay lại"]
            choice  = Renderer.menu(options)

            if choice == 2:
                break

            if choice == 0:
                changed = self._learn_menu(player) or changed
            elif choice == 1:
                changed = self._remove_menu(player) or changed

        return changed

    def _learn_menu(self, player: dict) -> bool:
        """Chọn kỹ năng học và slot để gán vào."""
        learnable = self.tech.get_learnable(player["realm_id"])
        if not learnable:
            Renderer.line("Chưa có kỹ năng nào học được.")
            Renderer.pause()
            return False

        Renderer.clear()
        Renderer.title("Chọn Kỹ Năng Muốn Học")
        Renderer.line()

        options = [
            f"{t.get('name_vn', t['id']):18} | {t.get('element', 'None'):5} | MP:{t.get('mp_cost', 10):2} | {t.get('description', '')[:32]}"
            for t in learnable
        ] + ["Quay lại"]

        choice = Renderer.menu(options)
        if choice == len(learnable):
            return False

        chosen = learnable[choice]

        # Chọn slot
        Renderer.clear()
        Renderer.title(f"Gán '{chosen['name_vn']}' vào slot nào?")
        Renderer.line()
        slot_options = self.tech.get_slot_display(player) + ["Huỷ"]
        slot_choice  = Renderer.menu(slot_options)

        if slot_choice == MAX_SLOTS:
            return False

        self.tech.learn(player, chosen["id"], slot_choice)
        Renderer.line()
        Renderer.line(f"✓ Đã học: {chosen['name_vn']} → Slot {slot_choice + 1}")
        Renderer.pause()
        return True

    def _remove_menu(self, player: dict) -> bool:
        Renderer.clear()
        Renderer.title("Xóa Kỹ Năng")
        slot_options = self.tech.get_slot_display(player) + ["Huỷ"]
        slot_choice = Renderer.menu(slot_options)

        if slot_choice == MAX_SLOTS:
            return False
        if not player["technique_slots"][slot_choice]:
            Renderer.line("Slot này đang trống.")
            Renderer.pause()
            return False

        self.tech.remove(player, slot_choice)
        Renderer.line(f"Đã xóa kỹ năng ở Slot {slot_choice + 1}.")
        Renderer.pause()
        return True
