"""
Sect inner hall tab.
"""

from ui.renderer import Renderer
from engine.systems.technique import MAX_SLOTS

RANK_NAMES = {
    0: "Chưa nhập môn",
    1: "Nội môn",
    2: "Đệ tử chân truyền",
    3: "Trưởng lão",
}


class SectTab:
    def __init__(self, world, npc, technique, flavor=None):
        self.world = world
        self.npc = npc
        self.tech = technique
        self.flavor = flavor

    def run(self, player: dict, world_state: dict) -> bool:
        if not world_state.get("player_sect"):
            Renderer.clear()
            Renderer.title("Nội Môn")
            Renderer.line("Người chưa gia nhập môn phái.")
            Renderer.pause()
            return False

        changed = False
        while True:
            sect = self.world.sects[world_state["player_sect"]]
            rank = world_state.get("player_rank", 0)
            Renderer.clear()
            Renderer.title(f"Nội Môn - {sect['name_vn']}")
            Renderer.line(f"Cấp bậc: {RANK_NAMES.get(rank, str(rank))}")
            Renderer.line(f"Thể lực: {world_state['sect_power'].get(sect['id'], 50)}/100")
            Renderer.line()

            options = [
                "Học công pháp môn phái",
                "Danh sách NPC trong môn",
                "Làm nhiệm vụ tăng cấp",
                "Quay lại",
            ]
            choice = Renderer.menu(options)
            if choice == 0:
                changed = self._learn_sect_technique(player, world_state) or changed
            elif choice == 1:
                self._show_npcs(player, world_state)
            elif choice == 2:
                changed = self._quest(player, world_state) or changed
            else:
                return changed

    def _learn_sect_technique(self, player: dict, world_state: dict) -> bool:
        sect_id = world_state["player_sect"]
        rank = world_state.get("player_rank", 0)
        technique_ids = self.world.get_sect_techniques(sect_id, rank)
        techniques = [self.tech.techniques[tid] for tid in technique_ids if tid in self.tech.techniques]
        if not techniques:
            Renderer.line("Cấp bậc hiện tại chưa mở công pháp nào.")
            Renderer.pause()
            return False

        Renderer.clear()
        Renderer.title("Công Pháp Môn Phái")
        options = [
            f"{t['name_vn']:18} | {t['element']:4} | MP:{t['mp_cost']} | {t['description'][:30]}"
            for t in techniques
        ] + ["Hủy"]
        choice = Renderer.menu(options)
        if choice == len(techniques):
            return False

        chosen = techniques[choice]
        Renderer.clear()
        Renderer.title(f"Gán {chosen['name_vn']} vào slot nào?")
        slot_options = self.tech.get_slot_display(player) + ["Hủy"]
        slot_choice = Renderer.menu(slot_options)
        if slot_choice == MAX_SLOTS:
            return False

        self.tech.learn(player, chosen["id"], slot_choice)
        Renderer.line(f"Đã học {chosen['name_vn']} vào slot {slot_choice + 1}.")
        Renderer.pause()
        return True

    def _show_npcs(self, player: dict, world_state: dict):
        Renderer.clear()
        Renderer.title("Đồng Môn")
        for npc in self.npc.get_npcs_in_sect(world_state["player_sect"]):
            relation = self.npc.get_relation(player, npc["id"], world_state)
            Renderer.line(
                f"{npc['name_vn']:16} | {npc['role']:8} | "
                f"Kính {relation['respect']:2} Tin {relation['trust']:2} Sợ {relation['fear']:2}"
            )
            Renderer.line(f"  {npc['description']}")
        Renderer.pause()

    def _quest(self, player: dict, world_state: dict) -> bool:
        rank = world_state.get("player_rank", 0)
        if rank >= 3:
            Renderer.line("Người đã đạt cấp bậc cao nhất hiện tại.")
            Renderer.pause()
            return False
        if not Renderer.confirm("Hoàn thành nhiệm vụ môn phái để tăng cấp?"):
            return False
        
        # Show quest completion flavor
        if self.flavor:
            Renderer.line(self.flavor.get("quest_complete", player.get("realm_id", "")))
        
        Renderer.line("Hoàn thành nhiệm vụ!")
        self.world.promote_player(world_state)
        
        # Show rank up flavor
        if self.flavor:
            Renderer.line(self.flavor.get("rank_up", player.get("realm_id", "")))
        
        Renderer.line(f"Cap bac moi: {RANK_NAMES.get(world_state['player_rank'], world_state['player_rank'])}.")
        Renderer.pause()
        return True
