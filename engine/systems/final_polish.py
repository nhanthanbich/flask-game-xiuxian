"""
Final Polish: Tutorial Quest, Help Menu, Settings
"""

import sys
sys.path.insert(0, '/tmp/cc-agent/67460546/project')

from typing import Dict, List


class TutorialQuest:
    """First playthrough tutorial quest"""

    def __init__(self):
        self.current_step = 0
        self.steps_completed = []
        self.tutorial_active = True

    def get_tutorial_steps(self) -> List[Dict]:
        """Define 5-step tutorial"""
        return [
            {
                "step": 1,
                "name": "Bước Đầu Tu Luyện",
                "npc": "Sư Phụ Hoa Yên",
                "objective": "Tu luyện 5 lần để hiểu cơ bản",
                "description": "Hoa Yên: 'Hãy bắt đầu luyện công. Mỗi lần tu luyện sẽ tăng linh lực.'",
                "hint": "Nhấn 'Tu luyện' trên tab Cultivation",
                "reward": "10 exp",
                "required_progress": {"cultivation_count": 5}
            },
            {
                "step": 2,
                "name": "Đạt Mốc Tiến Độ",
                "npc": "Sư Phụ Hoa Yên",
                "objective": "Linh lực đạt 50% tiến độ",
                "description": "Hoa Yên: 'Tiến độ càng cao, sự đột phá càng gần. Hãy tiếp tục.'",
                "hint": "Thấy tiến độ tăng trên thanh Tu Vi Tiến Độ",
                "reward": "20 exp",
                "required_progress": {"exp_percent": 50}
            },
            {
                "step": 3,
                "name": "Gặp Sư Huynh",
                "npc": "Sư Huynh Trương Vũ",
                "objective": "Nhận lời chào từ Trương Vũ",
                "description": "Trương Vũ: 'Chào tân thủ! Nếu cần giúp đỡ, tìm tôi ở tab Relations.'",
                "hint": "Chuyển sang tab 'Relations' để gặp các NPC",
                "reward": "15 exp, +10 Trương Vũ relationship",
                "required_progress": {"npc_interaction_count": 1}
            },
            {
                "step": 4,
                "name": "Nhận Quest Chính Thức",
                "npc": "Hoa Yên",
                "objective": "Nhận quest 'Lấy Thảo Dược từ Động Linh Tuyệt'",
                "description": "Hoa Yên: 'Nhiệm vụ đầu tiên của bạn sẽ dạy bạn về ngoài thế giới.'",
                "hint": "Trở lại Hoa Yên và nhân quest từ cô ấy",
                "reward": "50 exp, unlock quest system",
                "required_progress": {"quest_accepted": True}
            },
            {
                "step": 5,
                "name": "Khởi Hành Cuộc Phiêu Lưu",
                "npc": "Hoa Yên",
                "objective": "Chuẩn bị cho cuộc phiêu lưu",
                "description": "Hoa Yên: 'Bạn sẵn sàng rồi! Giang hồ rất rộng lớn, hãy khám phá!'",
                "hint": "Nhấn 'Bắt đầu' để bước vào thế giới Tu Tiên",
                "reward": "100 exp, 'Tân Thủ' badge",
                "required_progress": {"tutorial_complete": True}
            }
        ]

    def advance_step(self, step_requirement: Dict) -> Dict:
        """Check if tutorial step is complete"""
        if self.current_step >= len(self.get_tutorial_steps()):
            return {"complete": True, "message": "Hướng dẫn đã hoàn tất!"}

        current_tutorial_step = self.get_tutorial_steps()[self.current_step]

        if all(step_requirement.get(k, 0) >= v for k, v in
               current_tutorial_step["required_progress"].items()):
            self.steps_completed.append(self.current_step)
            self.current_step += 1

            if self.current_step < len(self.get_tutorial_steps()):
                next_step = self.get_tutorial_steps()[self.current_step]
                return {
                    "completed": current_tutorial_step["name"],
                    "reward": current_tutorial_step["reward"],
                    "next_objective": next_step["objective"],
                    "next_hint": next_step["hint"]
                }
            else:
                return {
                    "completed": current_tutorial_step["name"],
                    "reward": current_tutorial_step["reward"],
                    "message": "🎓 Hướng dẫn hoàn tất! Hãy tiếp tục cuộc phiêu lưu."
                }

        return {
            "incomplete": True,
            "hint": current_tutorial_step["hint"],
            "progress": step_requirement
        }

    def get_current_step_hint(self) -> str:
        """Get hint for current step"""
        if self.current_step < len(self.get_tutorial_steps()):
            return self.get_tutorial_steps()[self.current_step]["hint"]
        return ""


