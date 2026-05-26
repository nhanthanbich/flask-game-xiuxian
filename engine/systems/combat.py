"""
Turn-based combat system.
"""

import random

from engine.core.loader import Loader
from engine.systems.technique import TechniqueSystem, REALM_ORDER
from engine.systems.race import RaceSystem

ENEMIES_PATH = "data/entities/enemies.csv"
ROOTS_PATH = "data/entities/spiritual_roots.csv"

ELEMENT_STRONG = {
    "Kim": "Moc",
    "Moc": "Tho",
    "Thuy": "Hoa",
    "Hoa": "Kim",
    "Tho": "Thuy",
}


class CombatSystem:
    def __init__(self, settings: dict | None = None):
        self.settings = settings or Loader.load_settings()
        self.tech = TechniqueSystem()
        self.races = RaceSystem()
        self.enemies = Loader.load_by_id(ENEMIES_PATH)
        self.roots = Loader.load_by_id(ROOTS_PATH)

    def get_realm_index(self, realm_id: str) -> int:
        """Get realm index with safe fallback for new realm IDs."""
        try:
            return REALM_ORDER.index(realm_id)
        except ValueError:
            # Fallback: try to find by base realm name
            base_realm = realm_id.rsplit('_', 1)[0] if '_' in realm_id else realm_id
            for idx, r_id in enumerate(REALM_ORDER):
                if r_id == base_realm or r_id.startswith(base_realm):
                    return idx
            # Return lowest level if not found
            return 0

    def spawn_player_combat(self, player: dict) -> dict:
        # Get stats for current realm, with fallback logic
        stats = self.settings["realm_stats"].get(player["realm_id"])

        # If not found, try base realm name (e.g., "qi_refining" for "qi_refining_2")
        if stats is None:
            base_realm = player["realm_id"].rsplit('_', 1)[0]
            stats = self.settings["realm_stats"].get(base_realm)

        # Final fallback to qi_refining_1 or first available
        if stats is None:
            stats = self.settings["realm_stats"].get("qi_refining_1") or \
                    self.settings["realm_stats"].get("qi_refining") or \
                    next(iter(self.settings["realm_stats"].values()))

        root = self.roots.get(player.get("root_id"), {})
        race_mult = self.races.stat_mults(player.get("race_id", "human"))
        hp = int(int(stats["hp"]) * race_mult["hp"]) + int(player.get("hp_bonus", 0))
        mp = int(int(stats["mp"]) * race_mult["mp"]) + int(player.get("mp_bonus", 0))
        attack = int(int(stats["attack"]) * race_mult["attack"]) + int(player.get("stat_bonus", 0))
        return {
            "hp": hp,
            "hp_max": hp,
            "mp": mp,
            "mp_max": mp,
            "attack": attack,
            "element": root.get("element", "Vo"),
            "def_buff": 0,
        }

    def spawn_enemy(self, enemy_id: str) -> dict:
        enemy = self.enemies[enemy_id]
        difficulty = float(self.settings.get("combat_difficulty", 1.0))
        hp = int(int(enemy["hp"]) * difficulty)
        mp = int(enemy.get("mp") or 0)
        return {
            "id": enemy["id"],
            "name": enemy["name_vn"],
            "realm_id": enemy["realm_id"],
            "element": enemy["element"],
            "hp": hp,
            "hp_max": hp,
            "mp": mp,
            "mp_max": mp,
            "attack": int(int(enemy.get("atk") or enemy.get("attack") or 0) * difficulty),
            "defense": int(enemy.get("def") or 0),
            "exp": int(enemy.get("exp_reward") or enemy.get("exp") or 0),
            "skill_ids": [s for s in enemy.get("skill_ids", "").split("|") if s],
            "drop_technique_id": enemy.get("drop_technique_id", ""),
            "dot": 0,
            "stunned": False,
        }

    def player_turn(self, technique_id: str, player_state: dict, enemy_state: dict) -> list[str]:
        tech = self.tech.techniques[technique_id]
        return self._use_technique(
            tech,
            player_state,
            enemy_state,
            attacker_name=tech["name_vn"],
            root_element=player_state["element"],
            target_element=enemy_state["element"],
            target_defense=enemy_state.get("defense", 0),
        )

    def enemy_turn(self, enemy_state: dict, player_state: dict) -> list[str]:
        return self.enemy_skill_turn(enemy_state, player_state, self.tech.techniques)

    def enemy_skill_turn(self, enemy_state: dict, player_state: dict, techniques: dict) -> list[str]:
        logs = self._apply_dot(enemy_state)
        if enemy_state["hp"] <= 0:
            return logs
        if enemy_state.get("stunned"):
            enemy_state["stunned"] = False
            logs.append("Doi thu bi choang nen mat luot.")
            return logs

        usable = [
            techniques[tid] for tid in enemy_state.get("skill_ids", [])
            if tid in techniques and enemy_state["mp"] >= int(techniques[tid]["mp_cost"])
        ]
        if usable:
            tech = random.choice(usable)
            logs.extend(self._use_technique(
                tech,
                enemy_state,
                player_state,
                attacker_name=f"{enemy_state['name']} dung {tech['name_vn']}",
                root_element=enemy_state["element"],
                target_element=player_state["element"],
                target_defense=player_state.get("def_buff", 0),
            ))
            player_state["def_buff"] = 0
            return logs

        damage = max(1, enemy_state["attack"] - player_state.get("def_buff", 0))
        damage = self._apply_element_mult(damage, enemy_state["element"], player_state["element"])
        player_state["hp"] = max(0, player_state["hp"] - damage)
        player_state["def_buff"] = 0
        self._regen_mp(enemy_state)
        logs.append(f"{enemy_state['name']} phan cong, gay {damage} sat thuong.")
        return logs

    def calc_drop(self, enemy_data: dict) -> str | None:
        drop_id = enemy_data.get("drop_technique_id", "")
        if not drop_id:
            return None
        chance = float(self.settings["technique_drop_chance"]) * float(self.settings["drop_rate"])
        return drop_id if random.random() < chance else None

    @staticmethod
    def is_over(player_state: dict, enemy_state: dict) -> str | None:
        if enemy_state["hp"] <= 0:
            return "win"
        if player_state["hp"] <= 0:
            return "lose"
        return None

    def _use_technique(
        self,
        tech: dict,
        attacker: dict,
        target: dict,
        attacker_name: str,
        root_element: str,
        target_element: str,
        target_defense: int = 0,
    ) -> list[str]:
        mp_cost = int(tech["mp_cost"])
        if attacker["mp"] < mp_cost:
            self._regen_mp(attacker)
            return [f"{attacker_name} khong du MP va hoi phuc linh luc."]

        attacker["mp"] -= mp_cost
        hits = self._effect_hits(tech)
        total = 0
        for _ in range(hits):
            base = max(1, int(tech["power"]) + attacker["attack"] - target_defense)
            base = self._apply_root_technique_rules(base, root_element, tech["element"])
            base = self._apply_element_mult(base, tech["element"], target_element)
            base = int(base * float(tech.get("element_bonus_mult") or 1.0))
            target["hp"] = max(0, target["hp"] - base)
            total += base

        logs = [f"{attacker_name} gay {total} sat thuong."]
        self._apply_effect(tech, attacker, target, total, logs)
        self._regen_mp(attacker)
        return logs

    def _apply_effect(self, tech: dict, attacker: dict, target: dict, damage: int, logs: list[str]):
        effect = tech.get("effect", "none")
        value = int(tech.get("effect_value") or 0)
        if effect == "heal":
            healed = max(value, damage // 3)
            attacker["hp"] = min(attacker["hp_max"], attacker["hp"] + healed)
            logs.append(f"Hoi phuc {healed} HP.")
        elif effect == "full_heal":
            healed = attacker["hp_max"] - attacker["hp"]
            attacker["hp"] = attacker["hp_max"]
            logs.append(f"Hoi phuc toan bo HP (+{healed}).")
        elif effect == "guard":
            attacker["def_buff"] = max(attacker.get("def_buff", 0), value)
            logs.append("Phong thu tang trong luot ke tiep.")
        elif effect == "stun" and damage >= int(tech["power"]):
            target["stunned"] = True
            logs.append("Doi thu bi choang.")
        elif effect == "dot":
            target["dot"] = max(target.get("dot", 0), value)
            logs.append("Hoa luc tiep tuc thieu dot doi thu.")
        elif effect == "mp_burn":
            target["mp"] = max(0, target.get("mp", 0) - value)
            logs.append(f"Linh luc doi thu bi rut {value} MP.")

    def _apply_dot(self, target: dict) -> list[str]:
        if not target.get("dot"):
            return []
        dot = target["dot"]
        target["hp"] = max(0, target["hp"] - dot)
        target["dot"] = max(0, dot - 2)
        return [f"{target['name']} chiu {dot} sat thuong thieu dot."]

    def _regen_mp(self, state: dict):
        regen = max(1, int(state["mp_max"] * float(self.settings["mp_regen_rate"])))
        state["mp"] = min(state["mp_max"], state["mp"] + regen)

    def _apply_element_mult(self, damage: int, attack_element: str, defend_element: str) -> int:
        if ELEMENT_STRONG.get(attack_element) == defend_element:
            return int(damage * float(self.settings["element_bonus_mult"]))
        if ELEMENT_STRONG.get(defend_element) == attack_element:
            return int(damage * float(self.settings["element_penalty_mult"]))
        return damage

    def _apply_root_technique_rules(self, damage: int, root_element: str, technique_element: str) -> int:
        if technique_element == root_element:
            return int(damage * float(self.settings["same_root_technique_bonus"]))
        if ELEMENT_STRONG.get(technique_element) == root_element:
            return int(damage * float(self.settings["countered_root_technique_penalty"]))
        return damage

    @staticmethod
    def _effect_hits(tech: dict) -> int:
        if tech.get("effect") == "multi_hit":
            return max(1, int(tech.get("effect_value") or 1))
        return 1
