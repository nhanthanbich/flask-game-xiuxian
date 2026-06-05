"""
Effect-driven Combat System
Integrates EffectEngine with skill usage
"""

from engine.systems.effect_engine import effect_engine
from engine.systems.skill_loader import skill_loader
from typing import Dict, List, Tuple


class EffectCombat:
    """Combat system using data-driven effects"""

    def __init__(self):
        self.effect_engine = effect_engine
        self.skill_loader = skill_loader

    def use_skill_in_combat(self, caster: Dict, skill_id: str,
                           target: Dict,
                           combat_state: Dict) -> List[str]:
        """
        Use a skill in combat
        Returns list of result messages
        """
        try:
            skill = self.skill_loader.get_skill(skill_id)
        except ValueError:
            return [f"Công pháp {skill_id} không tồn tại"]

        results = []

        # Check cost
        cost_check = self._check_cost(caster, skill)
        if cost_check:
            return [cost_check]

        # Check cooldown
        cooldown_check = self._check_cooldown(skill_id, combat_state)
        if cooldown_check:
            return [cooldown_check]

        # Check crowd control
        if self.effect_engine.is_cc_active(caster):
            return [f"{caster.get('name', 'Bạn')} bị khống chế, không thể hành động"]

        # Apply each effect
        total_damage = 0
        for effect in skill.get('effects', []):
            msg, damage = self.effect_engine.apply_effect(
                caster, target, effect, combat_state
            )
            results.append(msg)
            if damage > 0:
                total_damage += damage

        # Deduct cost
        self._deduct_cost(caster, skill)
        results.insert(0, f"{caster.get('name', 'Bạn')} sử dụng {skill['name']}")

        # Add cooldown
        if skill['cooldown'] > 0:
            combat_state['cooldowns'][skill_id] = skill['cooldown']

        # Tick enemy effects
        dot_damage, dot_msgs = self.effect_engine.tick_effects(target)
        if dot_msgs:
            results.extend(dot_msgs)

        return results

    def _check_cost(self, caster: Dict, skill: Dict) -> str:
        """Check if caster has enough resources"""
        cost_type = skill['cost_type']
        cost_value = skill['cost_value']

        if cost_type == 'qi':
            current = caster.get('qi', 0)
            resource_name = 'linh lực'
        elif cost_type == 'blood':
            current = caster.get('blood', 0)
            resource_name = 'máu'
        elif cost_type == 'stamina':
            current = caster.get('stamina', 0)
            resource_name = 'thể lực'
        else:
            return ""

        if current < cost_value:
            return f"Không đủ {resource_name} ({current}/{cost_value})"

        return ""

    def _deduct_cost(self, caster: Dict, skill: Dict):
        """Deduct resource cost from caster"""
        cost_type = skill['cost_type']
        cost_value = skill['cost_value']

        if cost_type == 'qi':
            caster['qi'] = max(0, caster.get('qi', 0) - cost_value)
        elif cost_type == 'blood':
            caster['blood'] = max(0, caster.get('blood', 0) - cost_value)
        elif cost_type == 'stamina':
            caster['stamina'] = max(0, caster.get('stamina', 0) - cost_value)

    def _check_cooldown(self, skill_id: str, combat_state: Dict) -> str:
        """Check if skill is on cooldown"""
        cooldowns = combat_state.get('cooldowns', {})

        if skill_id in cooldowns and cooldowns[skill_id] > 0:
            return f"Công pháp còn cooldown ({cooldowns[skill_id]} lượt)"

        return ""

    def tick_cooldowns(self, combat_state: Dict):
        """Reduce all cooldowns by 1"""
        cooldowns = combat_state.get('cooldowns', {})
        for skill_id in cooldowns:
            cooldowns[skill_id] = max(0, cooldowns[skill_id] - 1)

    def get_skill_preview(self, skill_id: str) -> str:
        """Get formatted skill preview"""
        try:
            skill = self.skill_loader.get_skill(skill_id)
            description = self.skill_loader.generate_skill_description(skill)

            return (
                f"【{skill['name']}】\n"
                f"Cấp bậc: {skill['rank']} | Sức mạnh: {skill['power_level']}/10\n"
                f"Chi phí: {skill['cost_value']} {skill['cost_type']}\n"
                f"Cooldown: {skill['cooldown']} lượt\n"
                f"Thẻ: {', '.join(skill['tags'])}\n"
                f"Hiệu ứng: {description}"
            )
        except ValueError:
            return f"Công pháp {skill_id} không tồn tại"

    def get_available_skills(self, character: Dict,
                            learnable_skills: List[str]) -> List[Dict]:
        """Get skills available for character to use"""
        available = []

        for skill_id in learnable_skills:
            try:
                skill = self.skill_loader.get_skill(skill_id)
                available.append({
                    'id': skill_id,
                    'name': skill['name'],
                    'cost': f"{skill['cost_value']} {skill['cost_type']}",
                    'power': skill['power_level']
                })
            except ValueError:
                continue

        return available


# Global combat instance
effect_combat = EffectCombat()
