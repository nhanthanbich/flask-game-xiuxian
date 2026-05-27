"""
World and sect system.
"""

import random

from engine.core.loader import Loader
from engine.systems.technique import TechniqueSystem

SECTS_PATH = "data/entities/sects.csv"
WORLD_EVENTS_PATH = "data/entities/world_events.csv"
SECT_TECHNIQUES_PATH = "data/relations/sect_techniques.csv"
SECRET_REALMS_PATH = "data/entities/secret_realms.csv"
SECT_QUESTS_PATH = "data/relations/sect_quests.csv"

class WorldSystem:
    def __init__(self, settings: dict | None = None):
        self.settings = settings or Loader.load_settings()
        self.sects = Loader.load_by_id(SECTS_PATH)
        self.events = Loader.load_by_id(WORLD_EVENTS_PATH)
        self.sect_techniques = Loader.load(SECT_TECHNIQUES_PATH)
        self.secret_realms = Loader.load_by_id(SECRET_REALMS_PATH)
        self.sect_quests = Loader.load_by_id(SECT_QUESTS_PATH)
        self.tech = TechniqueSystem()

    def default_state(self) -> dict:
        return {
            "player_sect": None,
            "player_rank": 0,
            "sect_power": {sect_id: int(self.settings["default_sect_power"]) for sect_id in self.sects},
            "events_fired": [],
            "npc_relations": {},
            "npc_memories": {},
            "npc_events_fired": [],
            "world_history": [],
            "combat_wins": 0,
            "sect_contrib": 0,
            "sim_year": 0,
        }

    def ensure_state(self, world_state: dict | None) -> dict:
        state = self.default_state()
        if world_state:
            saved_power = world_state.get("sect_power", {})
            saved_events = world_state.get("events_fired", [])
            saved_npc = world_state.get("npc_relations", {})
            saved_memories = world_state.get("npc_memories", {})
            saved_npc_events = world_state.get("npc_events_fired", [])
            saved_history = world_state.get("world_history", [])
            state.update(world_state)
            state["sect_power"] = self.default_state()["sect_power"]
            state["sect_power"].update(saved_power)
            state["events_fired"] = list(saved_events)
            state["npc_relations"] = dict(saved_npc)
            state["npc_memories"] = dict(saved_memories)
            state["npc_events_fired"] = list(saved_npc_events)
            state["world_history"] = list(saved_history)
        return state

    def on_time_tick(self, data: dict):
        data["logs"] = self.tick(data["time"], data["world_state"])

    def tick(self, time, world_state: dict) -> list[str]:
        logs = []
        logs.extend(self._simulate_world(time, world_state))
        logs.extend(self._process_yearly_events(time, world_state))
        return logs

    def _process_yearly_events(self, time, world_state: dict) -> list[str]:
        """Xử lý các sự kiện theo năm."""
        logs = []
        for event in self.events.values():
            if event["id"] in world_state["events_fired"]:
                continue
            if time.year < int(event["trigger_year"]):
                continue
            if time.year == int(event["trigger_year"]) and time.month < int(event["trigger_month"]):
                continue

            world_state["events_fired"].append(event["id"])
            self._apply_event(world_state, event)
            logs.append(f"{event['name_vn']}: {event['description']}")
        return logs

    def get_available_secret_realms(self, player: dict) -> list[dict]:
        player_level = self.tech.get_realm_index(player["realm_id"])
        return [
            realm for realm in self.secret_realms.values()
            if self.tech.get_realm_index(realm["min_realm"]) <= player_level
        ]

    def get_available_quests(self, world_state: dict) -> list[dict]:
        sect_id = world_state.get("player_sect")
        if not sect_id:
            return []
        return [q for q in self.sect_quests.values() if q["sect_id"] == sect_id]

    def complete_quest(self, player: dict, world_state: dict, quest_id: str) -> tuple[bool, str]:
        quest = self.sect_quests.get(quest_id)
        if not quest or quest["sect_id"] != world_state.get("player_sect"):
            return False, "Không có nhiệm vụ phù hợp."
        qtype = quest["type"]
        required = int(quest["required_qty"])
        if qtype == "item":
            inv = player.setdefault("inventory", {})
            item_id = quest["target_id"]
            if inv.get(item_id, 0) < required:
                return False, "Chưa đủ vật phẩm nhiệm vụ."
            inv[item_id] -= required
            if inv[item_id] <= 0:
                del inv[item_id]
        elif qtype == "combat_win":
            if world_state.get("combat_wins", 0) < required:
                return False, "Chưa đủ số trận thắng."
            world_state["combat_wins"] -= required
        world_state["sect_contrib"] = world_state.get("sect_contrib", 0) + 1
        sect_id = world_state["player_sect"]
        world_state["sect_power"][sect_id] = self._clamp_power(
            world_state["sect_power"].get(sect_id, 50) + int(quest["reward_power"])
        )
        if world_state.get("player_rank", 0) < 3:
            world_state["player_rank"] += int(quest["reward_rank"])
            world_state["player_rank"] = min(3, world_state["player_rank"])
        reward_item = quest.get("reward_item", "")
        if reward_item:
            inv = player.setdefault("inventory", {})
            inv[reward_item] = inv.get(reward_item, 0) + 1
        return True, f"Hoàn thành {quest['name_vn']}."

    def get_available_sects(self, player: dict) -> list[dict]:
        player_level = self.tech.get_realm_index(player["realm_id"])
        return [
            sect for sect in self.sects.values()
            if self.tech.get_realm_index(sect["min_realm"]) <= player_level
        ]

    def join_sect(self, player: dict, world_state: dict, sect_id: str) -> bool:
        if sect_id not in self.sects:
            return False
        if world_state.get("player_sect"):
            return False
        if self.sects[sect_id] not in self.get_available_sects(player):
            return False

        world_state["player_sect"] = sect_id
        world_state["player_rank"] = 1
        return True

    def leave_sect(self, player: dict, world_state: dict) -> bool:
        if not world_state.get("player_sect"):
            return False
        world_state["player_sect"] = None
        world_state["player_rank"] = 0
        return True

    def get_sect_techniques(self, sect_id: str, player_rank: int) -> list[str]:
        return [
            row["technique_id"]
            for row in self.sect_techniques
            if row["sect_id"] == sect_id and int(row["rank_required"]) <= player_rank
        ]

    def promote_player(self, world_state: dict) -> bool:
        if not world_state.get("player_sect"):
            return False
        if world_state.get("player_rank", 0) >= 3:
            return False
        world_state["player_rank"] += 1
        sect_id = world_state["player_sect"]
        world_state["sect_power"][sect_id] = min(100, world_state["sect_power"].get(sect_id, 50) + 5)
        return True

    def _apply_event(self, world_state: dict, event: dict):
        effect_type = event["effect_type"]
        value = int(event["effect_value"])
        faction = event["affected_faction"]

        if effect_type == "sect_power":
            for sect_id, sect in self.sects.items():
                if sect["faction"] == faction:
                    world_state["sect_power"][sect_id] = self._clamp_power(
                        world_state["sect_power"].get(sect_id, 50) + value
                    )
        elif effect_type in ("resource_bonus", "realm_open"):
            for sect_id in world_state["sect_power"]:
                world_state["sect_power"][sect_id] = self._clamp_power(
                    world_state["sect_power"][sect_id] + max(1, value // 5)
                )
        elif effect_type == "war":
            for sect_id, sect in self.sects.items():
                if sect["faction"] == faction:
                    world_state["sect_power"][sect_id] = self._clamp_power(
                        world_state["sect_power"].get(sect_id, 50) + value
                    )

    @staticmethod
    def _clamp_power(value: int) -> int:
        return max(0, min(100, value))

    def _simulate_world(self, time, world_state: dict) -> list[str]:
        if world_state.get("sim_year", 0) >= time.year:
            return []
        world_state["sim_year"] = time.year
        logs = []

        # Sect power simulation
        for sect_id, sect in self.sects.items():
            base_drift = 1 if sect["faction"] == "human" else 2
            if sect["faction"] == "mo":
                base_drift = -1

            # Random variance
            random_factor = random.randint(-2, 2)
            total_drift = base_drift + random_factor

            old_power = world_state["sect_power"].get(sect_id, 50)
            new_power = self._clamp_power(old_power + total_drift)
            world_state["sect_power"][sect_id] = new_power

            # Check thresholds and fire events
            threshold_event = self._check_sect_threshold(sect_id, sect, old_power, new_power, world_state)
            if threshold_event:
                logs.append(threshold_event)

        if time.year > 1:
            logs.append("Các tông môn âm thầm dịch chuyển thế lực trong năm mới.")
            logs.append("Một số NPC đồng môn đã tích lũy thêm công trạng và danh vọng.")
        return logs

    def _check_sect_threshold(self, sect_id: str, sect: dict, old_power: int, new_power: int, world_state: dict) -> str | None:
        """Kiểm tra ngưỡng thế lực tông môn."""
        event_key = f"sect_threshold_{sect_id}_{new_power}"

        # Đã đạt ngưỡng cực yếu - tông môn suy vong
        if new_power < 20 and old_power >= 20:
            return f"{sect['name_vn']} đang suy vong, không còn nhận đệ tử mới."

        # Đạt ngưỡng cực mạnh - tông môn cường thịnh
        elif new_power > 80 and old_power <= 80:
            return f"{sect['name_vn']} đạt đỉnh thịnh, mở thêm nhiều nhiệm vụ hệ cao."

        # Tông môn giải thể
        elif new_power == 0:
            return f"{sect['name_vn']} đã giải thể, các đệ tử tản mát."

        return None
