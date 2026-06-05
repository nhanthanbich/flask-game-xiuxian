"""
Race/faction gameplay modifiers.
"""

from engine.core.loader import Loader

RACES_PATH = "data/entities/races.csv"


class RaceSystem:
    def __init__(self):
        self.races = Loader.load_by_id(RACES_PATH)

    def get(self, race_id: str) -> dict:
        return self.races.get(race_id) or self.races["human"]

    def cultivation_mult(self, race_id: str) -> float:
        return float(self.get(race_id)["cultivation_mult"])

    def stat_mults(self, race_id: str) -> dict:
        race = self.get(race_id)
        return {
            "hp": float(race["hp_mult"]),
            "mp": float(race["mp_mult"]),
            "attack": float(race["attack_mult"]),
        }
