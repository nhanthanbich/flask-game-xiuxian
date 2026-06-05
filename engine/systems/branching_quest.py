"""
Branching Quest System - Quest có nhánh lựa chọn dẫn đến kết quả khác nhau.

Không sửa quest hiện tại, chỉ thêm quest mới có branch.
"""

import random
from engine.core.loader import Loader
from engine.systems.npc import NPCSystem

BRANCHING_QUESTS_PATH = "data/quests_branching.csv"
QUEST_BRANCHES_PATH = "data/quest_branches.csv"


class BranchingQuestSystem:
    def __init__(self):
        self.quests = Loader.load_by_id(BRANCHING_QUESTS_PATH)
        self.branches = self._load_branches()

    def _load_branches(self) -> dict:
        """Load all quest branches organized by quest_id."""
        branches_raw = Loader.load_by_id(QUEST_BRANCHES_PATH)
        branches = {}

        for branch_id, branch_data in branches_raw.items():
            quest_id = branch_data.get("quest_id")
            if quest_id not in branches:
                branches[quest_id] = []
            branches[quest_id].append(branch_data)

        return branches

    def get_quest(self, quest_id: str) -> dict | None:
        """Get quest data by ID."""
        return self.quests.get(quest_id)

    def get_quest_branches(self, quest_id: str) -> list:
        """Get all branches for a quest."""
        return self.branches.get(quest_id, [])

    def check_requirement(self, player: dict, world_state: dict, quest_id: str) -> tuple[bool, str]:
        """
        Check if player can start a branching quest.
        Returns (can_start, reason_if_not).
        """
        quest = self.quests.get(quest_id)
        if not quest:
            return False, "Quest không tồn tại."

        requirement = quest.get("requirement", "")
        if not requirement:
            return True, ""

        # Parse requirement
        # Format: "relationship_npc_id >= 30" or "reputation >= 50" or "faction == thanh_van"
        try:
            if "relationship_" in requirement:
                # Extract NPC ID
                parts = requirement.split("relationship_")[1].split(" ")
                npc_key = parts[0]
                operator = parts[1] if len(parts) > 1 else ">="
                required_value = int(parts[2]) if len(parts) > 2 else 0

                # Get relationship from world_state
                relationships = world_state.get("relationships", {})
                player_rel = relationships.get(npc_key, 0)

                if operator == ">=" and player_rel < required_value:
                    return False, f"Cần quan hệ với {npc_key} ≥ {required_value} (hiện tại: {player_rel})."

            if "reputation >=" in requirement:
                required_rep = int(requirement.split(">=")[1].strip())
                player_rep = player.get("reputation", 0)
                if player_rep < required_rep:
                    return False, f"Cần thanh thế ≥ {required_rep} (hiện tại: {player_rep})."

            if "faction ==" in requirement:
                required_faction = requirement.split("==")[1].strip()
                player_faction = world_state.get("player_sect", "")
                if player_faction != required_faction:
                    return False, f"Cần gia nhập tông môn: {required_faction}."

            if "sect_contribution >=" in requirement:
                required_contrib = int(requirement.split(">=")[1].strip())
                player_contrib = world_state.get("sect_contribution", 0)
                if player_contrib < required_contrib:
                    return False, f"Cần công trạng tông môn ≥ {required_contrib} (hiện tại: {player_contrib})."

        except Exception as e:
            # If parsing fails, allow quest
            pass

        return True, ""

    def start_quest(self, player: dict, world_state: dict, quest_id: str) -> dict:
        """
        Start a branching quest.
        Returns quest info and available branches for player to choose.
        """
        quest = self.quests.get(quest_id)
        if not quest:
            return {"success": False, "message": "Quest không tồn tại."}

        can_start, reason = self.check_requirement(player, world_state, quest_id)
        if not can_start:
            return {"success": False, "message": reason}

        # Get available branches
        branches = self.get_quest_branches(quest_id)

        # Filter out END branches (only show initial choices)
        initial_branches = [
            b for b in branches
            if not b.get("branch_id", "").endswith("_END") and not b.get("branch_id", "").endswith("_ENDING")
        ]

        return {
            "success": True,
            "quest": quest,
            "branches": initial_branches,
            "message": f"Nhận quest: {quest.get('name_vn', quest_id)}",
        }

    def choose_branch(self, player: dict, world_state: dict, quest_id: str, branch_id: str) -> dict:
        """
        Player chooses a branch.
        Saves choice and returns branch consequences.
        """
        # Save choice
        if "quest_branch_flags" not in player:
            player["quest_branch_flags"] = {}

        player["quest_branch_flags"][quest_id] = branch_id

        # Get branch data
        branches = self.get_quest_branches(quest_id)
        branch_data = None
        for b in branches:
            if b.get("branch_id") == branch_id:
                branch_data = b
                break

        if not branch_data:
            return {"success": False, "message": "Branch không tồn tại."}

        return {
            "success": True,
            "branch": branch_data,
            "message": f"Đã chọn: {branch_data.get('choice_text', branch_id)}",
        }

    def complete_branch(self, player: dict, world_state: dict, quest_id: str, branch_id: str) -> dict:
        """
        Complete a branch and apply rewards/consequences.
        Returns next branch if exists, or marks quest as complete.
        """
        branches = self.get_quest_branches(quest_id)
        branch_data = None
        for b in branches:
            if b.get("branch_id") == branch_id:
                branch_data = b
                break

        if not branch_data:
            return {"success": False, "message": "Branch không tồn tại."}

        # Apply rewards
        reward_result = self._apply_rewards(player, branch_data)

        # Apply NPC relationship changes
        npc_changes = self._apply_npc_relationship_changes(world_state, branch_data)

        # Trigger world event if any
        world_event = branch_data.get("world_event_trigger", "none")
        if world_event and world_event != "none":
            self._trigger_world_event(world_state, world_event)

        # Save consequence
        if "quest_consequences" not in player:
            player["quest_consequences"] = {}
        player["quest_consequences"][branch_id] = {
            "rewards": reward_result,
            "npc_changes": npc_changes,
            "world_event": world_event,
        }

        # Check for sequential branch
        next_branch_id = branch_data.get("next_branch")
        if next_branch_id and next_branch_id != "none":
            # Get next branch data
            next_branch_data = None
            for b in branches:
                if b.get("branch_id") == next_branch_id:
                    next_branch_data = b
                    break

            if next_branch_data:
                return {
                    "success": True,
                    "branch_complete": True,
                    "next_branch": next_branch_data,
                    "message": f"Branch hoàn thành. Tiếp tục: {next_branch_data.get('choice_text', next_branch_id)}",
                }

        # Mark quest as complete
        if "completed_branch_quests" not in player:
            player["completed_branch_quests"] = []
        if quest_id not in player["completed_branch_quests"]:
            player["completed_branch_quests"].append(quest_id)

        return {
            "success": True,
            "branch_complete": True,
            "quest_complete": True,
            "message": f"Quest hoàn thành: {quest_id}",
            "rewards": reward_result,
            "npc_changes": npc_changes,
            "world_event": world_event,
        }

    def _apply_rewards(self, player: dict, branch_data: dict) -> dict:
        """Apply rewards from branch to player."""
        reward_type = branch_data.get("reward_type", "")
        reward_value = branch_data.get("reward_value", "")

        if not reward_type or reward_type == "none":
            return {"applied": False}

        rewards = {}
        types = reward_type.split("|")
        values = reward_value.split("|")

        for i, rtype in enumerate(types):
            value = values[i] if i < len(values) else "0"

            if rtype == "exp":
                exp_gain = int(value)
                player["exp"] = player.get("exp", 0) + exp_gain
                rewards["exp"] = exp_gain

            elif rtype == "gold":
                gold_gain = int(value)
                inventory = player.get("inventory", {})
                inventory["gold"] = inventory.get("gold", 0) + gold_gain
                rewards["gold"] = gold_gain

            elif rtype == "corruption":
                corruption_gain = int(value)
                player["demonic_corruption"] = min(100, player.get("demonic_corruption", 0) + corruption_gain)
                rewards["corruption"] = corruption_gain

            elif rtype == "reputation":
                rep_gain = int(value)
                player["reputation"] = player.get("reputation", 0) + rep_gain
                rewards["reputation"] = rep_gain

            elif rtype == "item":
                # Add item to inventory
                inventory = player.get("inventory", {})
                inventory[value] = inventory.get(value, 0) + 1
                rewards["item"] = value

            elif rtype == "faction_contribution":
                contrib_gain = int(value)
                # Add to world_state
                # Will be handled by caller
                rewards["faction_contribution"] = contrib_gain

        return rewards

    def _apply_npc_relationship_changes(self, world_state: dict, branch_data: dict) -> dict:
        """Apply NPC relationship changes from branch."""
        npc_changes_str = branch_data.get("npc_relationship_change", "")
        if not npc_changes_str or npc_changes_str == "none":
            return {}

        changes = {}
        relationships = world_state.setdefault("relationships", {})

        # Parse: "npc1:+20|npc2:-30"
        parts = npc_changes_str.split("|")
        for part in parts:
            if ":" in part:
                npc_id, change = part.split(":")
                change_value = int(change)
                current = relationships.get(npc_id, 0)
                relationships[npc_id] = current + change_value
                changes[npc_id] = change_value

        return changes

    def _trigger_world_event(self, world_state: dict, event_id: str):
        """Trigger a world event from quest branch."""
        world_events = world_state.setdefault("quest_world_events", [])
        world_events.append({
            "event_id": event_id,
            "triggered": True,
        })

        # Apply event effects
        if event_id == "sect_power_shift":
            # Shift sect power
            world_state["sect_power"] = world_state.get("sect_power", 100) - 10

        elif event_id == "sect_harmony":
            # Increase harmony
            world_state["sect_harmony"] = world_state.get("sect_harmony", 50) + 20

        elif event_id == "sect_conflict" or event_id == "sect_schism":
            # Decrease harmony
            world_state["sect_harmony"] = max(0, world_state.get("sect_harmony", 50) - 30)

        elif event_id == "sect_split":
            # Major split
            world_state["sect_unified"] = False

    def is_quest_completed(self, player: dict, quest_id: str) -> bool:
        """Check if a branching quest has been completed."""
        return quest_id in player.get("completed_branch_quests", [])

    def get_available_quests(self, player: dict, world_state: dict) -> list:
        """Get list of available branching quests for player."""
        available = []

        for quest_id, quest in self.quests.items():
            if self.is_quest_completed(player, quest_id):
                continue

            can_start, _ = self.check_requirement(player, world_state, quest_id)
            if can_start:
                available.append(quest)

        return available

    def check_unlock_condition(self, player: dict, condition: str) -> bool:
        """
        Check if a quest unlock condition is met.
        Format: "QB003_B1_chosen"
        """
        if "_chosen" in condition:
            branch_id = condition.replace("_chosen", "")
            # Check if player chose this branch
            quest_id = branch_id.rsplit("_B", 1)[0]
            chosen_branch = player.get("quest_branch_flags", {}).get(quest_id)
            return chosen_branch == branch_id

        return False
