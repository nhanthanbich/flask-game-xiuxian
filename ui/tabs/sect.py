"""
Sect inner hall tab.
"""

from ui.renderer import Renderer
from engine.systems.technique import MAX_SLOTS

RANK_NAMES = {
    0: "Chua nhap mon",
    1: "Noi mon",
    2: "De tu chan truyen",
    3: "Truong lao",
}


class SectTab:
    def __init__(self, world, npc, technique):
        self.world = world
        self.npc = npc
        self.tech = technique

    def run(self, player: dict, world_state: dict) -> bool:
        if not world_state.get("player_sect"):
            Renderer.clear()
            Renderer.title("Noi Mon")
            Renderer.line("Nguoi chua gia nhap mon phai.")
            Renderer.pause()
            return False

        changed = False
        while True:
            sect = self.world.sects[world_state["player_sect"]]
            rank = world_state.get("player_rank", 0)
            Renderer.clear()
            Renderer.title(f"Noi Mon - {sect['name_vn']}")
            Renderer.line(f"Cap bac: {RANK_NAMES.get(rank, str(rank))}")
            Renderer.line(f"The luc: {world_state['sect_power'].get(sect['id'], 50)}/100")
            Renderer.line()

            options = [
                "Hoc cong phap mon phai",
                "Danh sach NPC trong mon",
                "Lam nhiem vu tang cap",
                "Quay lai",
            ]
            choice = Renderer.menu(options)
            if choice == 0:
                changed = self._learn_sect_technique(player, world_state) or changed
            elif choice == 1:
                self._show_npcs(player, world_state)
            elif choice == 2:
                changed = self._quest(world_state) or changed
            else:
                return changed

    def _learn_sect_technique(self, player: dict, world_state: dict) -> bool:
        sect_id = world_state["player_sect"]
        rank = world_state.get("player_rank", 0)
        technique_ids = self.world.get_sect_techniques(sect_id, rank)
        techniques = [self.tech.techniques[tid] for tid in technique_ids if tid in self.tech.techniques]
        if not techniques:
            Renderer.line("Cap bac hien tai chua mo cong phap nao.")
            Renderer.pause()
            return False

        Renderer.clear()
        Renderer.title("Cong Phap Mon Phai")
        options = [
            f"{t['name_vn']:18} | {t['element']:4} | MP:{t['mp_cost']} | {t['description'][:30]}"
            for t in techniques
        ] + ["Huy"]
        choice = Renderer.menu(options)
        if choice == len(techniques):
            return False

        chosen = techniques[choice]
        Renderer.clear()
        Renderer.title(f"Gan {chosen['name_vn']} vao slot nao?")
        slot_options = self.tech.get_slot_display(player) + ["Huy"]
        slot_choice = Renderer.menu(slot_options)
        if slot_choice == MAX_SLOTS:
            return False

        self.tech.learn(player, chosen["id"], slot_choice)
        Renderer.line(f"Da hoc {chosen['name_vn']} vao slot {slot_choice + 1}.")
        Renderer.pause()
        return True

    def _show_npcs(self, player: dict, world_state: dict):
        Renderer.clear()
        Renderer.title("Dong Mon")
        for npc in self.npc.get_npcs_in_sect(world_state["player_sect"]):
            relation = self.npc.get_relation(player, npc["id"], world_state)
            Renderer.line(
                f"{npc['name_vn']:16} | {npc['role']:8} | "
                f"Kinh {relation['respect']:2} Tin {relation['trust']:2} So {relation['fear']:2}"
            )
            Renderer.line(f"  {npc['description']}")
        Renderer.pause()

    def _quest(self, world_state: dict) -> bool:
        rank = world_state.get("player_rank", 0)
        if rank >= 3:
            Renderer.line("Nguoi da dat cap bac cao nhat hien tai.")
            Renderer.pause()
            return False
        if not Renderer.confirm("Hoan thanh nhiem vu mon phai de tang cap?"):
            return False
        self.world.promote_player(world_state)
        Renderer.line(f"Cap bac moi: {RANK_NAMES.get(world_state['player_rank'], world_state['player_rank'])}.")
        Renderer.pause()
        return True
