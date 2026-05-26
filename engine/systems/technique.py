"""
Technique system.
"""

from engine.core.loader import Loader

MAX_SLOTS = 4

REALMS_PATH = "data/entities/realms.csv"
TECHNIQUES_PATH = "data/entities/techniques.csv"

# Dynamically load REALM_ORDER from CSV to support expanded realms
def _load_realm_order():
    """Load realm order from CSV, sorted by level."""
    realms = Loader.load(REALMS_PATH)
    sorted_realms = sorted(realms, key=lambda r: int(r.get("level", 0)))
    return [r["id"] for r in sorted_realms]

REALM_ORDER = _load_realm_order()


class TechniqueSystem:
    def __init__(self):
        self.techniques = {
            row["id"]: self._normalize(row)
            for row in Loader.load(TECHNIQUES_PATH)
        }

    def ensure_slots(self, player: dict):
        slots = player.setdefault("technique_slots", [])
        if len(slots) < MAX_SLOTS:
            slots.extend([None] * (MAX_SLOTS - len(slots)))
        elif len(slots) > MAX_SLOTS:
            del slots[MAX_SLOTS:]

    def get_realm_index(self, realm_id: str) -> int:
        """Get realm index with safe fallback."""
        try:
            return REALM_ORDER.index(realm_id)
        except ValueError:
            # Fallback: try to find by base realm name
            base_realm = realm_id.rsplit('_', 1)[0] if '_' in realm_id else realm_id
            for idx, r_id in enumerate(REALM_ORDER):
                if r_id == base_realm or r_id.startswith(base_realm):
                    return idx
            # Return lowest level if not found
            return 0

    def get_learnable(self, realm_id: str) -> list[dict]:
        realm_level = self.get_realm_index(realm_id)
        return [
            t for t in self.techniques.values()
            if self.get_realm_index(t["realm_id"]) <= realm_level
        ]

    def learn(self, player: dict, technique_id: str, slot_index: int):
        if technique_id not in self.techniques:
            raise KeyError(f"Unknown technique: {technique_id}")
        if not 0 <= slot_index < MAX_SLOTS:
            raise IndexError(f"Slot must be between 0 and {MAX_SLOTS - 1}")

        self.ensure_slots(player)
        player["technique_slots"][slot_index] = technique_id

    def remove(self, player: dict, slot_index: int):
        if not 0 <= slot_index < MAX_SLOTS:
            raise IndexError(f"Slot must be between 0 and {MAX_SLOTS - 1}")
        self.ensure_slots(player)
        player["technique_slots"][slot_index] = None

    def has_any(self, player: dict) -> bool:
        self.ensure_slots(player)
        return any(player["technique_slots"])

    def get_slot_display(self, player: dict) -> list[str]:
        self.ensure_slots(player)
        lines = []
        for idx, tid in enumerate(player["technique_slots"], 1):
            if not tid:
                lines.append(f"Slot {idx}: Trong")
                continue

            tech = self.techniques.get(tid)
            if tech is None:
                lines.append(f"Slot {idx}: {tid} (khong tim thay)")
                continue

            lines.append(
                f"Slot {idx}: {tech['name_vn']} | {tech['element']} | "
                f"MP:{tech['mp_cost']} | {tech['description']}"
            )
        return lines

    def get_slot_display_combat(self, player: dict, mp: int | None = None) -> list[str]:
        self.ensure_slots(player)
        lines = []
        for idx, tid in enumerate(player["technique_slots"], 1):
            if not tid or tid not in self.techniques:
                continue
            tech = self.techniques[tid]
            suffix = ""
            if mp is not None and mp < int(tech["mp_cost"]):
                suffix = " [thieu MP]"
            lines.append(
                f"{idx}. {tech['name_vn']} | {tech['element']} | "
                f"MP:{tech['mp_cost']} | {tech['description'][:28]}{suffix}"
            )
        return lines

    @staticmethod
    def _normalize(row: dict) -> dict:
        data = dict(row)
        # Support both 'realm_id' and 'req_realm' fields
        data["realm_id"] = data.get("realm_id") or data.get("req_realm") or "qi_refining_1"
        # Ensure all required fields exist with defaults
        data.setdefault("mp_cost", 10)
        data.setdefault("power", 10)
        data.setdefault("effect", "damage")
        data.setdefault("effect_value", 0)
        data.setdefault("element_bonus_mult", 1.0)
        data.setdefault("element", "None")
        data.setdefault("description", "")
        data.setdefault("type", "Pháp thuật")
        return data
