"""
NPC relation and memory system.
"""

from engine.core.loader import Loader

NPCS_PATH = "data/entities/npcs.csv"
NPC_MEMORIES_PATH = "data/relations/npc_memories.csv"
NPC_TIMELINES_PATH = "data/relations/npc_timelines.csv"

DEFAULT_RELATION = {"respect": 0, "trust": 0, "fear": 0}


class NPCSystem:
    def __init__(self):
        self.npcs = Loader.load_by_id(NPCS_PATH)
        self.memories = Loader.load(NPC_MEMORIES_PATH)
        self.timelines = Loader.load(NPC_TIMELINES_PATH)

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

    # ── NPC Timeline System ─────────────────────────────────────────────
    def process_npc_timelines(self, current_year: int, game_state: dict) -> list[str]:
        """
        Xử lý timeline của tất cả NPC theo năm hiện tại.
        Trả về danh sách sự kiện đã kích hoạt.
        """
        events_fired = []
        world_state = game_state.get("world_state", {})

        for timeline in self.timelines:
            npc_id = timeline.get("npc_id")
            trigger_year = int(timeline.get("trigger_year", 0))
            event_id = f"{npc_id}_{trigger_year}_{timeline.get('event_type', 'unknown')}"

            # Skip nếu đã fire
            if event_id in world_state.get("npc_events_fired", []):
                continue

            # Kiểm tra năm
            if current_year < trigger_year:
                continue

            # Kiểm tra điều kiện đặc biệt
            condition = timeline.get("trigger_condition", "always")
            if not self._check_timeline_condition(condition, game_state, npc_id):
                continue

            # Kích hoạt event
            event_result = self._apply_npc_timeline_event(npc_id, timeline, world_state)
            events_fired.append(timeline.get("event_text", ""))

            # Đánh dấu đã fire
            if "npc_events_fired" not in world_state:
                world_state["npc_events_fired"] = []
            world_state["npc_events_fired"].append(event_id)

        return events_fired

    def _check_timeline_condition(self, condition: str, game_state: dict, npc_id: str) -> bool:
        """Kiểm tra điều kiện kích hoạt timeline event."""
        if condition == "always":
            return True

        player = game_state.get("player", {})
        world_state = game_state.get("world_state", {})

        # Parse condition
        if "player_realm >=" in condition:
            required_realm = condition.split(">=")[1].strip().strip('"')
            player_level = self._get_realm_level(player.get("realm_id", "mortal"))
            required_level = self._get_realm_level(required_realm)
            return player_level >= required_level

        elif "player_sect ==" in condition:
            required_sect = condition.split("==")[1].strip().strip('"')
            return world_state.get("player_sect") == required_sect

        elif "player_sect !=" in condition:
            forbidden_sect = condition.split("!=")[1].strip().strip('"')
            npc_sect = self.npcs.get(npc_id, {}).get("sect_id", "none")
            return world_state.get("player_sect") != npc_sect and world_state.get("player_sect") is not None

        elif "sect_power <" in condition:
            parts = condition.split("<")
            sect_id = parts[0].strip()
            threshold = int(parts[1].strip())
            power = world_state.get("sect_power", {}).get(sect_id, 50)
            return power < threshold

        return True

    def _apply_npc_timeline_event(self, npc_id: str, timeline: dict, world_state: dict) -> dict:
        """Áp dụng kết quả của timeline event cho NPC."""
        npc = self.npcs.get(npc_id)
        if not npc:
            return {}

        event_type = timeline.get("event_type", "none")
        result_str = timeline.get("result", "{}")
        event_text = timeline.get("event_text", "")

        # Parse result JSON
        try:
            import json
            result = json.loads(result_str) if isinstance(result_str, str) else result_str
        except:
            result = {}

        # Áp dụng thay đổi dựa trên loại event
        if event_type == "promote":
            if "realm" in result:
                npc["realm_id"] = result["realm"]
            if "faction_rank" in result or "role" in result:
                npc["role"] = result.get("faction_rank", result.get("role", npc.get("role", "Đệ tử")))

        elif event_type == "die":
            npc["status"] = "dead"

        elif event_type == "change_faction":
            if "new_sect" in result:
                npc["sect_id"] = result["new_sect"]

        elif event_type == "become_enemy":
            relations = world_state.setdefault("npc_relations", {})
            if npc_id not in relations:
                relations[npc_id] = DEFAULT_RELATION.copy()
            relations[npc_id]["respect"] -= 5
            relations[npc_id]["trust"] -= 5

        elif event_type == "disappear":
            npc["status"] = "missing"

        elif event_type == "breakthrough":
            if "realm" in result:
                npc["realm_id"] = result["realm"]

        return result

    def _get_realm_level(self, realm_id: str) -> int:
        """Lấy cấp độ cảnh giới để so sánh."""
        realm_levels = {
            "mortal": 0,
            "qi_refining_1": 1, "qi_refining_2": 2, "qi_refining_3": 3,
            "foundation_1": 4, "foundation_2": 5, "foundation_3": 6,
            "core_formation_1": 7, "core_formation_2": 8, "core_formation_3": 9,
            "nascent_soul_1": 10, "nascent_soul_2": 11, "nascent_soul_3": 12,
            "deity_transform_1": 13, "deity_transform_2": 14, "deity_transform_3": 15,
        }
        return realm_levels.get(realm_id, 0)