class HelpMenu:
    """In-game help and mechanics explanation"""

    def __init__(self):
        self.help_topics = self._initialize_help()

    def _initialize_help(self) -> Dict[str, str]:
        """Define all help topics"""
        return {
            "cultivation": {
                "title": "🧘 Tu Luyện - Cách Tăng Cấp Bậc",
                "content": """
Tu luyện là cơ bản của cuộc sống tu sĩ. Mỗi lần tu luyện:
  • Tăng linh lực (Exp) theo số ngày
  • Tăng áp lực đột phá (Pressure)
  • Khi Exp + Pressure đều đạt 100% → có thể đột phá

Đột phá thành công → Lên cảnh giới mới
Đột phá thất bại → Áp lực reset, linh lực mất 50%
                """
            },
            "realms": {
                "title": "🏔️ Cảnh Giới - 5 Bậc Tu Luyện",
                "content": """
Luyện Khí (1–5): Cơ bản, dễ học kỹ năng
Trúc Cơ (1–5): Trung bình, tăng sức mạnh
Kết Đan (1–5): Khó, kỹ năng mạnh hơn
Nguyên Anh (1–5): Rất khó, kỹ năng siêu quái
Phi Thăng: Tối thượng, unlock endgame challenges
                """
            },
            "skills": {
                "title": "⚔️ Công Pháp - Chiến Đấu & Kỹ Năng",
                "content": """
Kỹ năng là cách chính để gây sát thương:
  • Dùng Linh Lực (QI) mỗi lần dùng
  • Có Cooldown (không thể dùng liên tiếp)
  • Effect: Damage, Heal, Buff, Debuff, CC, DOT, Life Steal

Học kỹ năng mới:
  • Từ NPC bạn bè (hỏi từ Relations tab)
  • Từ tông môn (sect quests)
  • Secret skills (chỉ từ secret realms)
                """
            },
            "sect": {
                "title": "🏯 Tông Môn - Gia Nhập & Phát Triển",
                "content": """
Tông môn là hệ thống quyền lực:
  • Gia nhập tông môn unlock quests
  • Sect Power tăng → status thay đổi
  • Tham gia quests tông môn → Power +10-20
  • Tông môn mạnh → mở territory, quân nhân

4 Tông Môn Chính:
  Thanh Vân: Orthodox, strong
  Hỗn Trâm: Demonic, flexible
  Trinh Đẩu: Neutral, healing-focused
  Ma Tộc: Ancient, powerful
                """
            },
            "branching": {
                "title": "🎭 Branching Quests - Chọn Con Đường",
                "content": """
Branching quests có 2–3 lựa chọn:
  [✓] Orthodox → +Faction reputation, -corruption
  [✗] Demonic → +Corruption, -faction reputation
  [?] Neutral → balanced outcome

Lựa chọn ĐƯỢC GHI NHỚ:
  • NPC nhớ bạn làm gì
  • Ảnh hưởng quest tiếp theo
  • Ảnh hưởng ending

Mỗi lựa chọn quan trọng!
                """
            },
            "relationships": {
                "title": "👥 Mối Quan Hệ - NPC Memory",
                "content": """
Mỗi NPC có 0–100 relationship score:
  • +10-20 khi hoàn quest họ
  • +5 khi học kỹ năng từ họ
  • -20 khi từ chối quest họ
  • -50 khi phản bội họ

Quan hệ cao:
  • Unlock special quests
  • Learn powerful skills
  • Get companion in battles

Mối quan hệ lưu lại qua New Game+!
                """
            },
            "world": {
                "title": "🌍 Thế Giới - Sect Dynamics",
                "content": """
Thế giới không tĩnh tại:
  • Tông môn chiến đấu với nhau
  • NPC tự động thực hiện hành động
  • Điều kiện thế giới thay đổi theo năm

Xem được:
  • Sect rankings (power)
  • Regional control (territory %)
  • NPC status (alive/dead/retired)
  • Major world events (wars, deaths)

Hành động của bạn ảnh hưởng thế giới!
                """
            }
        }

    def get_help_topic(self, topic: str) -> Dict:
        """Get help for specific topic"""
        if topic in self.help_topics:
            return self.help_topics[topic]
        return {
            "title": "❌ Chủ Đề Không Tìm Thấy",
            "content": "Chương mục giúp đỡ này chưa có. Hãy quay lại sau."
        }

    def list_all_topics(self) -> List[str]:
        """List all available help topics"""
        return list(self.help_topics.keys())

    def display_help_menu(self) -> str:
        """Display full help menu"""
        menu = "📚 MENU GIÚP ĐỠ:\n\n"
        for i, (key, topic) in enumerate(self.help_topics.items(), 1):
            menu += f"  {i}. {topic['title']}\n"
        return menu


