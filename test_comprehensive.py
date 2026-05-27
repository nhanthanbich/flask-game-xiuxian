#!/usr/bin/env python3
"""
Comprehensive error detection test.
Tests for edge cases and potential runtime errors.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flavor_system_edge_cases():
    """Test edge cases in flavor system."""
    print("=" * 60)
    print("TEST 1: Flavor System Edge Cases")
    print("=" * 60)
    
    from engine.core.flavor import FlavorSystem
    flavor = FlavorSystem()
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1.1: Empty realm ID
    result = flavor.get("cultivation", "")
    if result:
        print("✓ Empty realm_id returns fallback flavor")
        tests_passed += 1
    else:
        print("✗ Empty realm_id failed")
        tests_failed += 1
    
    # Test 1.2: Invalid realm ID
    result = flavor.get("cultivation", "nonexistent_realm")
    if result:
        print("✓ Invalid realm_id returns fallback flavor")
        tests_passed += 1
    else:
        print("✗ Invalid realm_id failed")
        tests_failed += 1
    
    # Test 1.3: Invalid category
    result = flavor.get("nonexistent_category", "qi_refining_1")
    if result == "":
        print("✓ Invalid category returns empty string")
        tests_passed += 1
    else:
        print("✗ Invalid category returned unexpected value")
        tests_failed += 1
    
    # Test 1.4: All categories for all realms
    all_realms = set()
    for row in flavor.rows:
        if row["realm_id"] != "realm_id":
            all_realms.add(row["realm_id"])
    
    categories = ["cultivation", "breakthrough", "combat_win", "combat_lose", "quest_complete", "rank_up"]
    for realm in all_realms:
        for cat in categories:
            result = flavor.get(cat, realm)
            if not result or len(result.strip()) == 0:
                print(f"✗ Missing flavor: {cat} / {realm}")
                tests_failed += 1
    
    if tests_failed == 0:
        print(f"✓ All {len(all_realms)} realms × {len(categories)} categories checked")
        tests_passed += 1
    
    return tests_passed, tests_failed

def test_game_initialization():
    """Test game initialization for potential errors."""
    print("\n" + "=" * 60)
    print("TEST 2: Game Initialization")
    print("=" * 60)
    
    try:
        from engine.core.game import Game
        game = Game()
        
        checks = [
            ("FlavorSystem", game.flavor is not None),
            ("CultivationSystem", game.cult is not None),
            ("TechniqueSystem", game.tech is not None),
            ("ItemSystem", game.items is not None),
            ("CombatSystem", game.combat is not None),
            ("WorldSystem", game.world is not None),
            ("NPCSystem", game.npc is not None),
            ("CultivationTab", game.cult_tab is not None and game.cult_tab.flavor is not None),
            ("SectTab", game.sect_tab is not None and game.sect_tab.flavor is not None),
            ("CombatUI", game.combat_ui is not None and game.combat_ui.flavor is not None),
        ]
        
        tests_passed = 0
        tests_failed = 0
        
        for name, result in checks:
            if result:
                print(f"✓ {name} initialized correctly")
                tests_passed += 1
            else:
                print(f"✗ {name} failed")
                tests_failed += 1
        
        return tests_passed, tests_failed
    
    except Exception as e:
        print(f"✗ Game initialization error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1

def test_sect_tab_methods():
    """Test SectTab methods for errors."""
    print("\n" + "=" * 60)
    print("TEST 3: SectTab Methods")
    print("=" * 60)
    
    try:
        from engine.core.game import Game
        from engine.systems.world import WorldSystem
        from engine.core.loader import Loader
        
        game = Game()
        settings = Loader.load_settings()
        
        player = {
            "name": "Test User",
            "realm_id": "qi_refining_1",
            "root_id": "metal",
            "race_id": "human",
            "exp": 0,
            "technique_slots": [None, None, None, None],
            "inventory": {},
        }
        
        world_state = game.world.default_state()
        
        # Test join sect
        available = game.world.get_available_sects(player)
        if available:
            sect = available[0]
            if game.world.join_sect(player, world_state, sect["id"]):
                print(f"✓ Can join sect: {sect['name_vn']}")
                
                # Test rank up
                if game.sect_tab.flavor:
                    print("✓ SectTab has flavor system")
                    
                    # Check if quest_complete flavor exists
                    quest_flavor = game.sect_tab.flavor.get("quest_complete", player["realm_id"])
                    if quest_flavor:
                        print(f"✓ Quest flavor retrievable in SectTab")
                    else:
                        print("✗ Quest flavor not found in SectTab")
                        return 0, 1
                    
                    # Check if rank_up flavor exists
                    rankup_flavor = game.sect_tab.flavor.get("rank_up", player["realm_id"])
                    if rankup_flavor:
                        print(f"✓ Rank up flavor retrievable in SectTab")
                    else:
                        print("✗ Rank up flavor not found in SectTab")
                        return 0, 1
                
                return 1, 0
            else:
                print("✗ Failed to join sect")
                return 0, 1
        else:
            print("✗ No sects available for testing")
            return 0, 1
    
    except Exception as e:
        print(f"✗ SectTab test error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1

def test_world_system():
    """Test WorldSystem for potential errors."""
    print("\n" + "=" * 60)
    print("TEST 4: World System")
    print("=" * 60)
    
    try:
        from engine.systems.world import WorldSystem
        from engine.core.loader import Loader
        
        settings = Loader.load_settings()
        world = WorldSystem(settings)
        
        tests_passed = 0
        tests_failed = 0
        
        # Test default state
        state = world.default_state()
        if state and "sect_power" in state and "events_fired" in state:
            print("✓ Default state has all required fields")
            tests_passed += 1
        else:
            print("✗ Default state missing required fields")
            tests_failed += 1
        
        # Test sects loading
        if len(world.sects) > 0:
            print(f"✓ {len(world.sects)} sects loaded")
            tests_passed += 1
        else:
            print("✗ No sects loaded")
            tests_failed += 1
        
        # Test events loading
        if len(world.events) > 0:
            print(f"✓ {len(world.events)} world events loaded")
            tests_passed += 1
        else:
            print("✗ No world events loaded")
            tests_failed += 1
        
        return tests_passed, tests_failed
    
    except Exception as e:
        print(f"✗ WorldSystem test error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1

def test_npc_system():
    """Test NPCSystem for potential errors."""
    print("\n" + "=" * 60)
    print("TEST 5: NPC System")
    print("=" * 60)
    
    try:
        from engine.systems.npc import NPCSystem
        
        npc = NPCSystem()
        
        tests_passed = 0
        tests_failed = 0
        
        if len(npc.npcs) > 0:
            print(f"✓ {len(npc.npcs)} NPCs loaded")
            tests_passed += 1
            
            # Test NPC relation
            test_npc = list(npc.npcs.values())[0]
            player = {"name": "Test"}
            world_state = {"npc_relations": {}}
            
            relation = npc.get_relation(player, test_npc["id"], world_state)
            if relation and "respect" in relation:
                print("✓ NPC relations work correctly")
                tests_passed += 1
            else:
                print("✗ NPC relations failed")
                tests_failed += 1
        else:
            print("✗ No NPCs loaded")
            tests_failed += 1
        
        return tests_passed, tests_failed
    
    except Exception as e:
        print(f"✗ NPCSystem test error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1

def test_csv_integrity():
    """Test CSV files for corruption."""
    print("\n" + "=" * 60)
    print("TEST 6: Data File Integrity")
    print("=" * 60)
    
    try:
        import csv
        
        csv_files = [
            "data/text/flavors.csv",
            "data/entities/enemies.csv",
            "data/entities/items.csv",
            "data/entities/npcs.csv",
            "data/entities/sects.csv",
            "data/entities/techniques.csv",
        ]
        
        tests_passed = 0
        tests_failed = 0
        
        for csv_file in csv_files:
            try:
                if os.path.exists(csv_file):
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        rows = list(reader)
                        if len(rows) > 0:
                            print(f"✓ {csv_file}: {len(rows)} rows")
                            tests_passed += 1
                        else:
                            print(f"✗ {csv_file}: No data rows")
                            tests_failed += 1
                else:
                    print(f"⚠ {csv_file}: File not found")
            except Exception as e:
                print(f"✗ {csv_file}: {e}")
                tests_failed += 1
        
        return tests_passed, tests_failed
    
    except Exception as e:
        print(f"✗ CSV integrity test error: {e}")
        import traceback
        traceback.print_exc()
        return 0, 1

def main():
    """Run all comprehensive tests."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE ERROR DETECTION TEST SUITE")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    
    # Run all tests
    p, f = test_flavor_system_edge_cases()
    total_passed += p
    total_failed += f
    
    p, f = test_game_initialization()
    total_passed += p
    total_failed += f
    
    p, f = test_sect_tab_methods()
    total_passed += p
    total_failed += f
    
    p, f = test_world_system()
    total_passed += p
    total_failed += f
    
    p, f = test_npc_system()
    total_passed += p
    total_failed += f
    
    p, f = test_csv_integrity()
    total_passed += p
    total_failed += f
    
    # Print summary
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    print(f"✓ Tests Passed: {total_passed}")
    print(f"✗ Tests Failed: {total_failed}")
    
    if total_failed == 0:
        print("\n✓✓✓ ALL TESTS PASSED - NO ERRORS DETECTED ✓✓✓")
        return 0
    else:
        print(f"\n✗✗✗ {total_failed} TEST(S) FAILED ✗✗✗")
        return 1

if __name__ == "__main__":
    exit(main())
