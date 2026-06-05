"""
Endgame Content System
Phi Thăng challenges, New Game+ mechanics, seasonal events
"""

import sys
sys.path.insert(0, '/tmp/cc-agent/67460546/project')

from typing import Dict, List, Tuple, Any
from enum import Enum
import random


class GrandmasterChallenge(Enum):
    """Phi Thăng endgame challenges"""
    ELITE_ARENA = "Đấu Trường Tinh Anh"
    SECT_DOMINANCE = "Thống Lãnh Giang Hồ"
    DEMON_HUNTING = "Săn Lùng Yêu Quái"
    HERITAGE = "Truyền Dạy Kế Thừa"


class MasteryType(Enum):
    """Element mastery perfection"""
    FIRE = "火 (Lửa)"
    WATER = "水 (Nước)"
    WOOD = "木 (Gỗ)"
    METAL = "金 (Kim)"
    EARTH = "土 (Đất)"


class NGPlusMode(Enum):
    """New Game+ difficulty modes"""
    KEEP = "Giữ linh căn + 50% exp/skill"
    RESET = "Reset level, world nhớ player"
    CHALLENGE = "Giống cũ nhưng enemy +20% stat"


class EndgameSystem:
    """Manages post-Phi Thăng content"""

    def __init__(self):
        self.grandmaster_unlocked = False
        self.current_mastery = None
        self.mastery_progress = {}  # mastery -> 0-100 progress
        self.secret_skills_unlocked = []
        self.grandmaster_challenges = {}
        self.challenge_leaderboard = []

    def unlock_grandmaster(self, player_realm: str):
        """Unlock Phi Thăng endgame"""
        if player_realm == "Phi Thăng":
            self.grandmaster_unlocked = True
            self.initialize_challenges()
            return "✨ Đạt Phi Thăng! Mở khóa nội dung Danh Sĩ"
        return None

    def initialize_challenges(self):
        """Initialize all grandmaster challenges"""
        self.grandmaster_challenges = {
            "elite_arena": {
                "name": GrandmasterChallenge.ELITE_ARENA.value,
                "description": "Chiến đấu với các vị cao nhân khác (ghost players)",
                "repeatable": True,
                "reward": "Ranking, special item",
                "difficulty": "Cao",
                "players_defeated": 0
            },
            "sect_dominance": {
                "name": GrandmasterChallenge.SECT_DOMINANCE.value,
                "description": "Dẫn dắt tông môn chiếm lãnh địa trên bản đồ",
                "repeatable": True,
                "reward": "Sect power +20, territory control",
                "difficulty": "Rất cao",
                "territories_conquered": 0
            },
            "demon_hunting": {
                "name": GrandmasterChallenge.DEMON_HUNTING.value,
                "description": "Tiêu diệt các tu sĩ ma đạo",
                "repeatable": True,
                "reward": "Corruption -10, justice honor",
                "difficulty": "Cực cao",
                "demons_purged": 0
            },
            "heritage": {
                "name": GrandmasterChallenge.HERITAGE.value,
                "description": "Truyền dạy cho tân nhân, tạo di sản",
                "repeatable": False,
                "reward": "Legacy character, new playthrough advantage",
                "difficulty": "Đặc biệt",
                "disciples_trained": 0
            }
        }

    def start_mastery(self, mastery_type: MasteryType) -> str:
        """Begin perfecting an element"""
        if not self.grandmaster_unlocked:
            return "❌ Phải đạt Phi Thăng trước"

        self.current_mastery = mastery_type.name
        self.mastery_progress[mastery_type.name] = 0

        return f"🔥 Bắt đầu tu luyện {mastery_type.value}\nTiến độ: 0%"

    def advance_mastery(self, days: int) -> str:
        """Advance mastery progress"""
        if not self.current_mastery:
            return "❌ Chưa chọn nào để tu luyện"

        progress = self.mastery_progress.get(self.current_mastery, 0)
        progress_gain = days * 0.5  # 0.5% per day

        self.mastery_progress[self.current_mastery] = min(100, progress + progress_gain)

        if self.mastery_progress[self.current_mastery] >= 100:
            return self._unlock_secret_skill(self.current_mastery)

        return f"📈 {self.current_mastery} mastery: {self.mastery_progress[self.current_mastery]:.0f}%"

    def _unlock_secret_skill(self, mastery: str) -> str:
        """Unlock secret ultimate skill for mastery"""
        skills = {
            "FIRE": "Thiên Hoả Dào Lâu - Thiêu Dương Tuyệt Kỹ (完全)",
            "WATER": "Thủy Cung Tuyệt Thế - Bao La Đại Dương (完全)",
            "WOOD": "Sinh Mệnh Tòng Sinh - Mục Linh Chi Oán (完全)",
            "METAL": "Kim Thế Li Tử - Thiết Huyết Hoa Hạng (完全)",
            "EARTH": "Đất Thần Thế Giới - Toàn Năng Bảo Vệ (完全)"
        }

        skill_name = skills.get(mastery, "Secret Skill")
        self.secret_skills_unlocked.append(skill_name)
        self.mastery_progress[mastery] = 100

        return f"✨ ĐẠT THÀNH CÔNG! Mở khóa skill bí ẩn:\n{skill_name}\n(Sử dụng: tất cả tình huống, không cooldown đầu tiên)"

    def get_challenge_status(self, challenge_id: str) -> Dict:
        """Get current challenge progress"""
        return self.grandmaster_challenges.get(challenge_id, {}).copy()

    def complete_elite_arena(self, opponent_level: int, victory: bool) -> str:
        """Complete elite arena challenge"""
        if not self.grandmaster_unlocked:
            return "❌ Phải đạt Phi Thăng trước"

        if victory:
            self.grandmaster_challenges["elite_arena"]["players_defeated"] += 1
            rank = self._calculate_arena_rank()
            return f"⚔️ THẮNG! Hạng #{rank}\n+100 reputation, +special item"
        else:
            return f"💔 Thua. Học hỏi từ đối thủ.\n+10 reputation"

    def _calculate_arena_rank(self) -> int:
        """Calculate leaderboard rank"""
        wins = self.grandmaster_challenges["elite_arena"]["players_defeated"]
        return max(1, 1000 - (wins * 5))

    def complete_sect_dominance(self, territories: int) -> str:
        """Complete sect dominance challenge"""
        if not self.grandmaster_unlocked:
            return "❌ Phải đạt Phi Thăng trước"

        self.grandmaster_challenges["sect_dominance"]["territories_conquered"] += territories
        total = self.grandmaster_challenges["sect_dominance"]["territories_conquered"]

        if total >= 5:
            return f"🏛️ CHINH PHỤC! Kiếm soát toàn bộ giang hồ.\n+Sect Master status"
        else:
            return f"⚔️ Chinh phục {territories} lãnh địa.\nTổng: {total}/5"

    def complete_demon_hunting(self, demons_purged: int) -> str:
        """Complete demon hunting challenge"""
        if not self.grandmaster_unlocked:
            return "❌ Phải đạt Phi Thăng trước"

        self.grandmaster_challenges["demon_hunting"]["demons_purged"] += demons_purged
        total = self.grandmaster_challenges["demon_hunting"]["demons_purged"]

        corruption_reduction = demons_purged * 2
        return f"👹 Tiêu diệt {demons_purged} yêu quái.\nCorruption -{corruption_reduction}\nTổng: {total} yêu quái"

    def train_disciple(self, disciple_name: str, training_days: int) -> str:
        """Train heritage disciple"""
        if not self.grandmaster_unlocked:
            return "❌ Phải đạt Phi Thăng trước"

        if self.grandmaster_challenges["heritage"]["disciples_trained"] >= 1:
            return "❌ Đã truyền thừa 1 lần. Một người đã đủ."

        # Calculate disciple strength based on training
        disciple_realm = min(4, (training_days // 50))  # Max Phi Thăng-1
        disciple_power = training_days * 2

        self.grandmaster_challenges["heritage"]["disciples_trained"] += 1

        return f"👨‍🏫 Truyền dạy hoàn tất!\nDệ tử: {disciple_name}\nCảnh giới: Nguyên Anh {disciple_realm}\nSức mạnh: {disciple_power}\n\n[Tiền đề cho playthrough tiếp theo]"


class NewGamePlusSystem:
    """Manages New Game+ progression"""

    def __init__(self):
        self.playthroughs = []
        self.current_ng_plus_mode = None
        self.previous_stats = {}

    def get_ng_plus_options(self, final_stats: Dict) -> List[Tuple[str, str]]:
        """Get New Game+ mode options"""
        self.previous_stats = final_stats

        options = [
            ("keep", "📖 Giữ - Bắt đầu với linh căn cũ, 50% exp/skill"),
            ("reset", "🔄 Reset - Luyện Khí 1 nhưng NPC nhớ bạn"),
            ("challenge", "⚔️ Thử Thách - Cùng thế giới, enemy +20% stat"),
        ]

        return options

    def start_ng_plus(self, mode: str, player_profile: Dict) -> Dict:
        """Initialize New Game+ playthrough"""
        self.current_ng_plus_mode = mode

        if mode == "keep":
            return self._ng_keep_mode(player_profile)
        elif mode == "reset":
            return self._ng_reset_mode(player_profile)
        elif mode == "challenge":
            return self._ng_challenge_mode(player_profile)

        return {}

    def _ng_keep_mode(self, profile: Dict) -> Dict:
        """Keep stats, exp boost"""
        return {
            "name": "Giữ Mode",
            "realm": profile.get("realm", "Luyện Khí 1"),
            "exp_multiplier": 1.5,  # 50% exp boost
            "skills_retained": profile.get("skills", []),
            "linh_can": profile.get("linh_can", "random"),
            "intro": "Bạn bắt đầu với kỹ năng cũ nhưng sự tu luyện sâu hơn (EXP +50%)"
        }

    def _ng_reset_mode(self, profile: Dict) -> Dict:
        """Reset realm, NPC remember"""
        return {
            "name": "Reset Mode",
            "realm": "Luyện Khí 1",
            "exp_multiplier": 1.0,
            "skills_retained": [],
            "linh_can": profile.get("linh_can", "random"),  # Keep linh căn
            "npc_memory": True,
            "intro": "Bạn quay lại, nhưng giang hồ nhớ bạn. Hoa Yên: 'Người trở lại rồi...'"
        }

    def _ng_challenge_mode(self, profile: Dict) -> Dict:
        """Challenge mode, enemies stronger"""
        return {
            "name": "Thử Thách Mode",
            "realm": profile.get("realm", "Luyện Khí 1"),
            "exp_multiplier": 1.0,
            "enemy_stat_multiplier": 1.2,  # +20% enemy stats
            "skills_retained": profile.get("skills", []),
            "linh_can": profile.get("linh_can", "random"),
            "intro": "Cùng thế giới, nhưng mọi thứ khó khăn hơn. Hãy thích nghi..."
        }

    def record_playthrough(self, playthrough_data: Dict):
        """Record completed playthrough"""
        playthrough_data["ng_plus_count"] = len(self.playthroughs)
        self.playthroughs.append(playthrough_data)

    def get_leaderboard(self) -> List[Dict]:
        """Get playthroughs leaderboard"""
        sorted_playthroughs = sorted(
            self.playthroughs,
            key=lambda x: x.get("score", 0),
            reverse=True
        )
        return sorted_playthroughs[:10]  # Top 10


class SeasonalEventSystem:
    """Manages seasonal events within game time"""

    def __init__(self):
        self.events_calendar = self._generate_calendar()
        self.completed_events = []
        self.active_event = None

    def _generate_calendar(self) -> Dict[int, List[Dict]]:
        """Generate events calendar (3 per year)"""
        events = {
            3: {
                "name": "Lễ Hội Tiên Phục Hồi",
                "month": 3,
                "description": "Festival để tưởng nhớ tiên sơ, nhân dịp đón năm mới",
                "quests": ["Tìm tiên hoa", "Tặng quà cộng đồng", "Ritual cầu mưa"],
                "reward": "Rare loot, special flower item",
                "world_effect": "Sect power +5 (peace), NPC happy"
            },
            7: {
                "name": "Thử Thách Danh Sĩ",
                "month": 7,
                "description": "Tournament hàng năm, giang hồ tranh chung kết",
                "quests": ["Tham dự tournament", "Chiến đấu vs 3 NPC", "Đạt semi-final"],
                "reward": "Tournament trophy, rare weapon",
                "world_effect": "Sect power ±10 (based on outcome)"
            },
            11: {
                "name": "Tối Hoàng Kỳ",
                "month": 11,
                "description": "Tối tối kỳ kỳ, ma quỷ tràn ngập, giang hồ vào nguy hiểm",
                "quests": ["Phòng vệ thị trấn", "Săn lùng yêu quái", "Cứu NPC bị bắt"],
                "reward": "Anti-demon items, corruption scroll",
                "world_effect": "Demonic corruption rises, NPC danger +20%"
            }
        }
        return events

    def check_season_event(self, current_month: int, current_year: int) -> Dict:
        """Check if event is active this month"""
        if current_month in self.events_calendar:
            event = self.events_calendar[current_month].copy()
            event["year"] = current_year
            self.active_event = event
            return event

        return {}

    def get_event_quests(self, event_name: str) -> List[str]:
        """Get quests for active event"""
        for month, event in self.events_calendar.items():
            if event["name"] == event_name:
                return event.get("quests", [])

        return []

    def complete_event(self, event_name: str, quest_count: int) -> str:
        """Complete seasonal event"""
        event_info = None
        for month, event in self.events_calendar.items():
            if event["name"] == event_name:
                event_info = event
                break

        if not event_info:
            return "❌ Event không tìm thấy"

        self.completed_events.append({
            "event": event_name,
            "quests_completed": quest_count,
            "reward": event_info.get("reward", "")
        })

        return f"🎉 Hoàn tất {event_name}!\nPhần thưởng: {event_info.get('reward', '')}\nThế giới: {event_info.get('world_effect', '')}"

    def get_season_calendar(self) -> str:
        """Display seasonal calendar"""
        calendar = "📅 LỊCH NGÀNH HO năm:\n\n"

        for month in sorted(self.events_calendar.keys()):
            event = self.events_calendar[month]
            calendar += f"Tháng {month}: {event['name']}\n"
            calendar += f"  → {event['description']}\n\n"

        return calendar


# Test endgame system
if __name__ == "__main__":
    print("\n" + "="*80)
    print("ENDGAME SYSTEM TEST".center(80))
    print("="*80 + "\n")

    # Test 1: Grandmaster challenges
    print("1️⃣ GRANDMASTER CHALLENGES")
    print("-" * 80)

    endgame = EndgameSystem()
    print(endgame.unlock_grandmaster("Phi Thăng"))
    print(endgame.complete_elite_arena(50, True))
    print(endgame.complete_sect_dominance(2))
    print(endgame.complete_demon_hunting(5))
    print()

    # Test 2: Mastery system
    print("2️⃣ MASTERY PERFECTION")
    print("-" * 80)

    print(endgame.start_mastery(MasteryType.FIRE))
    print(endgame.advance_mastery(200))  # 200 days = 100% mastery
    print()

    # Test 3: New Game+
    print("3️⃣ NEW GAME+ SYSTEM")
    print("-" * 80)

    ng_plus = NewGamePlusSystem()
    final_stats = {"realm": "Phi Thăng", "skills": ["SK001", "SK008"], "linh_can": "Thần Lôi"}
    options = ng_plus.get_ng_plus_options(final_stats)

    for mode, desc in options:
        print(f"  {desc}")

    print()
    mode = ng_plus.start_ng_plus("reset", final_stats)
    print(f"✓ {mode['name']}: {mode['intro']}")
    print()

    # Test 4: Seasonal events
    print("4️⃣ SEASONAL EVENTS")
    print("-" * 80)

    seasonal = SeasonalEventSystem()
    print(seasonal.get_season_calendar())

    print("Current events:")
    print(seasonal.check_season_event(3, 1))
    print()
    print(seasonal.complete_event("Lễ Hội Tiên Phục Hồi", 3))
    print()

    print("="*80)
    print("✅ ENDGAME SYSTEM COMPLETE".center(80))
    print("="*80 + "\n")
