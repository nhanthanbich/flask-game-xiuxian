"""
Replayability System
Choice tracking, endings, emergent replay value
"""

import sys
sys.path.insert(0, '/tmp/cc-agent/67460546/project')

from typing import Dict, List, Tuple
from enum import Enum
from datetime import datetime


class PlaythroughEnding(Enum):
    """4 different endings"""
    ASCENSION = "Vị Tiên Độc Lập"  # Solo transcendence
    SECT_MASTER = "Trưởng Môn Đế Quân"  # Sect master
    DEMON_KING = "Ma Hoàng Thống Lĩnh"  # Demonic ruler
    UNION = "Thống Nhất Giang Hồ"  # World unification (hardest)


class ReplayabilitySystem:
    """Tracks meaningful choices and enables replay differentiation"""

    def __init__(self):
        self.all_playthroughs = []
        self.current_playthrough = None

    def start_playthrough(self, character_name: str) -> Dict:
        """Initialize new playthrough tracking"""
        self.current_playthrough = {
            "id": len(self.all_playthroughs) + 1,
            "character": character_name,
            "start_date": datetime.now().isoformat(),
            "end_date": None,
            "ending": None,

            # Choice tracking (0-100 scales)
            "path_score": 50,  # 0=Orthodox, 100=Demonic
            "personality_score": 50,  # 0=Rational, 100=Emotional
            "sect_loyalty": {},  # sect_id -> loyalty points

            # Key decisions
            "major_choices": [],  # List of [choice_name, consequence]
            "npc_allies": [],  # Favorite NPCs
            "sect_affiliation": None,

            # Final stats
            "final_realm": None,
            "final_corruption": 0,
            "allies_alive": [],
            "sect_power_at_end": 0,
            "score": 0
        }

        return {
            "message": f"🎮 Bắt đầu playthrough: {character_name}",
            "id": self.current_playthrough["id"]
        }

    def record_choice(self, choice_name: str, choice_type: str, value: int) -> None:
        """Record player's meaningful choice"""
        if not self.current_playthrough:
            return

        if choice_type == "path":
            # 0=Orthodox (good), 100=Demonic (evil)
            self.current_playthrough["path_score"] += value
            self.current_playthrough["path_score"] = max(0, min(100,
                self.current_playthrough["path_score"]))

        elif choice_type == "personality":
            # 0=Rational, 100=Emotional
            self.current_playthrough["personality_score"] += value
            self.current_playthrough["personality_score"] = max(0, min(100,
                self.current_playthrough["personality_score"]))

        elif choice_type == "sect":
            sect_id = value  # value is sect_id
            self.current_playthrough["sect_loyalty"][sect_id] = \
                self.current_playthrough["sect_loyalty"].get(sect_id, 0) + 1

        self.current_playthrough["major_choices"].append({
            "choice": choice_name,
            "type": choice_type,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })

    def set_npc_ally(self, npc_name: str, strength: int = 1) -> None:
        """Track primary NPC allies"""
        if not self.current_playthrough:
            return

        if npc_name not in self.current_playthrough["npc_allies"]:
            self.current_playthrough["npc_allies"].append(npc_name)

    def finalize_playthrough(self, final_stats: Dict) -> Dict:
        """Complete playthrough and calculate ending"""
        if not self.current_playthrough:
            return {}

        # Calculate ending based on path_score and realm
        ending = self._determine_ending(final_stats)

        # Calculate score
        score = self._calculate_score(final_stats)

        self.current_playthrough.update({
            "end_date": datetime.now().isoformat(),
            "final_realm": final_stats.get("realm", "Unknown"),
            "final_corruption": final_stats.get("corruption", 0),
            "allies_alive": final_stats.get("npcs_alive", []),
            "sect_power_at_end": final_stats.get("sect_power", 0),
            "ending": ending,
            "score": score
        })

        self.all_playthroughs.append(self.current_playthrough)

        return {
            "ending": ending,
            "score": score,
            "leaderboard_rank": self._get_rank()
        }

    def _determine_ending(self, final_stats: Dict) -> str:
        """Determine which ending player gets"""
        if not self.current_playthrough:
            return "Unknown"

        realm = final_stats.get("realm", "")
        corruption = final_stats.get("corruption", 0)
        sect_power = final_stats.get("sect_power", 0)

        # Ending determination
        if realm != "Phi Thăng":
            return "Không Hoàn Thành"  # Incomplete

        path = self.current_playthrough["path_score"]
        sect = self.current_playthrough["sect_affiliation"]

        # Ascension: high realm, isolated path
        if path < 30:  # Orthodox
            if sect_power > 80:
                return PlaythroughEnding.SECT_MASTER.value
            else:
                return PlaythroughEnding.ASCENSION.value

        # Demon King: high realm, demonic path
        elif path > 70:  # Demonic
            return PlaythroughEnding.DEMON_KING.value

        # Union: balanced, high sect power, negotiated peace
        elif 40 <= path <= 60:
            if sect_power > 90:
                return PlaythroughEnding.UNION.value

        return PlaythroughEnding.ASCENSION.value

    def _calculate_score(self, final_stats: Dict) -> int:
        """Calculate playthrough score for leaderboard"""
        if not self.current_playthrough:
            return 0

        score = 0

        # Realm bonus (Phi Thăng = 1000 points)
        realm_points = {
            "Luyện Khí": 100,
            "Trúc Cơ": 300,
            "Kết Đan": 600,
            "Nguyên Anh": 900,
            "Phi Thăng": 1000
        }
        score += realm_points.get(final_stats.get("realm", ""), 0)

        # Choice diversity
        choices = self.current_playthrough["major_choices"]
        score += len(choices) * 10

        # NPC allies
        score += len(self.current_playthrough["npc_allies"]) * 50

        # Sect power bonus
        score += final_stats.get("sect_power", 0) * 2

        # Ending bonus
        ending_bonus = {
            "Vị Tiên Độc Lập": 200,
            "Trưởng Môn Đế Quân": 300,
            "Ma Hoàng Thống Lĩnh": 250,
            "Thống Nhất Giang Hồ": 500
        }
        score += ending_bonus.get(self.current_playthrough["ending"], 0)

        return score

    def _get_rank(self) -> int:
        """Get current playthrough rank in leaderboard"""
        if not self.current_playthrough:
            return 0

        current_score = self.current_playthrough["score"]
        rank = 1

        for pt in self.all_playthroughs[:-1]:  # Exclude current
            if pt.get("score", 0) > current_score:
                rank += 1

        return rank

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get leaderboard of playthroughs"""
        sorted_pts = sorted(
            self.all_playthroughs,
            key=lambda x: x.get("score", 0),
            reverse=True
        )

        leaderboard = []
        for i, pt in enumerate(sorted_pts[:limit], 1):
            leaderboard.append({
                "rank": i,
                "character": pt["character"],
                "ending": pt.get("ending", "N/A"),
                "score": pt.get("score", 0),
                "realm": pt.get("final_realm", "N/A"),
                "path": "Orthodox" if pt["path_score"] < 30 else
                        ("Demonic" if pt["path_score"] > 70 else "Balanced")
            })

        return leaderboard

    def get_playthrough_summary(self, playthrough_id: int = None) -> Dict:
        """Get summary of a playthrough"""
        if playthrough_id is None:
            pt = self.current_playthrough
        else:
            pt = next((p for p in self.all_playthroughs if p["id"] == playthrough_id), None)

        if not pt:
            return {}

        return {
            "id": pt["id"],
            "character": pt["character"],
            "ending": pt.get("ending", "In Progress"),
            "score": pt.get("score", "N/A"),
            "realm": pt.get("final_realm", "Unknown"),
            "path": "Orthodox" if pt["path_score"] < 30 else
                    ("Demonic" if pt["path_score"] > 70 else "Balanced"),
            "personality": "Rational" if pt["personality_score"] < 30 else
                          ("Emotional" if pt["personality_score"] > 70 else "Balanced"),
            "major_allies": pt["npc_allies"],
            "choices_made": len(pt["major_choices"]),
            "corruption": pt.get("final_corruption", 0)
        }

    def get_ng_plus_bonuses(self, playthrough_id: int) -> Dict:
        """Get bonuses for starting New Game+ based on previous playthrough"""
        prev_pt = next((p for p in self.all_playthroughs if p["id"] == playthrough_id), None)

        if not prev_pt:
            return {}

        # NPC memory
        npc_memory = {
            "npcs_remember": prev_pt["npc_allies"],
            "relationship_bonus": {npc: 20 for npc in prev_pt["npc_allies"]}
        }

        # Skill retention based on score
        if prev_pt.get("score", 0) > 1500:
            skill_level = 3  # Keep 3 skills
        elif prev_pt.get("score", 0) > 1000:
            skill_level = 2  # Keep 2 skills
        else:
            skill_level = 1  # Keep 1 skill

        # World awareness
        world_bonus = {
            "secret_realms_known": 2,
            "hidden_items_revealed": 3,
            "shortcut_paths": True
        }

        return {
            "npc_memory": npc_memory,
            "skill_retention": skill_level,
            "world_knowledge": world_bonus,
            "prestige_level": (len(self.all_playthroughs))
        }


# Test replayability system
if __name__ == "__main__":
    print("\n" + "="*80)
    print("REPLAYABILITY SYSTEM TEST".center(80))
    print("="*80 + "\n")

    replay = ReplayabilitySystem()

    # Playthrough 1: Orthodox path
    print("1️⃣ PLAYTHROUGH 1: Orthodox (Thanh Vân)")
    print("-" * 80)

    pt1 = replay.start_playthrough("Chính Tông Chiến Sĩ")
    print(pt1["message"])

    replay.record_choice("Reject demonic arts", "path", -20)
    replay.record_choice("Aid Thanh Vân", "sect", "thanh_van")
    replay.set_npc_ally("Hoa Yên", 1)
    replay.set_npc_ally("Trương Vũ", 1)

    result1 = replay.finalize_playthrough({
        "realm": "Phi Thăng",
        "corruption": 5,
        "sect_power": 85,
        "npcs_alive": ["Hoa Yên", "Trương Vũ"],
    })

    print(f"✓ Ending: {result1['ending']}")
    print(f"✓ Score: {result1['score']}")
    print(f"✓ Rank: #{result1['leaderboard_rank']}")
    print()

    # Playthrough 2: Demonic path
    print("2️⃣ PLAYTHROUGH 2: Demonic (Hỗn Trâm)")
    print("-" * 80)

    pt2 = replay.start_playthrough("Ma Đạo Xán Lạn")
    print(pt2["message"])

    replay.record_choice("Embrace dark power", "path", +25)
    replay.record_choice("Choose emotional path", "personality", +20)
    replay.record_choice("Ally with Hỗn Trâm", "sect", "hun_tram")
    replay.set_npc_ally("Tử Phong", 1)

    result2 = replay.finalize_playthrough({
        "realm": "Phi Thăng",
        "corruption": 75,
        "sect_power": 60,
        "npcs_alive": ["Tử Phong"],
    })

    print(f"✓ Ending: {result2['ending']}")
    print(f"✓ Score: {result2['score']}")
    print(f"✓ Rank: #{result2['leaderboard_rank']}")
    print()

    # Leaderboard
    print("3️⃣ LEADERBOARD")
    print("-" * 80)

    leaderboard = replay.get_leaderboard(5)
    print(f"{'Rank':<6} {'Character':<25} {'Ending':<25} {'Score':<10} {'Path':<12}")
    print("-" * 80)

    for entry in leaderboard:
        print(f"{entry['rank']:<6} {entry['character']:<25} {entry['ending']:<25} {entry['score']:<10} {entry['path']:<12}")

    print()

    # Playthrough summary
    print("4️⃣ PLAYTHROUGH SUMMARIES")
    print("-" * 80)

    for i in [1, 2]:
        summary = replay.get_playthrough_summary(i)
        print(f"\n[Playthrough {i}]")
        print(f"  Character: {summary['character']}")
        print(f"  Ending: {summary['ending']}")
        print(f"  Path: {summary['path']} | Personality: {summary['personality']}")
        print(f"  Allies: {', '.join(summary['major_allies'])}")
        print(f"  Choices: {summary['choices_made']} | Score: {summary['score']}")

    print()

    # NG+ bonuses
    print("5️⃣ NEW GAME+ BONUSES (from PT1)")
    print("-" * 80)

    ng_bonuses = replay.get_ng_plus_bonuses(1)
    print(f"NPC Memory: {ng_bonuses['npc_memory']['npcs_remember']}")
    print(f"Skill Retention: {ng_bonuses['skill_retention']} skills")
    print(f"Prestige Level: {ng_bonuses['prestige_level']}")

    print()
    print("="*80)
    print("✅ REPLAYABILITY SYSTEM COMPLETE".center(80))
    print("="*80 + "\n")
