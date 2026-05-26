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

    # ── Cảnh giới tiếp theo ─────────────────────────────────────────────
    def next_realm(self, realm_id: str) -> dict | None:
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
        """Trả về thông tin đột phá: sẵn sàng, rủi ro, hậu quả thất bại."""
        nxt = self.next_realm(player["realm_id"])
        if nxt is None:
            return {"ready": False, "next": None, "risk": 0.0, "failure_skip_months": 0}
        required = int(nxt.get("exp_required", 0))
        return {
            "ready":                player.get("exp", 0) >= required,
            "next":                 nxt,
            "risk":                 float(nxt.get("breakthrough_risk", 0.0)),
            "failure_skip_months":  int(nxt.get("failure_skip_months", 0)),
        }

    def attempt_breakthrough(self, player: dict) -> dict:
        """
        Thử đột phá. Trả về:
          Thành công: {"success": True,  "realm": nxt}
          Thất bại:  {"success": False, "failure_skip_months": N, "message": str}
        """
        info = self.get_breakthrough_info(player)
        if not info["ready"] or info["next"] is None:
            return {"success": False, "message": "Chưa đủ điều kiện đột phá.", "failure_skip_months": 0}

        nxt  = info["next"]
        risk = float(self.settings.get("breakthrough_risk_mult", 1.0)) * info["risk"]
        skip = info["failure_skip_months"]

        if random.random() < risk:
            return {
                "success":              False,
                "failure_skip_months":  skip,
                "message": (
                    f"Đột phá thất bại! Thiên lôi giáng xuống — "
                    f"mất {skip} tháng dưỡng thương." if skip
                    else "Đột phá thất bại! Căn cơ chưa vững."
                ),
            }

        player["realm_id"] = nxt["id"]
        return {"success": True, "realm": nxt}

    def do_breakthrough(self, player: dict) -> dict:
        """Đột phá không rủi ro — dùng khi game đã confirm từ trước."""
        nxt = self.next_realm(player["realm_id"])
        player["realm_id"] = nxt["id"]
        return nxt

    # ── Hiển thị ────────────────────────────────────────────────────────
    def realm_display(self, realm_id: str) -> str:
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
    