"""
Balance smoke tests.
Run from project root with: python tools/balance_test.py
"""

import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from engine.core.loader import Loader
from engine.systems.combat import CombatSystem
from engine.systems.cultivation import CultivationSystem
from engine.systems.technique import TechniqueSystem


def simulate_fights():
    combat = CombatSystem()
    tech = TechniqueSystem()
    enemies = Loader.load("data/entities/enemies.csv")
    player = {
        "name": "Tester",
        "realm_id": "qi_refining",
        "root_id": "metal",
        "exp": 0,
        "technique_slots": ["metal_slash", "earth_guard", None, None],
        "inventory": {},
    }
    print("Combat win rate, 100 runs")
    print("+----------------------+----------+")
    print("| Enemy                | Win Rate |")
    print("+----------------------+----------+")
    for enemy in enemies:
        if enemy["realm_id"] != "qi_refining":
            continue
        wins = 0
        for _ in range(100):
            p_state = combat.spawn_player_combat(player)
            e_state = combat.spawn_enemy(enemy["id"])
            for _turn in range(40):
                usable = [
                    tid for tid in player["technique_slots"]
                    if tid and p_state["mp"] >= int(tech.techniques[tid]["mp_cost"])
                ]
                if usable:
                    combat.player_turn(random.choice(usable), p_state, e_state)
                else:
                    combat._regen_mp(p_state)
                result = combat.is_over(p_state, e_state)
                if result:
                    wins += result == "win"
                    break
                combat.enemy_skill_turn(e_state, p_state, tech.techniques)
                result = combat.is_over(p_state, e_state)
                if result:
                    wins += result == "win"
                    break
        print(f"| {enemy['name_vn'][:20]:20} | {wins:7}% |")
    print("+----------------------+----------+")


def simulate_cultivation():
    cult = CultivationSystem()
    roots = Loader.load("data/entities/spiritual_roots.csv")
    realms = Loader.load("data/entities/realms.csv")
    print()
    print("Cultivation months to next realm")
    print("+--------------+----------------+--------+")
    print("| Root         | Target         | Months |")
    print("+--------------+----------------+--------+")
    for root in roots:
        exp = 0
        months = 0
        for realm in realms[1:]:
            required = int(realm["exp_required"])
            while exp < required:
                months += 1
                exp += cult.calc_exp(1, root["id"])
            print(f"| {root['name_vn'][:12]:12} | {realm['name_vn'][:14]:14} | {months:6} |")
    print("+--------------+----------------+--------+")


if __name__ == "__main__":
    simulate_fights()
    simulate_cultivation()
