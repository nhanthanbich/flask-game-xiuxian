"""
NPC relation and memory system.
"""

from engine.core.loader import Loader

NPCS_PATH = "data/entities/npcs.csv"
NPC_MEMORIES_PATH = "data/relations/npc_memories.csv"

DEFAULT_RELATION = {"respect": 0, "trust": 0, "fear": 0}


class NPCSystem:
    def __init__(self):
        self.npcs = Loader.load_by_id(NPCS_PATH)
        self.memories = Loader.load(NPC_MEMORIES_PATH)

    def get_npcs_in_sect(self, sect_id: str) -> list[dict]:
        return [
            npc for npc in self.npcs.values()
            if npc["sect_id"] == sect_id or npc["sect_id"] == "none"
        ]

    def get_relation(self, player: dict, npc_id: str, world_state: dict | None = None) -> dict:
        state = world_state if world_state is not None else {}
        relations = state.setdefault("npc_relations", {})
        relation = relations.setdefault(npc_id, DEFAULT_RELATION.copy())
        return relation

    def update_relation(self, player: dict, npc_id: str, event_type: str, world_state: dict | None = None):
        relation = self.get_relation(player, npc_id, world_state)
        for memory in self._matching_memories(npc_id, event_type):
            relation["respect"] += int(memory["relation_delta_respect"])
            relation["trust"] += int(memory["relation_delta_trust"])
            relation["fear"] += int(memory["relation_delta_fear"])

    def get_greeting(self, npc_id: str, relation: dict) -> str:
        npc = self.npcs[npc_id]
        if relation.get("fear", 0) >= 6:
            return f"{npc['name_vn']} cẩn trọng lùi nửa bước: 'Uy danh của ngươi không nhỏ.'"
        if relation.get("trust", 0) >= 6:
            return f"{npc['name_vn']} mỉm cười: 'Ta tin người có thể đi xa hơn.'"
        if relation.get("respect", 0) >= 6:
            return f"{npc['name_vn']} chắp tay: 'Thực lực của ngươi đang được công nhận.'"
        if npc["personality"] == "friendly":
            return f"{npc['name_vn']}: 'Cần gì thì cứ hỏi ta.'"
        if npc["personality"] == "strict":
            return f"{npc['name_vn']}: 'Giữ tâm tĩnh, đừng nóng với tiến độ.'"
        if npc["personality"] == "greedy":
            return f"{npc['name_vn']}: 'Có lợi ích thì mới dễ nói chuyện.'"
        return f"{npc['name_vn']}: 'Nhận quả của ngươi còn chưa rõ.'"

    def remember(self, player: dict, npc_id: str, event_type: str, world_state: dict | None = None):
        state = world_state if world_state is not None else {}
        memories = state.setdefault("npc_memories", {})
        npc_memories = memories.setdefault(npc_id, [])
        if event_type not in npc_memories:
            npc_memories.append(event_type)
        self.update_relation(player, npc_id, event_type, state)

    def memory_texts(self, npc_id: str, event_types: list[str]) -> list[str]:
        texts = []
        for event_type in event_types:
            matched = self._matching_memories(npc_id, event_type)
            if matched:
                texts.append(matched[0]["memory_text"])
        return texts

    def _matching_memories(self, npc_id: str, event_type: str) -> list[dict]:
        return [
            memory for memory in self.memories
            if memory["npc_id"] == npc_id and memory["trigger_event"] == event_type
        ]

    def on_join_sect(self, data: dict):
        player = data["player"]
        world_state = data["world_state"]
        sect_id = data["sect_id"]
        for npc in self.get_npcs_in_sect(sect_id):
            self.remember(player, npc["id"], "join_sect", world_state)

    def on_breakthrough(self, data: dict):
        self._remember_for_known(data["player"], data["world_state"], "breakthrough")

    def on_combat_win(self, data: dict):
        self._remember_for_known(data["player"], data["world_state"], "win_combat")

    def on_gift(self, data: dict):
        npc_id = data.get("npc_id")
        if npc_id:
            self.remember(data["player"], npc_id, "gift", data["world_state"])

    def _remember_for_known(self, player: dict, world_state: dict, event_type: str):
        known_ids = set(world_state.get("npc_relations", {}).keys())
        sect_id = world_state.get("player_sect")
        for npc in self.npcs.values():
            if npc["id"] in known_ids or npc["sect_id"] == sect_id:
                self.remember(player, npc["id"], event_type, world_state)
