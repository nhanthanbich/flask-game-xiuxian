"""
Secret Realm System - Bí Cảnh.

Bí cảnh là "khu vực nguy hiểm tạm thời" có loot + exp + rủi ro.
Vào/ra tự do, không lock time.
"""

import random
from engine.core.loader import Loader

SECRET_REALMS_PATH = "data/entities/secret_realms.csv"


class SecretRealmSystem:
    def __init__(self):
        self.realms = Loader.load_by_id(SECRET_REALMS_PATH)

    def check_requirement(self, player: dict, realm_id: str) -> tuple[bool, str]:
        """
        Check if player can enter a secret realm.
        Returns (can_enter, reason_if_not).
        """
        realm = self.realms.get(realm_id)
        if not realm:
            return False, "Bí cảnh không tồn tại."

        requirement = realm.get("requirement", "")
        if not requirement or requirement == "always":
            return True, ""

        # Parse requirement - supports OR conditions
        # Format: "realm_level >= X" or "race == mo or corruption >= 30"
        try:
            # Check for OR conditions
            if " or " in requirement:
                # Split by " or " and check each condition
                conditions = [c.strip() for c in requirement.split(" or ")]
                passed_any = False
                reasons = []

                for cond in conditions:
                    passed, reason = self._check_single_requirement(player, cond)
                    if passed:
                        passed_any = True
                        break
                    else:
                        reasons.append(reason)

                if not passed_any:
                    return False, " hoặc ".join(reasons)

                return True, ""
            else:
                # Single condition
                return self._check_single_requirement(player, requirement)

        except Exception as e:
            # If parsing fails, allow entry
            return True, ""

    def _check_single_requirement(self, player: dict, requirement: str) -> tuple[bool, str]:
        """Check a single requirement condition."""
        # Check realm level
        if "realm_level >=" in requirement:
            required_level = int(requirement.split(">=")[1].strip())
            player_level = self._get_player_realm_level(player)
            if player_level < required_level:
                return False, f"Cần cảnh giới level ≥ {required_level} (hiện tại: {player_level})."

        # Check race
        if "race ==" in requirement:
            required_race = requirement.split("==")[1].strip()
            player_race = player.get("race_id", "human")
            if player_race != required_race:
                return False, f"Cần chủng tộc: {required_race}."

        # Check corruption
        if "corruption >=" in requirement:
            required_corruption = int(requirement.split(">=")[1].strip())
            player_corruption = player.get("demonic_corruption", 0)
            if player_corruption < required_corruption:
                return False, f"Cần ô nhiễm tà đạo ≥ {required_corruption}% (hiện tại: {player_corruption}%)."

        return True, ""

    def _get_player_realm_level(self, player: dict) -> int:
        """Get numeric realm level from realm_id."""
        from engine.systems.technique import REALM_ORDER
        realm_id = player.get("realm_id", "mortal")
        try:
            return REALM_ORDER.index(realm_id)
        except (ValueError, NameError):
            return 0

    def enter_realm(self, player: dict, realm_id: str) -> dict:
        """
        Player enters a secret realm.
        Returns info about entry (time cost, enemies, etc).
        """
        realm = self.realms.get(realm_id)
        if not realm:
            return {"success": False, "message": "Bí cảnh không tồn tại."}

        can_enter, reason = self.check_requirement(player, realm_id)
        if not can_enter:
            return {"success": False, "message": reason}

        time_cost = int(realm.get("time_cost_days", 3))
        enemy_strength = realm.get("enemy_strength", "weak")
        difficulty = int(realm.get("difficulty", 1))

        # Generate enemies based on difficulty
        enemy_count = difficulty + random.randint(0, 1)
        enemies = self._generate_realm_enemies(realm, enemy_count)

        return {
            "success": True,
            "realm": realm,
            "time_cost_days": time_cost,
            "enemies": enemies,
            "event_text": realm.get("event_text", ""),
            "difficulty": difficulty,
        }

    def _generate_realm_enemies(self, realm: dict, count: int) -> list:
        """Generate enemies for secret realm based on strength."""
        strength = realm.get("enemy_strength", "weak")

        # Base enemy types by strength
        enemy_types = {
            "weak": ["forest_wolf", "marsh_rat"],
            "medium": ["rogue_thief", "bone_vulture"],
            "hard": ["cult_fanatic", "tomb_guardian"],
            "extreme": ["demon_spawn", "corrupted_elder"],
        }

        available = enemy_types.get(strength, enemy_types["weak"])
        enemies = []

        for i in range(count):
            enemy_id = random.choice(available)
            enemies.append({
                "id": f"{enemy_id}_{i}",
                "base_id": enemy_id,
                "strength_multiplier": 1.0 + (0.1 * int(realm.get("difficulty", 1))),
            })

        return enemies

    def complete_realm(self, player: dict, realm_id: str, victory: bool) -> dict:
        """
        Called when player completes a secret realm (win or lose).
        Returns rewards on victory, penalties on defeat.
        """
        realm = self.realms.get(realm_id)
        if not realm:
            return {"success": False, "message": "Bí cảnh không tồn tại."}

        if victory:
            # Victory rewards
            loot_items = realm.get("loot_items", "").split("+")
            exp_reward = int(realm.get("exp_reward", 0))
            corruption_reward = int(realm.get("corruption_reward", 0))

            # Check if first clear
            cleared_realms = player.get("secret_realms_cleared", [])
            first_clear = realm_id not in cleared_realms

            if first_clear:
                # Full rewards on first clear
                player["secret_realms_cleared"] = cleared_realms + [realm_id]
                loot_message = f"Loot đầy đủ: {', '.join(loot_items)}"
            else:
                # 50% loot on repeated clears, but full exp/corruption
                loot_items = loot_items[:max(1, len(loot_items) // 2)]
                loot_message = f"Loot (50%): {', '.join(loot_items)}"

            # Add corruption if rewarded
            if corruption_reward > 0:
                current_corruption = player.get("demonic_corruption", 0)
                player["demonic_corruption"] = min(100, current_corruption + corruption_reward)

            return {
                "success": True,
                "victory": True,
                "exp_gained": exp_reward,
                "corruption_gained": corruption_reward,
                "loot": loot_items,
                "message": f"Thắng! {loot_message}. Nhận {exp_reward} exp.",
                "event_text": realm.get("event_text", ""),
            }

        else:
            # Defeat penalties
            hp_loss_percent = random.randint(30, 50)
            corruption_increase = 5

            # Add corruption
            current_corruption = player.get("demonic_corruption", 0)
            player["demonic_corruption"] = min(100, current_corruption + corruption_increase)

            return {
                "success": True,
                "victory": False,
                "hp_loss_percent": hp_loss_percent,
                "corruption_gained": corruption_increase,
                "message": f"Thất bại! Mất {hp_loss_percent}% HP, bị đuổi ra. Ô nhiễm tà đạo +{corruption_increase}%.",
                "time_lost_days": 1,
            }
