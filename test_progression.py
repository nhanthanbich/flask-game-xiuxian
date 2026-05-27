#!/usr/bin/env python3
"""
Test script for the new progression and timeline systems.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.core.loader import Loader
from engine.systems.cultivation import CultivationSystem
from engine.systems.npc import NPCSystem
from engine.systems.world import WorldSystem
from engine.systems.time import TimeSystem

def test_cultivation_pressure():
    """Test the cultivation pressure system."""
    print("=" * 60)
    print("TEST 1: Cultivation Pressure System")
    print("=" * 60)

    settings = Loader.load_settings()
    cult = CultivationSystem(settings)

    player = {
        "name": "Test Player",
        "realm_id": "qi_refining_1",
        "root_id": "metal",
        "race_id": "human",
        "exp": 0,
        "technique_slots": [None, None, None, None],
        "inventory": {}
    }

    # Test pressure accumulation
    for i in range(5):
        exp_gain = cult.calc_player_exp(3, player)
        result = cult.add_cultivation_pressure(player, exp_gain)
        status = cult.get_pressure_status(player)
        print(f"Train {i+1}: +{exp_gain} exp, Pressure: {status['pressure']}%, Status: {status['status']}")
        if result.get("event"):
            print(f"  Event: {result['event']} - {result['message']}")

    print()
    pressure = player.get("cultivation_pressure", 0)
    print(f"Final pressure: {pressure}%")

    if pressure > 0:
        print("PASS: Pressure accumulates correctly")
    else:
        print("FAIL: Pressure not accumulating")
        return False

    return True


def test_breakthrough_modes():
    """Test the three breakthrough modes."""
    print("\n" + "=" * 60)
    print("TEST 2: Breakthrough Modes")
    print("=" * 60)

    settings = Loader.load_settings()
    cult = CultivationSystem(settings)

    player = {
        "name": "Test Player",
        "realm_id": "qi_refining_1",
        "root_id": "metal",
        "race_id": "human",
        "exp": 500,
        "technique_slots": [None, None, None, None],
        "inventory": {},
        "cultivation_pressure": 85,
        "breakthrough_ready": True
    }

    # Test wait mode
    result = cult.attempt_breakthrough(player, mode="wait")
    print(f"Wait mode: {result}")
    if result.get('pressure'):
        print("PASS: Wait mode increases pressure")
    else:
        print("FAIL: Wait mode not working")
        return False

    # Test seclusion mode
    player["cultivation_pressure"] = 85
    result = cult.attempt_breakthrough(player, mode="seclusion")
    print(f"Seclusion mode: {result.get('success')} - {result.get('message', result.get('lore', 'No message'))}")

    # Test normal mode
    player["cultivation_pressure"] = 85
    result = cult.attempt_breakthrough(player, mode="normal")
    print(f"Normal mode: {result.get('success')} - {result.get('message', result.get('lore', 'No message'))}")

    return True


def test_breakthrough_thresholds():
    """Ensure breakthrough thresholds are capped and do not force waiting near 100."""
    print("\n" + "=" * 60)
    print("TEST 5: Breakthrough Threshold Balance")
    print("=" * 60)

    settings = Loader.load_settings()
    cult = CultivationSystem(settings)

    thresholds = {
        "qi_refining_1": 10,
        "qi_refining_2": 15,
        "qi_refining_3": 25,
        "foundation_1": 35,
        "foundation_2": 45,
        "foundation_3": 55,
        "core_formation_1": 60,
        "core_formation_2": 65,
        "core_formation_3": 70,
        "nascent_soul_1": 72,
        "nascent_soul_2": 78,
        "nascent_soul_3": 84,
        "deity_transform_1": 85,
        "deity_transform_2": 90,
        "deity_transform_3": 95,
        "great_ascension_1": 95,
        "true_immortal": 95,
    }

    all_passed = True
    for realm_id, expected in thresholds.items():
        actual = cult.breakthrough_pressure_requirement(realm_id)
        print(f"{realm_id}: expected {expected}, actual {actual}")
        if actual != expected:
            all_passed = False

    if all_passed:
        print("PASS: Breakthrough thresholds are balanced.")
    else:
        print("FAIL: Some breakthrough thresholds are not balanced.")

    return all_passed


def test_breakthrough_item_support():
    print("\n" + "=" * 60)
    print("TEST 3: Breakthrough Item Support")
    print("=" * 60)

    settings = Loader.load_settings()
    cult = CultivationSystem(settings)
    player = {
        "name": "Test Player",
        "realm_id": "foundation_1",
        "root_id": "metal",
        "race_id": "human",
        "exp": 2500,
        "technique_slots": [None, None, None, None],
        "inventory": {"qi_pill_major": 1},
        "cultivation_pressure": 85,
        "breakthrough_ready": True,
    }

    result = cult.attempt_breakthrough(player, mode="normal")
    print(f"Breakthrough item result: {result}")
    if result.get("breakthrough_item") == "qi_pill_major":
        print("PASS: Breakthrough item is recognized and consumed if available.")
        return True
    print("FAIL: Breakthrough item logic not working.")
    return False


def test_sect_task_block():
    print("\n" + "=" * 60)
    print("TEST 4: Sect Task Block")
    print("=" * 60)

    settings = Loader.load_settings()
    world = WorldSystem(settings)
    player = {
        "name": "Test Player",
        "inventory": {"stone_pendant": 1},
    }
    world_state = world.default_state()
    world_state["player_sect"] = "cloud_peak"
    world_state["combat_wins"] = 0
    crowd = world.has_ready_sect_task(player, world_state)
    print(f"Ready task while no quest? {crowd}")

    if not crowd:
        print("PASS: No ready task when requirements are unmet.")
    else:
        print("FAIL: Invalid ready task detection.")
        return False

    # Create an available item quest and satisfy it
    quest = next(q for q in world.sect_quests.values() if q["type"] == "item" and q["sect_id"] == "cloud_peak")
    player["inventory"][quest["target_id"]] = int(quest["required_qty"])
    world_state["player_sect"] = quest["sect_id"]
    if world.has_ready_sect_task(player, world_state):
        print("PASS: Ready sect task is detected correctly.")
        return True
    print("FAIL: Sect task ready state not detected.")
    return False


def test_npc_timelines():
    """Test the NPC timeline system."""
    print("\n" + "=" * 60)
    print("TEST 3: NPC Timeline System")
    print("=" * 60)

    npc_system = NPCSystem()

    # Check if timelines loaded
    if not npc_system.timelines:
        print("FAIL: No timelines loaded")
        return False

    print(f"Loaded {len(npc_system.timelines)} NPC timeline events")

    # Test timeline processing
    game_state = {
        "player": {
            "name": "Test Player",
            "realm_id": "foundation_1",
            "sect_id": None
        },
        "world_state": {
            "player_sect": None,
            "sect_power": {},
            "npc_events_fired": []
        }
    }

    # Test at year 5
    events = npc_system.process_npc_timelines(5, game_state)
    print(f"Year 5 events: {len(events)}")
    for event in events:
        print(f"  - {event}")

    # Test at year 10
    events = npc_system.process_npc_timelines(10, game_state)
    print(f"Year 10 events: {len(events)}")
    for event in events:
        print(f"  - {event}")

    return True


def test_world_tick():
    """Test the world tick system."""
    print("\n" + "=" * 60)
    print("TEST 4: World Tick System")
    print("=" * 60)

    settings = Loader.load_settings()
    world = WorldSystem(settings)

    world_state = world.default_state()
    time = TimeSystem(year=1, month=1, day=1)

    # Initial state
    print(f"Initial sect powers: {len(world_state['sect_power'])} sects")

    # Simulate 10 years
    logs = []
    for year in range(1, 11):
        time.year = year
        time.month = 1
        result_logs = world.tick(time, world_state)
        if result_logs:
            logs.extend(result_logs)
            print(f"Year {year}: {len(result_logs)} events")

    if logs:
        print(f"PASS: World tick generated {len(logs)} events")
        for log in logs[:5]:  # Show first 5
            print(f"  - {log}")
        return True
    else:
        print("FAIL: No world events generated")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PROGRESSION AND TIMELINE SYSTEM TEST SUITE")
    print("=" * 60)

    tests = [
        ("Cultivation Pressure", test_cultivation_pressure),
        ("Breakthrough Modes", test_breakthrough_modes),
        ("Breakthrough Threshold Balance", test_breakthrough_thresholds),
        ("NPC Timelines", test_npc_timelines),
        ("World Tick", test_world_tick),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\nALL TESTS PASSED")
        return 0
    else:
        print(f"\n{failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit(main())