class SettingsMenu:
    """Player settings and preferences"""

    def __init__(self):
        self.settings = {
            "text_size": "normal",  # small, normal, large
            "message_speed": "normal",  # slow, normal, fast
            "auto_confirm": False,  # Some actions auto-confirm
            "language": "vi",  # Vietnamese
            "difficulty": "normal",  # easy, normal, hard
            "show_hints": True,
            "sound_enabled": False  # Placeholder for future
        }

    def update_setting(self, setting_name: str, value: str) -> str:
        """Update a setting"""
        if setting_name not in self.settings:
            return f"❌ Cài đặt '{setting_name}' không tồn tại"

        if setting_name == "text_size":
            if value not in ["small", "normal", "large"]:
                return "❌ Kích thước chữ: small, normal, hoặc large"
            self.settings["text_size"] = value
            return f"✓ Cỡ chữ: {value} (72%, 100%, 130%)"

        elif setting_name == "message_speed":
            if value not in ["slow", "normal", "fast"]:
                return "❌ Tốc độ: slow, normal, hoặc fast"
            self.settings["message_speed"] = value
            return f"✓ Tốc độ tin nhắn: {value} (0.5x, 1x, 2x)"

        elif setting_name == "auto_confirm":
            self.settings["auto_confirm"] = value == "true"
            return f"✓ Xác nhận tự động: {'Bật' if value == 'true' else 'Tắt'}"

        elif setting_name == "show_hints":
            self.settings["show_hints"] = value == "true"
            return f"✓ Hiển thị gợi ý: {'Bật' if value == 'true' else 'Tắt'}"

        return f"✓ Cài đặt '{setting_name}' = {value}"

    def get_settings_menu(self) -> str:
        """Display settings menu"""
        menu = """
⚙️ CÀI ĐẶT TRÒ CHƠI

1. Cỡ Chữ (Text Size)
   Hiện tại: {}
   • /set text_size small
   • /set text_size normal
   • /set text_size large

2. Tốc Độ Tin Nhắn (Message Speed)
   Hiện tại: {}
   • /set message_speed slow
   • /set message_speed normal
   • /set message_speed fast

3. Xác Nhận Tự Động (Auto Confirm)
   Hiện tại: {}
   • /set auto_confirm true (Bật)
   • /set auto_confirm false (Tắt)

4. Hiển Thị Gợi Ý (Show Hints)
   Hiện tại: {}
   • /set show_hints true
   • /set show_hints false

5. Độ Khó (Difficulty)
   Hiện tại: {}
   • easy, normal, hard

6. Lưu & Thoát
   • /save (Lưu game)
   • /quit (Thoát)
""".format(
            self.settings["text_size"],
            self.settings["message_speed"],
            "Bật" if self.settings["auto_confirm"] else "Tắt",
            "Bật" if self.settings["show_hints"] else "Tắt",
            self.settings["difficulty"]
        )
        return menu

    def get_current_settings(self) -> Dict:
        """Get all current settings"""
        return self.settings.copy()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("FINAL POLISH TEST".center(80))
    print("="*80 + "\n")

    # Test 1: Tutorial
    print("1️⃣ TUTORIAL QUEST")
    print("-" * 80)

    tutorial = TutorialQuest()
    steps = tutorial.get_tutorial_steps()

    for step in steps[:2]:
        print(f"\nStep {step['step']}: {step['name']}")
        print(f"  NPC: {step['npc']}")
        print(f"  Objective: {step['objective']}")
        print(f"  Hint: {step['hint']}")
        print(f"  Reward: {step['reward']}")

    print("\n✓ Tutorial system ready for first playthrough")
    print()

    # Test 2: Help Menu
    print("2️⃣ HELP MENU")
    print("-" * 80)

    help_menu = HelpMenu()
    print(help_menu.display_help_menu())

    print("✓ 7 help topics available:")
    print(f"  Topics: {', '.join(help_menu.list_all_topics())}")
    print()

    # Test 3: Settings
    print("3️⃣ SETTINGS MENU")
    print("-" * 80)

    settings = SettingsMenu()
    print(settings.get_settings_menu())

    print("\n✓ Changing settings...")
    print(settings.update_setting("text_size", "large"))
    print(settings.update_setting("message_speed", "fast"))
    print(settings.update_setting("auto_confirm", "true"))

    print()
    print("="*80)
    print("✅ FINAL POLISH COMPLETE".center(80))
    print("="*80 + "\n")
