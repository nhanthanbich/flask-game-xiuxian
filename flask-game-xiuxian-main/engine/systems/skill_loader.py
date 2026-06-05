"""
Skill Loader - Load skills from CSV and build effect objects
"""

import csv
from typing import Dict, List, Any
from pathlib import Path


class SkillLoader:
    """Load and cache skills from CSV files"""

    def __init__(self, skills_master_path: str = "data/skills_master.csv",
                 skill_effects_path: str = "data/skill_effects.csv"):
        self.skills_master_path = skills_master_path
        self.skill_effects_path = skill_effects_path
        self.skills_cache = {}
        self.effects_cache = {}
        self.load_all()

    def load_all(self):
        """Load both skills_master and skill_effects"""
        self._load_skills_master()
        self._load_skill_effects()
        self._build_skills()

    def _load_skills_master(self):
        """Load skills_master.csv"""
        try:
            with open(self.skills_master_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    skill_id = row['id']
                    self.skills_cache[skill_id] = {
                        'id': skill_id,
                        'name': row['name'],
                        'element': row['element'],
                        'cost_type': row['cost_type'],
                        'cost_value': int(row['cost_value']),
                        'cooldown': int(row['cooldown']),
                        'tags': row['tags'].split('|'),
                        'learn_source': row['learn_source'],
                        'learn_requirement': row['learn_requirement'],
                        'rank': int(row['rank']),
                        'power_level': int(row['power_level']),
                        'effects': []
                    }
        except FileNotFoundError:
            print(f"Warning: {self.skills_master_path} not found")

    def _load_skill_effects(self):
        """Load skill_effects.csv"""
        try:
            with open(self.skill_effects_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    skill_id = row['skill_id']
                    if skill_id not in self.effects_cache:
                        self.effects_cache[skill_id] = []

                    effect = {
                        'name': row['effect_name'],
                        'type': row['effect_type'],
                        'value': int(row['value']) if row['value'] else 0,
                        'element': row['element'],
                        'scaling': row['scaling'],
                        'duration': int(row['duration']) if row['duration'] else 0,
                        'success_chance': float(row['success_chance']) if row['success_chance'] else 1.0,
                        'stat': row['stat'],
                        'crit_chance': float(row['crit_chance']) if row['crit_chance'] else 0.0,
                        'stack_behavior': row['stack_behavior'],
                        'resist_check': row['resist_check'].lower() == 'true',
                        'damage_per_turn': int(row['damage_per_turn']) if row['damage_per_turn'] else 0,
                    }

                    self.effects_cache[skill_id].append(effect)
        except FileNotFoundError:
            print(f"Warning: {self.skill_effects_path} not found")

    def _build_skills(self):
        """Build complete skill objects with effects"""
        for skill_id, effects in self.effects_cache.items():
            if skill_id in self.skills_cache:
                self.skills_cache[skill_id]['effects'] = effects

    def get_skill(self, skill_id: str) -> Dict[str, Any]:
        """Get a single skill by ID"""
        if skill_id not in self.skills_cache:
            raise ValueError(f"Skill {skill_id} not found")

        return self.skills_cache[skill_id].copy()

    def get_all_skills(self) -> Dict[str, Dict]:
        """Get all skills"""
        return {k: v.copy() for k, v in self.skills_cache.items()}

    def get_skills_by_tag(self, tag: str) -> List[Dict]:
        """Get all skills with a specific tag"""
        result = []
        for skill in self.skills_cache.values():
            if tag in skill['tags']:
                result.append(skill.copy())
        return result

    def generate_skill_description(self, skill: Dict) -> str:
        """
        Auto-generate description from effects

        Returns a readable description of what the skill does
        """
        descriptions = []

        for effect in skill.get('effects', []):
            effect_type = effect['type']

            if effect_type == 'damage':
                desc = f"Tấn công {effect['value']} ({effect['element']})"
                if effect['crit_chance'] > 0:
                    desc += f", {int(effect['crit_chance']*100)}% chí mạng"
                descriptions.append(desc)

            elif effect_type == 'heal':
                desc = f"Chữa {effect['value']} HP"
                descriptions.append(desc)

            elif effect_type == 'buff':
                stat = effect['stat']
                value = effect['value']
                duration = effect['duration']
                descriptions.append(f"Tăng {stat} +{value}% ({duration} lượt)")

            elif effect_type == 'debuff':
                effect_name = effect['name'].replace('_', ' ')
                duration = effect['duration']
                descriptions.append(f"Gây {effect_name} ({duration} lượt)")

            elif effect_type == 'dot':
                damage = effect['damage_per_turn']
                duration = effect['duration']
                element = effect['element']
                descriptions.append(f"DOT {element}: {damage} HP/lượt ({duration} lượt)")

            elif effect_type == 'cc':
                cc_type = effect['name'].replace('_', ' ')
                success = int(effect['success_chance'] * 100)
                descriptions.append(f"Khống chế {cc_type} ({success}%)")

            elif effect_type == 'life_steal':
                descriptions.append("Hút HP từ damage gây ra")

            elif effect_type == 'utility':
                utility = effect['name'].replace('_', ' ')
                value = effect['value']
                descriptions.append(f"Tăng {utility} +{value}%")

        return " | ".join(descriptions)

    def reload(self):
        """Reload skills from CSV (for live updates)"""
        self.skills_cache.clear()
        self.effects_cache.clear()
        self.load_all()

    def add_skill_from_data(self, skill_dict: Dict):
        """Dynamically add a skill (useful for testing)"""
        skill_id = skill_dict['id']
        self.skills_cache[skill_id] = {
            'id': skill_id,
            'name': skill_dict.get('name', 'New Skill'),
            'element': skill_dict.get('element', 'none'),
            'cost_type': skill_dict.get('cost_type', 'qi'),
            'cost_value': skill_dict.get('cost_value', 50),
            'cooldown': skill_dict.get('cooldown', 0),
            'tags': skill_dict.get('tags', []),
            'learn_source': skill_dict.get('learn_source', 'npc'),
            'learn_requirement': skill_dict.get('learn_requirement', 'none'),
            'rank': skill_dict.get('rank', 1),
            'power_level': skill_dict.get('power_level', 5),
            'effects': skill_dict.get('effects', [])
        }


# Global skill loader instance
skill_loader = SkillLoader()
