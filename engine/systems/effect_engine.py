"""
Effect Engine - Data-driven skill effect system
Supports: damage, heal, buff, debuff, dot, cc, life_steal, utility
"""

import random
from typing import Dict, Any, List, Tuple


class EffectEngine:
    """Resolves and applies effects from skill data"""

    def __init__(self):
        self.active_buffs = {}  # player_id -> {stat: [buff_objects]}
        self.active_debuffs = {}
        self.active_dots = {}  # player_id -> [dot_objects]
        self.active_ccs = {}  # player_id -> [cc_objects]

    def apply_effect(self, caster: Dict, target: Dict,
                     effect_data: Dict,
                     combat_context: Dict) -> Tuple[str, int]:
        """
        Apply single effect and return (message, damage_dealt)

        Args:
            caster: Attacker player/enemy state
            target: Defender player/enemy state
            effect_data: Effect configuration from CSV
            combat_context: Combat state (turn, etc)

        Returns:
            (result_message, damage_dealt)
        """
        effect_type = effect_data.get("type", "damage")

        if effect_type == "damage":
            return self._apply_damage(caster, target, effect_data)
        elif effect_type == "heal":
            return self._apply_heal(caster, target, effect_data)
        elif effect_type == "buff":
            return self._apply_buff(target, effect_data)
        elif effect_type == "debuff":
            return self._apply_debuff(target, effect_data)
        elif effect_type == "dot":
            return self._apply_dot(target, effect_data)
        elif effect_type == "cc":
            return self._apply_cc(target, effect_data)
        elif effect_type == "life_steal":
            return self._apply_life_steal(caster, target, effect_data)
        elif effect_type == "utility":
            return self._apply_utility(target, effect_data)
        else:
            return f"Loại hiệu ứng không xác định: {effect_type}", 0

    def _apply_damage(self, caster: Dict, target: Dict,
                      effect_data: Dict) -> Tuple[str, int]:
        """Apply damage effect"""
        damage = self._calculate_damage(caster, target, effect_data)

        # Check critical hit
        crit_chance = effect_data.get("crit_chance", 0.0)
        is_crit = random.random() < crit_chance

        if is_crit:
            damage = int(damage * 1.5)
            msg = f"Chí mạng! Tấn công {damage} damage ({effect_data.get('element', 'none')})"
        else:
            msg = f"Tấn công {damage} damage ({effect_data.get('element', 'none')})"

        # Apply damage
        target["hp"] = max(0, target.get("hp", 0) - damage)

        return msg, damage

    def _calculate_damage(self, caster: Dict, target: Dict,
                         effect_data: Dict) -> int:
        """Calculate damage with scaling"""
        base_value = effect_data.get("value", 0)
        scaling = effect_data.get("scaling", "att")

        # Get caster stats
        caster_att = caster.get("attack", 10)
        caster_qi = caster.get("qi", 10)
        caster_realm_idx = caster.get("realm_index", 0)

        # Get target defense
        target_def = target.get("defense", 5)
        target_qi = target.get("qi", 10)

        # Calculate damage based on scaling
        if scaling == "att":
            damage = int(base_value * caster_att / 100)
        elif scaling == "qi":
            damage = int(base_value * caster_qi / 100)
        elif scaling == "realm":
            damage = int(base_value * (caster_realm_idx + 1) / 2)
        elif scaling == "hybrid":
            damage = int(base_value * (caster_att + caster_qi) / 200)
        else:
            damage = base_value

        # Apply defense reduction
        defense_reduction = int(target_def * 0.3)  # 30% damage reduction
        damage = max(1, damage - defense_reduction)

        return damage

    def _apply_heal(self, caster: Dict, target: Dict,
                   effect_data: Dict) -> Tuple[str, int]:
        """Apply healing effect"""
        heal_type = effect_data.get("target", "self")
        base_value = effect_data.get("value", 0)
        scaling = effect_data.get("scaling", "qi")

        # Calculate heal amount
        if scaling == "qi":
            heal = int(base_value * caster.get("qi", 10) / 100)
        else:
            heal = int(base_value * caster.get("attack", 10) / 100)

        # Apply heal
        target_hp_max = target.get("hp_max", 100)
        target["hp"] = min(target_hp_max, target.get("hp", 0) + heal)

        return f"Chữa {heal} HP cho {target.get('name', 'đồng minh')}", heal

    def _apply_buff(self, target: Dict,
                   effect_data: Dict) -> Tuple[str, int]:
        """Apply buff effect"""
        stat = effect_data.get("stat", "att")
        value = effect_data.get("value", 0)
        duration = effect_data.get("duration", 1)

        target_id = id(target)
        if target_id not in self.active_buffs:
            self.active_buffs[target_id] = {}

        buff = {
            "stat": stat,
            "value": value,
            "duration_left": duration,
            "duration_max": duration
        }

        if stat not in self.active_buffs[target_id]:
            self.active_buffs[target_id][stat] = []

        self.active_buffs[target_id][stat].append(buff)

        return f"Tăng {stat} +{value}% trong {duration} lượt", 0

    def _apply_debuff(self, target: Dict,
                     effect_data: Dict) -> Tuple[str, int]:
        """Apply debuff effect with resistance check"""
        effect = effect_data.get("effect", "weaken")
        duration = effect_data.get("duration", 1)
        resist_check = effect_data.get("resist_check", True)
        success_chance = effect_data.get("success_chance", 1.0)

        # Check if target resists
        if resist_check:
            target_resist = target.get("resistance", 0)
            effective_chance = max(0.0, success_chance - target_resist / 100)
            if random.random() > effective_chance:
                return f"{target.get('name', 'Đối phương')} chống cự debuff thành công", 0

        target_id = id(target)
        if target_id not in self.active_debuffs:
            self.active_debuffs[target_id] = []

        debuff = {
            "effect": effect,
            "duration_left": duration,
            "duration_max": duration,
            "value": effect_data.get("value", 0)
        }

        self.active_debuffs[target_id].append(debuff)

        return f"Áp dụng {effect} trong {duration} lượt", 0

    def _apply_dot(self, target: Dict,
                  effect_data: Dict) -> Tuple[str, int]:
        """Apply damage over time effect"""
        damage_per_turn = effect_data.get("damage_per_turn", 10)
        duration = effect_data.get("duration", 5)
        element = effect_data.get("element", "none")

        target_id = id(target)
        if target_id not in self.active_dots:
            self.active_dots[target_id] = []

        dot = {
            "damage_per_turn": damage_per_turn,
            "duration_left": duration,
            "element": element,
            "stack_behavior": effect_data.get("stack_behavior", "refresh")
        }

        self.active_dots[target_id].append(dot)

        return f"Áp dụng DOT ({element}): {damage_per_turn} damage/lượt x{duration}", 0

    def _apply_cc(self, target: Dict,
                 effect_data: Dict) -> Tuple[str, int]:
        """Apply crowd control effect"""
        cc_type = effect_data.get("effect", "stun")
        duration = effect_data.get("duration", 1)
        success_chance = effect_data.get("success_chance", 0.8)

        if random.random() > success_chance:
            return f"Khống chế {cc_type} thất bại", 0

        target_id = id(target)
        if target_id not in self.active_ccs:
            self.active_ccs[target_id] = []

        cc = {
            "type": cc_type,
            "duration_left": duration,
            "duration_max": duration
        }

        self.active_ccs[target_id].append(cc)

        return f"Khống chế {cc_type} thành công ({duration} lượt)", 0

    def _apply_life_steal(self, caster: Dict, target: Dict,
                         effect_data: Dict) -> Tuple[str, int]:
        """Apply life steal effect (steal HP based on damage)"""
        # First apply damage
        damage = self._calculate_damage(caster, target, effect_data)
        target["hp"] = max(0, target.get("hp", 0) - damage)

        # Then steal HP
        percentage = effect_data.get("percentage", 0.3)
        heal_amount = int(damage * percentage)
        caster_hp_max = caster.get("hp_max", 100)
        caster["hp"] = min(caster_hp_max, caster.get("hp", 0) + heal_amount)

        return f"Tấn công {damage} và hút {heal_amount} HP", damage

    def _apply_utility(self, target: Dict,
                      effect_data: Dict) -> Tuple[str, int]:
        """Apply utility effect (evade, block, counter, reflect)"""
        utility_type = effect_data.get("effect", "evade")
        value = effect_data.get("value", 50)
        duration = effect_data.get("duration", 1)

        target_id = id(target)
        if utility_type == "evade":
            if target_id not in self.active_buffs:
                self.active_buffs[target_id] = {}
            target["evasion_boost"] = value
            return f"Tăng né tránh {value}% trong {duration} lượt", 0

        elif utility_type == "block":
            if target_id not in self.active_buffs:
                self.active_buffs[target_id] = {}
            target["block_chance"] = value
            return f"Tăng khả năng chặn {value}% trong {duration} lượt", 0

        return f"Hiệu ứng utility: {utility_type}", 0

    def tick_effects(self, character: Dict):
        """Called each turn to reduce effect durations and apply DOT"""
        char_id = id(character)
        damage_taken = 0
        messages = []

        # Tick DOTs
        if char_id in self.active_dots:
            dots_to_remove = []
            for i, dot in enumerate(self.active_dots[char_id]):
                # Apply damage
                damage = dot["damage_per_turn"]
                character["hp"] = max(0, character.get("hp", 0) - damage)
                damage_taken += damage
                messages.append(f"DOT ({dot['element']}): -{damage} HP")

                # Reduce duration
                dot["duration_left"] -= 1
                if dot["duration_left"] <= 0:
                    dots_to_remove.append(i)

            # Remove expired DOTs
            for i in reversed(dots_to_remove):
                self.active_dots[char_id].pop(i)

        # Tick CCs
        if char_id in self.active_ccs:
            ccs_to_remove = []
            for i, cc in enumerate(self.active_ccs[char_id]):
                cc["duration_left"] -= 1
                if cc["duration_left"] <= 0:
                    ccs_to_remove.append(i)
                    messages.append(f"Khống chế {cc['type']} hết hiệu lực")

            for i in reversed(ccs_to_remove):
                self.active_ccs[char_id].pop(i)

        # Tick Buffs
        if char_id in self.active_buffs:
            for stat in list(self.active_buffs[char_id].keys()):
                buffs_to_remove = []
                for i, buff in enumerate(self.active_buffs[char_id][stat]):
                    buff["duration_left"] -= 1
                    if buff["duration_left"] <= 0:
                        buffs_to_remove.append(i)
                        messages.append(f"Buff {stat} hết hiệu lực")

                for i in reversed(buffs_to_remove):
                    self.active_buffs[char_id][stat].pop(i)

        # Tick Debuffs
        if char_id in self.active_debuffs:
            debuffs_to_remove = []
            for i, debuff in enumerate(self.active_debuffs[char_id]):
                debuff["duration_left"] -= 1
                if debuff["duration_left"] <= 0:
                    debuffs_to_remove.append(i)
                    messages.append(f"Debuff {debuff['effect']} hết hiệu lực")

            for i in reversed(debuffs_to_remove):
                self.active_debuffs[char_id].pop(i)

        return damage_taken, messages

    def get_active_buffs(self, character: Dict) -> Dict[str, int]:
        """Get active buff modifiers for a character"""
        char_id = id(character)
        modifiers = {}

        if char_id not in self.active_buffs:
            return modifiers

        for stat, buffs in self.active_buffs[char_id].items():
            total = 0
            for buff in buffs:
                total += buff["value"]
            if total > 0:
                modifiers[stat] = total

        return modifiers

    def get_active_debuffs(self, character: Dict) -> List[str]:
        """Get list of active debuffs"""
        char_id = id(character)
        if char_id not in self.active_debuffs:
            return []

        return [d["effect"] for d in self.active_debuffs[char_id]]

    def is_cc_active(self, character: Dict) -> bool:
        """Check if character has active crowd control"""
        char_id = id(character)
        return char_id in self.active_ccs and len(self.active_ccs[char_id]) > 0


# Global effect engine instance
effect_engine = EffectEngine()
