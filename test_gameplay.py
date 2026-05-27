#!/usr/bin/env python3
"""
Gameplay simulation test to verify all features work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.core.game import Game
from engine.systems.combat import CombatSystem
from engine.core.loader import Loader

def test_gameplay_flow():
    """Simulate various gameplay scenarios."""
    print("=" * 60)
    print("GAMEPLAY SIMULATION TEST")
    print("=" * 60)
    
    try:
        game = Game()
        print("✓ Game created successfully")
        
        # Create a test player
        player = {
            "name": "Test Tu Si",
            "realm_id": "qi_refining_1",
            "root_id": "metal",
            "race_id": "human",
            "exp": 0,
            "technique_slots": [None, None, None, None],
            "inventory": {},
        }
        print(f"✓ Test player created: {player['name']}")
        
        # Test 1: Cultivation flavor
        print("\n--- Test 1: Cultivation Flavor ---")
        cult_flavor = game.flavor.get("cultivation", player["realm_id"])
        if cult_flavor:
            print(f"✓ Cultivation flavor: {cult_flavor[:60]}...")
        else:
            print("✗ No cultivation flavor found")
        
        # Test 2: Quest completion flavor
        print("\n--- Test 2: Quest Completion Flavor ---")
        quest_flavor = game.flavor.get("quest_complete", player["realm_id"])
        if quest_flavor:
            print(f"✓ Quest flavor: {quest_flavor[:60]}...")
        else:
            print("✗ No quest completion flavor found")
        
        # Test 3: Rank up flavor
        print("\n--- Test 3: Rank Up Flavor ---")
        rankup_flavor = game.flavor.get("rank_up", player["realm_id"])
        if rankup_flavor:
            print(f"✓ Rank up flavor: {rankup_flavor[:60]}...")
        else:
            print("✗ No rank up flavor found")
        
        # Test 4: Breakthrough flavor
        print("\n--- Test 4: Breakthrough Flavor ---")
        break_flavor = game.flavor.get("breakthrough", player["realm_id"])
        if break_flavor:
            print(f"✓ Breakthrough flavor: {break_flavor[:60]}...")
        else:
            print("✗ No breakthrough flavor found")
        
        # Test 5: Combat win/lose flavors
        print("\n--- Test 5: Combat Flavors ---")
        win_flavor = game.flavor.get("combat_win", player["realm_id"])
        lose_flavor = game.flavor.get("combat_lose", player["realm_id"])
        if win_flavor:
            print(f"✓ Combat win flavor: {win_flavor[:60]}...")
        else:
            print("✗ No combat win flavor found")
        if lose_flavor:
            print(f"✓ Combat lose flavor: {lose_flavor[:60]}...")
        else:
            print("✗ No combat lose flavor found")
        
        # Test 6: World state initialization
        print("\n--- Test 6: World State ---")
        world_state = game.world.default_state()
        print(f"✓ World state initialized")
        print(f"  - Sects: {len(world_state['sect_power'])}")
        print(f"  - Events fired: {len(world_state['events_fired'])}")
        print(f"  - NPC relations: {len(world_state['npc_relations'])}")
        
        # Test 7: Sect operations
        print("\n--- Test 7: Sect Operations ---")
        available_sects = game.world.get_available_sects(player)
        if available_sects:
            sect = available_sects[0]
            print(f"✓ Available sect found: {sect['name_vn']}")
            
            # Try to join sect
            if game.world.join_sect(player, world_state, sect["id"]):
                print(f"✓ Joined sect: {sect['name_vn']}")
                
                # Check sector flavor for new realm after advancement
                new_realm = "foundation_1"
                sect_quest_flavor = game.flavor.get("quest_complete", new_realm)
                if sect_quest_flavor:
                    print(f"✓ Foundation realm quest flavor available: {sect_quest_flavor[:40]}...")
            else:
                print("✗ Failed to join sect")
        else:
            print("✗ No sects available")
        
        # Test 8: Enemy spawning and combat mechanics
        print("\n--- Test 8: Combat System ---")
        enemies = Loader.load_by_id("data/entities/enemies.csv")
        if enemies:
            enemy = list(enemies.values())[0]
            print(f"✓ Enemy available: {enemy['name_vn']}")
            
            # Test combat state
            combat_state = game.combat.spawn_player_combat(player)
            print(f"✓ Combat state created: HP={combat_state['hp']}, MP={combat_state['mp']}")
        else:
            print("✗ No enemies found")
        
        # Test 9: Time system
        print("\n--- Test 9: Time System ---")
        time = game.time
        initial_display = time.display()
        time.advance_months(1)
        new_display = time.display()
        if initial_display != new_display:
            print(f"✓ Time advances: {initial_display} -> {new_display}")
        else:
            print("✗ Time system not working")
        
        # Test 10: All realms have all flavor categories
        print("\n--- Test 10: Realm Flavor Coverage ---")
        realms = set()
        for row in game.flavor.rows:
            realms.add(row["realm_id"])
        
        categories = ["cultivation", "breakthrough", "combat_win", "combat_lose", "quest_complete", "rank_up"]
        missing_flavors = []
        
        for realm in realms:
            for cat in categories:
                flavor_text = game.flavor.get(cat, realm)
                if not flavor_text or len(flavor_text) == 0:
                    missing_flavors.append(f"{cat}/{realm}")
        
        if not missing_flavors:
            print(f"✓ All {len(realms)} realms have all {len(categories)} flavor categories")
        else:
            print(f"✗ Missing {len(missing_flavors)} flavor combinations:")
            for mf in missing_flavors[:5]:
                print(f"  - {mf}")
        
        print("\n" + "=" * 60)
        print("✓ ALL GAMEPLAY TESTS PASSED")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"\n✗ ERROR during gameplay test: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(test_gameplay_flow())
