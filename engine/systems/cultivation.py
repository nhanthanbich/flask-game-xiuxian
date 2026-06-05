"""
cultivation.py
Xử lý tu luyện: tính exp, đột phá có rủi ro, hiển thị tiến độ.

Quy tắc exp:
  - Đơn hệ linh căn + cùng hệ công pháp  → exp_multiplier        (x1.5, nhanh)
  - Đơn hệ linh căn + khác hệ công pháp  → off_element_multiplier (x0.6, chậm)
  - Ngũ Hành Linh Căn                    → exp_multiplier         (x0.7, mọi hệ đều nhau)
  - technique_element=None               → dùng exp_multiplier    (tu luyện chung)

Rủi ro đột phá:
  breakthrough_risk  = xác suất thất bại (0.0–1.0), tăng dần theo cảnh giới
  failure_skip_months = số tháng bị tổn thất khi thất bại
"""

import random
from engine.core.loader import Loader
from engine.systems.technique import REALM_ORDER

REALMS_PATH = "data/entities/realms.csv"
ROOTS_PATH  = "data/entities/spiritual_roots.csv"

ELEMENT_TO_ROOT = {
    "Kim": "metal", "Mộc": "wood",
    "Thủy": "water", "Hỏa": "fire", "Thổ": "earth",
}


