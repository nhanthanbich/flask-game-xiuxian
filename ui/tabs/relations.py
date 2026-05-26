"""
NPC relation tab.
"""

from ui.renderer import Renderer


class RelationTab:
    def __init__(self, npc):
        self.npc = npc

    def run(self, player: dict, world_state: dict) -> bool:
        while True:
            npcs = self._known_npcs(world_state)
            Renderer.clear()
            Renderer.title("Quan He NPC")
            if not npcs:
                Renderer.line("Chua gap NPC nao.")
                Renderer.pause()
                return False

            options = [
                self._npc_line(player, world_state, npc)
                for npc in npcs
            ] + ["Quay lai"]
            choice = Renderer.menu(options)
            if choice == len(npcs):
                return False
            self._npc_detail(player, world_state, npcs[choice])

    def _known_npcs(self, world_state: dict) -> list[dict]:
        known_ids = set(world_state.get("npc_relations", {}).keys())
        sect_id = world_state.get("player_sect")
        result = []
        for npc in self.npc.npcs.values():
            if npc["id"] in known_ids or npc["sect_id"] == sect_id or npc["sect_id"] == "none":
                result.append(npc)
        return result

    def _npc_line(self, player: dict, world_state: dict, npc: dict) -> str:
        relation = self.npc.get_relation(player, npc["id"], world_state)
        return (
            f"{npc['name_vn']:16} | {npc['role']:8} | "
            f"Kinh {relation['respect']:2} Tin {relation['trust']:2} So {relation['fear']:2}"
        )

    def _npc_detail(self, player: dict, world_state: dict, npc: dict):
        relation = self.npc.get_relation(player, npc["id"], world_state)
        Renderer.clear()
        Renderer.title(npc["name_vn"])
        Renderer.line(npc["description"])
        Renderer.line()
        Renderer.line(self.npc.get_greeting(npc["id"], relation))
        Renderer.line()
        Renderer.title("Ky Uc")
        event_types = world_state.get("npc_memories", {}).get(npc["id"], [])
        texts = self.npc.memory_texts(npc["id"], event_types)
        if not texts:
            Renderer.line("NPC nay chua co ky uc dang ke ve nguoi.")
        for text in texts:
            Renderer.line(f"- {text}")
        Renderer.pause()
