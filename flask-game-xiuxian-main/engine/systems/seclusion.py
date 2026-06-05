"""
Seclusion System - Bế Quan.

Bế quan để tu luyện tập trung, thời gian trôi nhanh hơn bình thường,
nhưng mất liên hệ với thế giới.
"""

import random
from engine.core.loader import Loader


class SeclusionSystem:
    def __init__(self):
        self.settings = Loader.load_settings()

    # Seclusion locations with their multipliers and costs
    SECLUSION_LOCATIONS = {
        "sect_grounds": {
            "name": "Tông Môn",
            "time_multiplier": 1.5,
            "cost_type": "sect_contribution",
            "cost_amount": 10,
            "danger_chance": 0.0,
            "description": "Nơi bế quan an toàn trong tông môn.",
        },
        "mountain_cave": {
            "name": "Động Núi Riêng",
            "time_multiplier": 1.3,
            "cost_type": "supplies",
            "cost_amount": 5,
            "danger_chance": 0.05,
            "description": "Động riêng trên núi, yên tĩnh nhưng hơi khắc nghiệt.",
        },
        "secret_realm": {
            "name": "Bí Cảnh Vừa Khám Phá",
            "time_multiplier": 2.0,
            "cost_type": "risk",
            "cost_amount": 0,
            "danger_chance": 0.10,
            "description": "Linh khí dồi dào nhưng nguy hiểm, yêu thú có thể tấn công.",
        },
    }

    def start_seclusion(self, player: dict, location: str, duration_days: int, world_state: dict) -> dict:
        """
        Start a seclusion session.
        Returns info about seclusion starting.
        """
        if player.get("in_seclusion", False):
            return {"success": False, "message": "Đang trong bế quan rồi."}

        if location not in self.SECLUSION_LOCATIONS:
            return {"success": False, "message": "Địa điểm không hợp lệ."}

        loc_info = self.SECLUSION_LOCATIONS[location]

        # Check cost
        cost_type = loc_info["cost_type"]
        cost_amount = loc_info["cost_amount"]

        if cost_type == "sect_contribution":
            sect_contrib = world_state.get("sect_contrib", 0)
            if sect_contrib < cost_amount:
                return {
                    "success": False,
                    "message": f"Cần {cost_amount} công trạng tông môn (hiện có: {sect_contrib}).",
                }
            # Deduct cost
            world_state["sect_contrib"] = sect_contrib - cost_amount

        elif cost_type == "supplies":
            # Check inventory for supplies
            inventory = player.get("inventory", {})
            # Simplified: just check if has any items
            total_items = sum(inventory.values()) if inventory else 0
            if total_items < cost_amount:
                return {
                    "success": False,
                    "message": f"Cần {cost_amount} vật phẩm tiêu hao.",
                }

        # Start seclusion
        player["in_seclusion"] = True
        player["seclusion_location"] = location
        player["seclusion_duration_remaining"] = duration_days

        # Record start date (year, month)
        from engine.systems.time import TimeSystem
        # Time will be set by caller

        return {
            "success": True,
            "message": f"Bắt đầu bế quan tại {loc_info['name']} trong {duration_days} ngày.",
            "time_multiplier": loc_info["time_multiplier"],
            "location_info": loc_info,
        }

    def process_seclusion_day(self, player: dict, world_state: dict) -> dict:
        """
        Process one day of seclusion.
        Returns any events that occurred (monster attacks, etc).
        """
        if not player.get("in_seclusion", False):
            return {"event": None}

        location = player.get("seclusion_location", "")
        loc_info = self.SECLUSION_LOCATIONS.get(location)

        if not loc_info:
            return {"event": None}

        # Decrease duration
        player["seclusion_duration_remaining"] = player.get("seclusion_duration_remaining", 0) - 1

        # Check if finished
        if player["seclusion_duration_remaining"] <= 0:
            return self._end_seclusion(player, world_state)

        # Check for monster attack
        danger_chance = loc_info.get("danger_chance", 0)
        if random.random() < danger_chance:
            return {
                "event": "monster_attack",
                "message": "Yêu thú tấn công trong lúc bế quan!",
                "enemy_type": "secret_realm_monster",
            }

        return {"event": None}

    def _end_seclusion(self, player: dict, world_state: dict) -> dict:
        """
        End seclusion and return consequences.
        """
        location = player.get("seclusion_location", "")
        loc_info = self.SECLUSION_LOCATIONS.get(location, {})
        duration = player.get("seclusion_duration_remaining", 0)

        # Calculate total days in seclusion
        start_date = player.get("seclusion_start_date")
        if start_date:
            # Calculate actual days passed
            from engine.systems.time import TimeSystem
            # This will be set by caller
            total_days = duration
        else:
            total_days = duration

        # Reset seclusion state
        player["in_seclusion"] = False
        player["seclusion_location"] = None
        player["seclusion_duration_remaining"] = 0
        player["seclusion_start_date"] = None

        # Check for social consequences
        consequences = self._calculate_social_consequences(total_days, player, world_state)

        return {
            "event": "seclusion_end",
            "message": f"Kết thúc bế quan sau {total_days} ngày tại {loc_info.get('name', 'không rõ')}.",
            "days_passed": total_days,
            "consequences": consequences,
        }

    def _calculate_social_consequences(self, days: int, player: dict, world_state: dict) -> dict:
        """
        Calculate social consequences of long seclusion.
        """
        consequences = {
            "sect_warning": False,
            "npc_reactions": [],
            "world_changes": [],
        }

        # Convert days to game years (360 days per year)
        years = days / 360

        if years >= 1.0:
            # Long seclusion - major consequences
            sect_id = world_state.get("player_sect")
            if sect_id:
                # Check sect rank
                rank = world_state.get("player_rank", 1)
                if rank <= 2:  # Low rank disciples may be expelled
                    consequences["sect_warning"] = True
                    consequences["npc_reactions"].append(
                        "Tông môn cân nhắc việc khai trừ do vắng mặt quá lâu."
                    )

                consequences["world_changes"].append(
                    "Tông môn quyền lực thay đổi trong lúc ngươi vắng mặt."
                )

            # NPC relationship decay
            consequences["npc_reactions"].append(
                "Một số NPC quen biết đã thay đổi tính cách hoặc quên ngươi."
            )

        elif years >= 0.5:  # 6 months
            # Medium seclusion - minor consequences
            consequences["npc_reactions"].append(
                "NPC ngạc nhiên: 'Cậu biến mất nửa năm nay!'"
            )

        return consequences

    def get_available_locations(self, player: dict, world_state: dict) -> list:
        """
        Get list of available seclusion locations for player.
        """
        locations = []

        # Always available
        locations.append({
            "id": "mountain_cave",
            **self.SECLUSION_LOCATIONS["mountain_cave"],
            "available": True,
        })

        # Sect grounds - only if in a sect
        sect_id = world_state.get("player_sect")
        if sect_id:
            locations.append({
                "id": "sect_grounds",
                **self.SECLUSION_LOCATIONS["sect_grounds"],
                "available": True,
            })

        # Secret realm - only if cleared one
        cleared_realms = player.get("secret_realms_cleared", [])
        if cleared_realms:
            locations.append({
                "id": "secret_realm",
                **self.SECLUSION_LOCATIONS["secret_realm"],
                "available": True,
            })

        return locations
