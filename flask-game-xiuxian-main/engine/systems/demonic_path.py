"""
Demonic Path System - Con đường tà đạo.

Ma tu ≠ Ma tộc:
- Ma tộc: chủng tộc, sẵn có từ đầu game
- Ma tu: tà đạo, công pháp biến dị, bất kể chủng tộc
"""

import random
from engine.core.loader import Loader

DEMONIC_SKILLS_PATH = "data/entities/demonic_skills.csv"

# Demonic realm progression
DEMONIC_REALMS = [
    {"id": None, "name": "Chưa bước vào tà đạo", "corruption_min": 0, "corruption_max": -1},
    {"id": "ta_khi", "name": "Tà Khí", "corruption_min": 1, "corruption_max": 25},
    {"id": "ta_luyen", "name": "Tà Luyện", "corruption_min": 26, "corruption_max": 50},
    {"id": "hoa_ma", "name": "Hỏa Ma", "corruption_min": 51, "corruption_max": 75},
    {"id": "tuyet_ac", "name": "Tuyệt Ác", "corruption_min": 76, "corruption_max": 100},
]


class DemonicPathSystem:
    def __init__(self):
        self.demonic_skills = Loader.load_by_id(DEMONIC_SKILLS_PATH)

    def get_demonic_realm(self, corruption: int) -> dict:
        """Get demonic realm based on corruption level."""
        for realm in DEMONIC_REALMS:
            if realm["id"] is None:
                continue
            if realm["corruption_min"] <= corruption <= realm["corruption_max"]:
                return realm
        # Return Tuyệt Ác if above max
        if corruption > 75:
            return DEMONIC_REALMS[-1]
        return DEMONIC_REALMS[0]

    def learn_demonic_skill(self, player: dict, skill_id: str) -> dict:
        """
        Called when player learns a demonic skill.
        Returns event info if this is a milestone.
        """
        skill = self.demonic_skills.get(skill_id)
        if not skill:
            return {"success": False, "message": "Không tìm thấy kỹ năng."}

        is_forbidden = int(skill.get("forbidden", 0)) == 1
        corruption_cost = int(skill.get("corruption_cost", 10))

        # First demonic skill - trigger "Bước vào tà đạo"
        if player.get("demonic_arts_count", 0) == 0:
            player["is_demonic"] = True
            player["demonic_arts_count"] = 1
            player["demonic_corruption"] = corruption_cost
            player["demonic_realm"] = self.get_demonic_realm(corruption_cost)["id"]

            return {
                "success": True,
                "event": "enter_demonic_path",
                "message": "Ngươi đã bước vào con đường không thể quay lại. Tà đạo đã mở ra trước mắt ngươi.",
                "corruption_gained": corruption_cost,
            }

        # Additional demonic skills
        player["demonic_arts_count"] = player.get("demonic_arts_count", 0) + 1
        player["demonic_corruption"] = min(100, player.get("demonic_corruption", 0) + corruption_cost)
        player["demonic_realm"] = self.get_demonic_realm(player["demonic_corruption"])["id"]

        return {
            "success": True,
            "event": None,
            "message": f"Đã học {skill.get('name_vn', skill_id)}. Ô nhiễm tà đạo tăng {corruption_cost}.",
            "corruption_gained": corruption_cost,
        }

    def use_demonic_skill(self, player: dict, skill_id: str) -> dict:
        """
        Called when player uses a demonic/forbidden skill in combat.
        Returns corruption gain info.
        """
        skill = self.demonic_skills.get(skill_id)
        if not skill:
            return {"corruption_gained": 0}

        is_forbidden = int(skill.get("forbidden", 0)) == 1
        corruption_cost = int(skill.get("corruption_cost", 10))

        # Forbidden techniques add corruption even without being demonic yet
        if not player.get("is_demonic", False):
            if is_forbidden and player.get("demonic_corruption", 0) >= 30:
                # Trigger entering demonic path
                player["is_demonic"] = True
                player["demonic_realm"] = "ta_khi"
                return {
                    "event": "enter_demonic_path",
                    "message": "Cấm thuật đã mở ra con đường tà đạo. Ngươi không thể quay lại.",
                    "corruption_gained": corruption_cost,
                }
            else:
                player["demonic_corruption"] = min(100, player.get("demonic_corruption", 0) + 5)
                return {
                    "corruption_gained": 5,
                    "message": "Sử dụng cấm thuật. Ô nhiễm tà đạo nhẹ tăng.",
                }

        # Already demonic - add corruption
        player["demonic_corruption"] = min(100, player.get("demonic_corruption", 0) + corruption_cost)
        player["demonic_realm"] = self.get_demonic_realm(player["demonic_corruption"])["id"]

        return {
            "corruption_gained": corruption_cost,
            "message": "Tà đạo dung hợp vào tâm hồn.",
        }

    def accept_demonic_offer(self, player: dict) -> dict:
        """
        Player accepts NPC offer to join demonic path.
        """
        if player.get("is_demonic", False):
            return {"success": False, "message": "Ngươi đã ở trong tà đạo rồi."}

        player["is_demonic"] = True
        player["demonic_corruption"] = 50
        player["demonic_realm"] = "ta_luyen"

        return {
            "success": True,
            "event": "enter_demonic_path",
            "message": "Ngươi đã chấp nhận con đường tà đạo. Quyền lực và nguy hiểm đồng thời mở ra.",
        }

    def can_demonic_breakthrough(self, player: dict, location: str) -> dict:
        """
        Check if player can attempt demonic breakthrough.
        Must be at high corruption and special location.
        """
        if not player.get("is_demonic", False):
            return {"can_breakthrough": False, "reason": "Ngươi không phải Ma tu."}

        corruption = player.get("demonic_corruption", 0)
        if corruption < 80:
            return {"can_breakthrough": False, "reason": f"Ô nhiễm tà đạo chưa đủ (cần ≥80%, hiện tại {corruption}%)."}

        # Check location
        demonic_locations = ["ma_mo", "hang_den", "tuyet_dia", "ma_cot"]
        if location not in demonic_locations:
            return {"can_breakthrough": False, "reason": "Cần địa điểm có ma tính cao để đột phá tà đạo."}

        # Check sect affiliation
        if player.get("sect_id"):
            return {
                "can_breakthrough": False,
                "reason": "Không thể đột phá tà đạo khi còn trong tông môn chính đạo. Sẽ bị phát hiện và khai trừ.",
                "warning": "Nếu tiếp tục, ngươi sẽ bị khai trừ khỏi tông môn!",
            }

        return {"can_breakthrough": True}

    def attempt_demonic_breakthrough(self, player: dict, location: str) -> dict:
        """
        Attempt demonic breakthrough with risk based on location.
        """
        # Location risk levels
        location_data = {
            "ma_mo": {"success_rate": 0.70, "hp_loss": 0, "name": "Mộ cổ"},
            "hang_den": {"success_rate": 0.80, "hp_loss": 20, "name": "Hang động đen"},
            "tuyet_dia": {"success_rate": 0.90, "hp_loss": 50, "name": "Tuyệt địa"},
            "ma_cot": {"success_rate": 0.95, "hp_loss": 80, "name": "Ma cốt"},
        }

        if location not in location_data:
            return {"success": False, "message": "Địa điểm không hợp lệ."}

        loc_info = location_data[location]
        success = random.random() < loc_info["success_rate"]

        if not player.get("is_demonic", False) or player.get("demonic_corruption", 0) < 80:
            return {"success": False, "message": "Không đủ điều kiện đột phá tà đạo."}

        if success:
            player["demonic_breakthroughs"] = player.get("demonic_breakthroughs", 0) + 1
            player["demonic_corruption"] = min(100, player.get("demonic_corruption", 0) + 15)

            # Advance demonic realm
            old_realm = player.get("demonic_realm", "ta_khi")
            realm_order = ["ta_khi", "ta_luyen", "hoa_ma", "tuyet_ac"]
            if old_realm in realm_order:
                idx = realm_order.index(old_realm)
                if idx < len(realm_order) - 1:
                    player["demonic_realm"] = realm_order[idx + 1]

            hp_loss = loc_info["hp_loss"]

            return {
                "success": True,
                "message": f"Đột phá tà đạo thành công! Ma tính ngươi đã tăng lên {player['demonic_realm']}.",
                "hp_loss_percent": hp_loss,
                "corruption_gained": 15,
                "world_event": "Một Ma tu mới đã ra đời!",
            }
        else:
            hp_loss = loc_info["hp_loss"] + 20  # Extra damage on failure

            return {
                "success": False,
                "message": "Đột phá tà đạo thất bại! Linh hồn bị tổn thương nghiêm trọng.",
                "hp_loss_percent": hp_loss,
            }

    def get_corruption_effects(self, player: dict) -> dict:
        """
        Get current effects based on corruption level.
        """
        corruption = player.get("demonic_corruption", 0)

        effects = {
            "damage_bonus": 0,
            "npc_reaction": "neutral",
            "sect_warning": False,
            "locked_content": [],
        }

        if corruption >= 100:
            effects["damage_bonus"] = 40
            effects["npc_reaction"] = "terror"
            effects["locked_content"] = ["orthodox_quests", "orthodox_npcs"]
        elif corruption >= 76:
            effects["damage_bonus"] = 30
            effects["npc_reaction"] = "hostile"
            effects["sect_warning"] = True
        elif corruption >= 51:
            effects["damage_bonus"] = 20
            effects["npc_reaction"] = "suspicious"
            effects["sect_warning"] = True
        elif corruption >= 26:
            effects["damage_bonus"] = 10
            effects["npc_reaction"] = "wary"
        elif corruption >= 1:
            effects["damage_bonus"] = 5
            effects["npc_reaction"] = "neutral"

        return effects
