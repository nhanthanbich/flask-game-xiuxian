"""
Flavor text lookup.
"""

import random

from engine.core.loader import Loader

FLAVORS_PATH = "data/text/flavors.csv"


class FlavorSystem:
    def __init__(self):
        self.rows = Loader.load(FLAVORS_PATH)

    def get(self, category: str, realm_id: str) -> str:
        matches = [
            row["text"] for row in self.rows
            if row["category"] == category and row["realm_id"] == realm_id
        ]
        if not matches:
            matches = [
                row["text"] for row in self.rows
                if row["category"] == category
            ]
        return random.choice(matches) if matches else ""