class CultivationSystem:

    def __init__(self, settings: dict | None = None):
        self.settings = settings or {}
        self.realms   = Loader.load_by_id(REALMS_PATH)
        self.roots    = Loader.load_by_id(ROOTS_PATH)
        self.pressure_multipliers = self.settings.get("pressure_multipliers", {
            0: 0.00,  # Mortal has almost no pressure buildup
            1: 0.14, 2: 0.12, 3: 0.10,  # Qi Refining stays lightweight and onboarding-friendly
            4: 0.10, 5: 0.11, 6: 0.12,  # Foundation begins to matter
            7: 0.12, 8: 0.13, 9: 0.14,  # Core Formation becomes meaningful
            10: 0.15, 11: 0.16, 12: 0.17,  # Nascent Soul brings instability
            13: 0.18, 14: 0.19, 15: 0.20,  # Deity Transformation is oppressive
            16: 0.21, 17: 0.21, 18: 0.22,
            19: 0.22, 20: 0.23, 21: 0.23,
            22: 0.24, 23: 0.24, 24: 0.24,
            25: 0.24, 26: 0.24, 27: 0.24,
            28: 0.24,
        })

        # Build backward compatibility mapping for old realm IDs
        self._build_legacy_mapping()

    def _build_legacy_mapping(self):
        """
        Build mapping from old realm IDs (qi_refining) to new IDs (qi_refining_1).
        For backward compatibility with old saves.
        """
        self.legacy_realm_map = {}
        for realm_id in self.realms:
            # Map old format to first sub-realm
            # e.g., "qi_refining" -> "qi_refining_1"
            base_name = realm_id.rsplit('_', 1)[0] if '_' in realm_id else realm_id
            if base_name not in self.legacy_realm_map and realm_id.endswith('_1'):
                self.legacy_realm_map[base_name] = realm_id

        # Special mappings for old realm names
        legacy_mappings = {
            'qi_refining': 'qi_refining_1',
            'foundation': 'foundation_1',
            'core_formation': 'core_formation_1',
            'nascent_soul': 'nascent_soul_1',
            'deity_transform': 'deity_transform_1',
            'ascension': 'great_ascension_1',  # ascension -> great_ascension_1
        }
        for old_id, new_id in legacy_mappings.items():
            if old_id not in self.legacy_realm_map:
                self.legacy_realm_map[old_id] = new_id

    def normalize_realm_id(self, realm_id: str) -> str:
        """
        Normalize realm_id for backward compatibility.
        Converts old IDs (qi_refining) to new IDs (qi_refining_1).
        """
        if realm_id in self.realms:
            return realm_id
        # Check legacy mapping
        return self.legacy_realm_map.get(realm_id, realm_id)

    # ── Tính exp ────────────────────────────────────────────────────────
    def calc_exp(self, months: int, root_id: str,
                 technique_element: str | None = None) -> int:
        """
        Tính exp tu luyện theo tháng, linh căn và hệ công pháp.
        technique_element=None → tu luyện chung, dùng exp_multiplier.
        """
        root     = self.roots[root_id]
        base     = float(self.settings.get("base_exp_per_month", 10))
        exp_rate = float(self.settings.get("exp_rate", 1.0))

        if root_id == "five_elements" or technique_element is None:
            mult = float(root["exp_multiplier"])
        else:
            same = ELEMENT_TO_ROOT.get(technique_element) == root_id
            mult = float(root["exp_multiplier"]) if same \
                   else float(root["off_element_multiplier"])

        return max(int(base * months * mult * exp_rate), 1)

    def calc_player_exp(self, months: int, player: dict,
                        race_system=None,
                        technique_element: str | None = None) -> int:
        """Tính exp có tính thêm race multiplier nếu truyền vào."""
        exp = self.calc_exp(months, player["root_id"], technique_element)
        if race_system:
            exp = int(exp * race_system.cultivation_mult(
                player.get("race_id", "human")))
        return exp

    def _pressure_multiplier_for_realm(self, realm_id: str) -> float:
        """Lấy hệ số áp lực theo cảnh giới hiện tại."""
        realm_id = self.normalize_realm_id(realm_id)
        realm = self.realms.get(realm_id)
        if not realm:
            return 0.12
        level = int(realm.get("level", 0))
        return self.pressure_multipliers.get(level, 0.30)

    def breakthrough_pressure_requirement(self, realm_id: str | None = None) -> int:
        """
        Trả về ngưỡng áp lực cần thiết để đột phá từ cảnh giới hiện tại.

        NEW DESIGN: Early realms (Luyện Khí) have NO pressure requirement.
        Pressure only becomes a meaningful mechanic in mid+ realms.

        Realm Level Mapping:
        - 0: Mortal (threshold: 0)
        - 1-3: Luyện Khí (threshold: 0) - NO pressure gate
        - 4-5: Early/Mid Trúc Cơ (threshold: 15)
        - 6: Late Trúc Cơ (threshold: 25)
        - 7-9: Kim Đan (threshold: 40/50/60)
        - 10-12: Nguyên Anh (threshold: 65/72/80)
        - 13-15: Hóa Thần (threshold: 85/90/95)
        - 16+: (threshold: 95)
        """
        realm_id = self.normalize_realm_id(realm_id or "mortal")
        realm = self.realms.get(realm_id, {"level": 0})
        level = int(realm.get("level", 0))

        # New threshold structure
        if level == 0:  # Mortal
            return 0
        elif level <= 3:  # Luyện Khí (levels 1-3)
            return 0  # NO pressure requirement
        elif level == 4:  # Early Trúc Cơ
            return 15
        elif level == 5:  # Mid Trúc Cơ
            return 15
        elif level == 6:  # Late Trúc Cơ
            return 25
        elif level == 7:  # Early Kim Đan
            return 40
        elif level == 8:  # Mid Kim Đan
            return 50
        elif level == 9:  # Late Kim Đan
            return 60
        elif level == 10:  # Early Nguyên Anh
            return 65
        elif level == 11:  # Mid Nguyên Anh
            return 72
        elif level == 12:  # Late Nguyên Anh
            return 80
        elif level == 13:  # Early Hóa Thần
            return 85
        elif level == 14:  # Mid Hóa Thần
            return 90
        elif level == 15:  # Late Hóa Thần
            return 95
        else:  # Level 16+
            return 95

    def get_breakthrough_item_id(self, realm: dict) -> str | None:
        item_id = realm.get("breakthrough_item")
        return item_id if item_id else None

    def apply_pressure_to_exp(self, player: dict, exp_gained: int) -> tuple[int, str | None]:
        """
        Áp dụng áp lực vào hiệu quả tu luyện hiện tại.

        NEW DESIGN: Penalties only apply in mid+ realms.
        Luyện Khí and early Trúc Cơ have NO exp penalties from pressure.
        """
        pressure = player.get("cultivation_pressure", 0)
        realm_id = player.get("realm_id", "mortal")
        realm = self.realms.get(realm_id, {"level": 0})
        level = int(realm.get("level", 0))
        message = None

        # No penalties for early realms (Mortal, Luyện Khí, early Trúc Cơ)
        if level <= 5:
            return exp_gained, None

        # Penalties start from late Trúc Cơ onwards
        if pressure >= 95:
            if random.random() < 0.30:
                adjusted = max(1, int(exp_gained * 0.5))
                message = "Linh khí hỗn loạn, tu lực chỉ còn một nửa thu hoạch."
            else:
                adjusted = max(1, int(exp_gained * 0.85))
                message = "Áp lực đột phá khiến công lực giảm nhẹ."
        elif pressure >= 85:
            if random.random() < 0.20:
                adjusted = max(1, int(exp_gained * 0.6))
                message = "Một phần tu lực bị tiêu hao do nội tâm không ổn."
            else:
                adjusted = max(1, int(exp_gained * 0.9))
        else:
            adjusted = exp_gained

        return adjusted, message

    # ── Hệ thống áp lực tu luyện ───────────────────────────────────────────
    def add_cultivation_pressure(self, player: dict, exp_gained: int):
        """Thêm áp lực tu luyện khi tích lũy linh lực."""
        pressure = player.setdefault("cultivation_pressure", 0)
        multiplier = self._pressure_multiplier_for_realm(player.get("realm_id", "mortal"))
        pressure += int(exp_gained * multiplier)
        pressure = min(pressure, 100)
        player["cultivation_pressure"] = pressure

        # Kiểm tra ngưỡng
        return self._check_pressure_threshold(player, pressure)

    def _check_pressure_threshold(self, player: dict, pressure: int) -> dict:
        """
        Kiểm tra ngưỡng áp lực và trả về thông báo.

        NEW DESIGN: Tẩu hỏa nhập ma only happens in mid+ realms.
        """
        realm_id = player.get("realm_id", "mortal")
        realm = self.realms.get(realm_id, {"level": 0})
        level = int(realm.get("level", 0))

        # No tẩu hỏa nhập ma for early realms (Mortal, Luyện Khí, early Trúc Cơ)
        if level <= 5:
            # Light flavor text only
            if pressure >= 80:
                return {"event": None, "message": "Linh khí dồn nén, cảm thấy hơi khó chịu."}
            return {"event": None, "message": None}

        # Tẩu hỏa nhập ma only from late Trúc Cơ onwards
        if pressure >= 100:
            # Tẩu hỏa nhập ma
            player["cultivation_pressure"] = 60
            return {
                "event": "táu_hoả_nhập_ma",
                "message": "Áp lực tu luyện quá lớn! Thiên địa linh khí phản phệ — ngươi bị tẩu hỏa nhập ma!",
                "hp_loss_percent": random.randint(20, 40)
            }
        elif pressure >= 95:
            player["breakthrough_ready"] = True
            return {
                "event": "pressure_critical",
                "message": "Nội tâm nóng như ngọn lửa thượng nguyên, đột phá đã trở thành cơn bão không thể trì hoãn!",
                "flavor": "Làn khí hỗn loạn lan tỏa, bầu không khí xung quanh như rung chuyển dưới chân ngươi."
            }
        elif pressure >= 85:
            return {
                "event": "pressure_high",
                "message": "Linh khí bất ổn, tu lực bắt đầu hao tổn không đều.",
                "flavor": "Không khí quanh đỉnh đầu ngươi mỏng manh như vải, tiếng gió vang như thì thầm."
            }
        elif pressure >= 70:
            return {
                "event": "pressure_unstable",
                "message": "Nội tâm không còn thuần nhất, tu lực trở nên bất ổn và khó điều hòa.",
                "flavor": "Những âm thanh nhỏ và luồng khí lạ vờn quanh trống ngực ngươi."
            }
        return {"event": None, "message": None}

    def get_pressure_status(self, player: dict) -> dict:
        """Lấy trạng thái áp lực hiện tại."""
        pressure = player.get("cultivation_pressure", 0)
        breakthrough_ready = player.get("breakthrough_ready", False)
        breakthrough_risk = player.get("breakthrough_risk", 0)

        status = "ổn_định"
        if pressure >= 95:
            status = "critical"
        elif pressure >= 80:
            status = "warning"
        elif pressure >= 60:
            status = "high"

        return {
            "pressure": pressure,
            "status": status,
            "breakthrough_ready": breakthrough_ready,
            "breakthrough_risk": breakthrough_risk
        }

    def increase_breakthrough_risk(self, player: dict):
        """Tăng rủi ro khi trì hoãn đột phá."""
        risk = player.get("breakthrough_risk", 0)
        risk = min(risk + 10, 100)
        player["breakthrough_risk"] = risk

        pressure = player.get("cultivation_pressure", 0)
        pressure = min(pressure + 5, 100)
        player["cultivation_pressure"] = pressure

    def reset_pressure(self, player: dict):
        """Reset áp lực sau khi đột phá thành công.

        Lower realms retain a light momentum after breakthrough,
        while higher realms are allowed a deeper spiritual reset.
        """
        realm_id = self.normalize_realm_id(player.get("realm_id", "mortal"))
        level = int(self.realms.get(realm_id, {}).get("level", 0))

        if level <= 3:
            player["cultivation_pressure"] = random.randint(10, 20)
        elif level <= 6:
            player["cultivation_pressure"] = random.randint(5, 12)
        elif level <= 12:
            player["cultivation_pressure"] = random.randint(0, 8)
        else:
            player["cultivation_pressure"] = 0

        player["breakthrough_ready"] = False
        player["breakthrough_risk"] = 0

    # ── Cảnh giới tiếp theo ─────────────────────────────────────────────
    def next_realm(self, realm_id: str) -> dict | None:
        # Normalize realm_id for backward compatibility
        realm_id = self.normalize_realm_id(realm_id)

        if realm_id not in self.realms:
            return None

        current_level = int(self.realms[realm_id]["level"])
        for r in Loader.load(REALMS_PATH):
            if int(r["level"]) == current_level + 1:
                return r
        return None

    def can_breakthrough(self, player: dict) -> bool:
        nxt = self.next_realm(player["realm_id"])
        return bool(nxt and player.get("exp", 0) >= int(nxt.get("exp_required", 0)))

    # ── Đột phá ─────────────────────────────────────────────────────────
    def get_breakthrough_info(self, player: dict) -> dict:
        """Trả về thông tin đột phá: sẵn sàng, rủi ro, ngưỡng áp lực và điều kiện."""
        nxt = self.next_realm(player["realm_id"])
        if nxt is None:
            return {
                "ready": False,
                "next": None,
                "risk": 0.0,
                "failure_skip_months": 0,
                "breakthrough_item": "",
                "pressure_required": 0,
                "pressure_ready": True,
            }
        required = int(nxt.get("exp_required", 0))
        pressure_required = self.breakthrough_pressure_requirement(player["realm_id"])
        pressure_current = player.get("cultivation_pressure", 0)
        return {
            "ready":                player.get("exp", 0) >= required,
            "next":                 nxt,
            "risk":                 float(nxt.get("breakthrough_risk", 0.0)),
            "failure_skip_months":  int(nxt.get("failure_skip_months", 0)),
            "breakthrough_item":    nxt.get("breakthrough_item", ""),
            "pressure_required":    pressure_required,
            "pressure_ready":       pressure_current >= pressure_required,
        }

    def attempt_breakthrough(self, player: dict, mode: str = "normal") -> dict:
        """
        Thử đột phá với 3 chế độ:
          - "normal": Đột phá ngay (60% + pressure_bonus 20%)
          - "seclusion": Bế quan đột phá (85%, mất 1-3 tháng)
          - "wait": Chờ thêm (+5 pressure, +10 risk)

        Trả về:
          Thành công: {"success": True, "realm": nxt, "lore": str}
          Thất bại:  {"success": False, "failure_skip_months": N, "message": str}
        """
        pressure = player.get("cultivation_pressure", 0)
        realm_id = self.normalize_realm_id(player.get("realm_id", "mortal"))
        realm_level = int(self.realms.get(realm_id, {}).get("level", 0))

        # Kiểm tra điều kiện
        if mode in ["normal", "seclusion"]:
            pressure_threshold = self.breakthrough_pressure_requirement(player.get("realm_id", "mortal"))
            if pressure < pressure_threshold:
                return {
                    "success": False,
                    "message": f"Áp lực chưa đủ để đột phá. Cần {pressure_threshold}% áp lực.",
                    "failure_skip_months": 0,
                }

        info = self.get_breakthrough_info(player)
        if not info["ready"] and info["next"] is None:
            return {"success": False, "message": "Chưa đủ điều kiện đột phá.", "failure_skip_months": 0}

        nxt = info["next"]
        if nxt is None:
            return {"success": False, "message": "Đã đạt cảnh giới tối cao.", "failure_skip_months": 0}

        item_id = info.get("breakthrough_item")
        item_bonus = 0.0
        item_used = False
        if item_id and player.get("inventory", {}).get(item_id, 0) > 0 and mode != "wait":
            inv = player.setdefault("inventory", {})
            inv[item_id] -= 1
            if inv[item_id] <= 0:
                del inv[item_id]
            item_used = True
            item_bonus = 0.10

        # Tính tỷ lệ thành công theo chế độ
        if mode == "normal":
            base_rate = 0.60
            pressure_bonus = (pressure / 100) * 0.20
            success_rate = base_rate + pressure_bonus + item_bonus
            failure_damage = 30
            failure_pressure = 50

        elif mode == "seclusion":
            success_rate = 0.85 + item_bonus
            failure_damage = 15
            failure_pressure = 60

        elif mode == "wait":
            self.increase_breakthrough_risk(player)
            danger_risk = player.get("breakthrough_risk", 0)
            return {
                "success": False,
                "message": f"Chờ thêm. Áp lực +5, Rủi ro +10 (hiện tại {danger_risk}%).",
                "pressure": player.get("cultivation_pressure", 0),
                "risk": danger_risk,
                "advance_months": 1,
                "failure_skip_months": 0
            }

        else:
            return {"success": False, "message": "Chế độ đột phá không hợp lệ.", "failure_skip_months": 0}

        # Thử đột phá
        # Early cultivation should feel fast and forgiving; serious failure starts later.
        if realm_level <= 3:
            success_rate = 1.0
            failure_damage = 0
            failure_pressure = min(30, player.get("cultivation_pressure", 0))
        elif realm_level <= 5:
            success_rate = max(success_rate, 0.92)
            failure_damage = min(failure_damage, 5)
            failure_pressure = min(failure_pressure, 35)
        elif realm_level == 6:
            success_rate = max(success_rate, 0.85)
            failure_damage = min(failure_damage, 10)
            failure_pressure = min(failure_pressure, 45)

        skip = info["failure_skip_months"]

        if random.random() < success_rate:
            # Thành công
            player["realm_id"] = nxt["id"]
            lore = self._get_breakthrough_lore(nxt["id"])
            self.reset_pressure(player)
            return {
                "success": True,
                "realm": nxt,
                "lore": lore,
                "seclusion_time": random.randint(1, 3) if mode == "seclusion" else 0,
                "breakthrough_item": item_id,
                "item_used": item_used
            }
        else:
            # Thất bại
            player["cultivation_pressure"] = failure_pressure
            player["breakthrough_ready"] = False

            return {
                "success": False,
                "failure_skip_months": skip,
                "hp_loss_percent": failure_damage,
                "breakthrough_item": item_id,
                "item_used": item_used,
                "message": (
                    f"Đột phá thất bại! Thiên lôi giáng xuống —"
                    f" mất {skip} tháng dưỡng thương, tổn hại {failure_damage}% sinh lực."
                    if skip
                    else f"Đột phá thất bại! Căn cơ chưa vững, mất {failure_damage}% sinh lực."
                ),
            }

    def _get_breakthrough_lore(self, realm_id: str) -> str:
        """Lấy đoạn văn học đột phá cho từng cảnh giới."""
        lore_texts = {
            "qi_refining_1": "Linh khí lần đầu lưu thông trong kinh mạch, như suối nguồn chảy qua đất khô.",
            "qi_refining_2": "Kinh mạch mở rộng, linh khí tuôn như thác đổ qua vực sâu.",
            "qi_refining_3": "Thân thể đạt cực hạn Luyện Khí, một bước nữa là Trúc Cơ.",
            "foundation_1": "Nền móng đạo cơ thành hình, như núi non vươn lên từ biển cả.",
            "foundation_2": "Đạo cơ thêm vững, mỗi hơi thở đều kéo theo linh khí thiên địa.",
            "foundation_3": "Kim đan manh nha trong đan điền, như sao mai le lói lúc bình minh.",
            "core_formation_1": "Kim đan ngưng tụ, tinh cầu rực sáng trong đan điền.",
            "core_formation_2": "Kim đan thêm chắc, thần thức mở rộng ra ngoài thân.",
            "core_formation_3": "Kim đan đạt cực hạn, nguyên anh đang hình thành bên trong.",
            "nascent_soul_1": "Nguyên anh xuất khiếu, thần hồn rời thân thể và nhìn xuống phàm giới.",
            "nascent_soul_2": "Nguyên anh lớn mạnh, có thể tồn tại độc lập với thể xác.",
            "nascent_soul_3": "Nguyên anh đạt đỉnh, một niệm có thể chạm đến mây trời.",
            "deity_transform_1": "Thần ý hòa vào thiên địa, cảm nhận được vạn vật như phần cơ thể mình.",
            "deity_transform_2": "Thần thức trải rộng trăm dặm, mỗi ý niệm đều mang theo ý thiên địa.",
            "deity_transform_3": "Hóa Thần cực hạn, thân thể như đã trở thành một với thế giới.",
        }
        return lore_texts.get(realm_id, "Ánh sáng rực rỡ bao trùm thân thể — ngươi đã bước qua ranh giới.")

    def do_breakthrough(self, player: dict) -> dict:
        """Đột phá không rủi ro — dùng khi game đã confirm từ trước."""
        nxt = self.next_realm(player["realm_id"])
        player["realm_id"] = nxt["id"]
        return nxt

    # ── Hiển thị ────────────────────────────────────────────────────────
    def realm_display(self, realm_id: str) -> str:
        # Normalize for backward compatibility
        realm_id = self.normalize_realm_id(realm_id)

        if realm_id not in self.realms:
            return "Cảnh Giới Không Xác Định"

        r = self.realms[realm_id]
        return f"{r['name_vn']} ({r['name']})"

    def root_display(self, root_id: str) -> str:
        root = self.roots[root_id]
        if root_id == "five_elements":
            return (f"{root['name_vn']} — {root['element']}  |  "
                    f"x{root['exp_multiplier']} exp (mọi hệ đều nhau)")
        return (f"{root['name_vn']} — {root['element']} hệ  |  "
                f"x{root['exp_multiplier']} (cùng hệ)  "
                f"x{root['off_element_multiplier']} (khác hệ)")

    def exp_progress(self, player: dict) -> str:
        nxt = self.next_realm(player["realm_id"])
        if nxt is None:
            return "Đã đạt cảnh giới tối cao."
        current  = player["exp"]
        required = int(nxt["exp_required"])
        pct      = min(int(current / required * 20), 20)
        bar      = "█" * pct + "░" * (20 - pct)
        return f"[{bar}] {current:,} / {required:,} exp → {nxt['name_vn']}"

    def get_seclusion_durations(self, realm_id: str) -> list[tuple[int, str]]:
        """
        Trả về danh sách các lựa chọn thời gian bế quan dựa trên cảnh giới.
        Trả về list của (số_tháng, mô_tả_hiển_thị)

        NEW DESIGN: Early realms use VERY SHORT durations.
        Luyện Khí: days only
        Trúc Cơ: months only (no years before Kim Đan)

        Tier 1 (Mortal/Qi Refining): Days - rapid growth
        Tier 2 (Foundation): Months (1-6 months)
        Tier 3 (Core Formation): Months to 1 year
        Tier 4 (Nascent Soul): Years
        Tier 5 (Deity Transformation): Decades
        Tier 6+ (Void Refinement+): Centuries
        """
        realm_index = self.get_realm_index(realm_id)

        # Tier 1: Mortal / Qi Refining (0-3) - ONLY DAYS
        if realm_index <= 3:
            return [
                (0.1, "3 ngày"),   # 3 days
                (0.23, "7 ngày"),  # 7 days
                (1, "1 tháng"),    # 1 month
            ]

        # Tier 2: Foundation (4-6) - ONLY MONTHS (no years)
        elif realm_index <= 6:
            return [
                (1, "1 tháng"),
                (3, "3 tháng"),
                (6, "6 tháng"),
            ]

        # Tier 3: Core Formation (7-9) - Months to 1 year
        elif realm_index <= 9:
            return [
                (6, "6 tháng"),
                (12, "1 năm"),
                (36, "3 năm"),
            ]

        # Tier 4: Nascent Soul (10-12) - Years
        elif realm_index <= 12:
            return [
                (12, "1 năm"),
                (36, "3 năm"),
                (60, "5 năm"),
                (120, "10 năm"),
            ]

        # Tier 5: Deity Transformation (13-15) - Decades
        elif realm_index <= 15:
            return [
                (60, "5 năm"),
                (120, "10 năm"),
                (240, "20 năm"),
                (600, "50 năm"),
            ]

        # Tier 6+: Void Refinement and beyond (16+) - Centuries
        else:
            return [
                (240, "20 năm"),
                (600, "50 năm"),
                (1200, "100 năm"),
                (3600, "300 năm"),
            ]

    def get_realm_index(self, realm_id: str) -> int:
        """Get the numeric index of a realm for comparison."""
        try:
            return REALM_ORDER.index(realm_id)
        except (ValueError, NameError):
            # Fallback: parse from realm_id
            base_realm = realm_id.split('_')[0] if '_' in realm_id else realm_id
            for idx, r_id in enumerate(REALM_ORDER):
                if r_id == base_realm or r_id.startswith(base_realm):
                    return idx
            return 0

    def get_cultivation_flavor(self, realm_id: str, months: float) -> str:
        """
        Trả về flavor text phù hợp với cảnh giới và thời gian tu luyện.

        Args:
            realm_id: ID cảnh giới hiện tại
            months: Số tháng tu luyện

        Returns:
            Flavor text mô tả quá trình tu luyện
        """
        realm_index = self.get_realm_index(realm_id)
        realm_name = self.realms.get(realm_id, {}).get("name_vn", realm_id)

        # Convert months to readable format
        if months < 1:
            days = int(months * 30)
            time_desc = f"{days} ngày"
        elif months < 12:
            time_desc = f"{int(months)} tháng"
        elif months < 120:
            years = int(months / 12)
            time_desc = f"{years} năm"
        elif months < 1200:
            decades = int(months / 120)
            time_desc = f"{decades} thập kỷ"
        elif months < 12000:
            centuries = int(months / 1200)
            time_desc = f"{centuries} thế kỷ"
        else:
            millennia = int(months / 12000)
            time_desc = f"{millennia} thiên niên kỷ"

        # Tier-specific flavor
        # Tier 1: Mortal / Qi Refining
        if realm_index <= 3:
            flavors = [
                f"Ngươi vận chuyển linh khí suốt {time_desc}, cảm nhận thiên địa trở nên gần gũi hơn.",
                f"{time_desc} bế quan, ngươi hấp thụ linh khí thiên địa, tu vi tăng tiến.",
                f"Trong {time_desc}, ngươi cảm nhận được sự biến đổi của cơ thể.",
                f"Linh khí tuôn chảy trong {time_desc}, một bước nhỏ trên con đường tu tiên.",
            ]

        # Tier 2: Foundation
        elif realm_index <= 6:
            flavors = [
                f"Suốt {time_desc}, ngươi kiến tạo nền móng vững chắc cho đạo tu.",
                f"{time_desc} khổ tu, căn cơ dần ổn định.",
                f"Trong {time_desc}, ngươi cảm nhận được chân khí ngưng tụ.",
                f"Thời gian {time_desc} trôi qua, nền móng đạo tâm vững như bàn thạch.",
            ]

        # Tier 3: Core Formation
        elif realm_index <= 9:
            flavors = [
                f"Suốt {time_desc}, ngươi ngưng luyện kim đan, cảm nhận sức mạnh tập trung.",
                f"{time_desc} tu luyện, chánh niệm kiên định như kim cương.",
                f"Trong {time_desc}, chân khí hóa hình, chuẩn bị cho bước nhảy vọt.",
                f"Thời gian {time_desc} trôi qua trong nhập định, tu vi thăng hoa.",
            ]

        # Tier 4: Nascent Soul
        elif realm_index <= 12:
            flavors = [
                f"{time_desc} trôi qua trong một lần nhập định, nguyên anh dần hình thành.",
                f"Suốt {time_desc}, ngươi cảm nhận linh hồn thoát xác, đạt tới cảnh giới mới.",
                f"Trong {time_desc}, một lần giác ngộ như ngàn năm tu hành.",
                f"Thời gian {time_desc} như đại mộng, nguyên anh ngưng tụ, đạo tâm kiên định.",
            ]

        # Tier 5: Deity Transformation
        elif realm_index <= 15:
            flavors = [
                f"Một lần bế quan {time_desc}, thế gian đã đổi vài thế hệ.",
                f"Suốt {time_desc}, ngươi siêu thoát phàm trần, xúc cảm thần thánh.",
                f"Trong {time_desc}, ngươi chứng kiến tuần hoàn của thiên địa.",
                f"Thời gian {time_desc} dài đằng đẵng, nhưng ngươi đã vượt qua phàm tục.",
            ]

        # Tier 6+: Void Refinement and beyond
        else:
            flavors = [
                f"{time_desc} tu hành, ngươi đã vượt qua giới hạn của thời gian.",
                f"Suốt {time_desc}, ngươi chứng kiến sự hưng thịnh và tàn lụi của vạn vật.",
                f"Trong {time_desc}, ngươi như hòa mình vào hư không, không còn ràng buộc.",
                f"Thời gian {time_desc} vô nghĩa với kẻ đã bước vào con đường bất tử.",
            ]

        return random.choice(flavors)

    def breakthrough_display(self, player: dict) -> str:
        """Hiển thị rủi ro đột phá cảnh giới tiếp theo."""
        info = self.get_breakthrough_info(player)
        nxt  = info["next"]
        if nxt is None:
            return ""
        risk_pct = int(info["risk"] * 100)
        skip     = info["failure_skip_months"]
        return (f"Đột phá → {nxt['name_vn']}  |  "
                f"Rủi ro: {risk_pct}%  |  "
                f"Thất bại mất: {skip} tháng")

    def is_same_element(self, root_id: str, technique_element: str) -> bool:
        if root_id == "five_elements":
            return False
        return ELEMENT_TO_ROOT.get(technique_element) == root_id
    