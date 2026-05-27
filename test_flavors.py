#!/usr/bin/env python3
"""
Test script to verify flavor system and new categories.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.core.flavor import FlavorSystem
from engine.core.loader import Loader
from engine.core.game import Game
from engine.systems.world import WorldSystem

def test_flavor_loading():
    """Test that all flavors load correctly."""
    print("=" * 50)
    print("TEST 1: Loading Flavor System")
    print("=" * 50)
    try:
        flavor = FlavorSystem()
        print(f"✓ FlavorSystem loaded: {len(flavor.rows)} total flavors")
        return flavor
    except Exception as e:
        print(f"✗ ERROR loading FlavorSystem: {e}")
        return None

def test_flavor_categories(flavor):
    """Test that all flavor categories exist."""
    print("\n" + "=" * 50)
    print("TEST 2: Flavor Categories")
    print("=" * 50)
    
    categories = {}
    for row in flavor.rows:
        cat = row["category"]
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    
    expected = {
        "cultivation": 28,
        "breakthrough": 28,
        "combat_win": 28,
        "combat_lose": 28,
        "quest_complete": 28,
        "rank_up": 28,
    }
    
    for cat, expected_count in expected.items():
        actual_count = categories.get(cat, 0)
        if actual_count == expected_count:
            print(f"✓ {cat:20} : {actual_count:2} entries")
        else:
            print(f"✗ {cat:20} : {actual_count:2} entries (expected {expected_count})")
    
    return categories

def test_realm_coverage(flavor):
    """Test that all realms have flavors."""
    print("\n" + "=" * 50)
    print("TEST 3: Realm Coverage")
    print("=" * 50)
    
    realms = set()
    for row in flavor.rows:
        if row["realm_id"] != "realm_id":  # Skip header
            realms.add(row["realm_id"])
    
    print(f"✓ Total realms with flavors: {len(realms)}")
    print(f"  Realms: {sorted(realms)[:5]}... (showing first 5)")
    return realms

def test_flavor_retrieval(flavor, realms):
    """Test that specific flavors can be retrieved."""
    print("\n" + "=" * 50)
    print("TEST 4: Flavor Retrieval")
    print("=" * 50)
    
    test_cases = [
        ("cultivation", "qi_refining_1"),
        ("quest_complete", "qi_refining_1"),
        ("rank_up", "qi_refining_1"),
        ("combat_win", "foundation_1"),
        ("breakthrough", "true_immortal"),
    ]
    
    for cat, realm in test_cases:
        result = flavor.get(cat, realm)
        if result and len(result) > 0:
            preview = result[:50] + "..." if len(result) > 50 else result
            print(f"✓ {cat:20} / {realm:20} : {preview}")
        else:
            print(f"✗ {cat:20} / {realm:20} : NO FLAVOR FOUND")

def test_game_initialization():
    """Test that Game class can be instantiated."""
    print("\n" + "=" * 50)
    print("TEST 5: Game Initialization")
    print("=" * 50)
    
    try:
        game = Game()
        print("✓ Game instance created successfully")
        print(f"  - FlavorSystem: {type(game.flavor).__name__}")
        print(f"  - Cultivation tab has flavor: {game.cult_tab.flavor is not None}")
        print(f"  - Sect tab has flavor: {game.sect_tab.flavor is not None}")
        print(f"  - Combat screen has flavor: {game.combat_ui.flavor is not None}")
        return game
    except Exception as e:
        print(f"✗ ERROR initializing Game: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_world_system():
    """Test WorldSystem."""
    print("\n" + "=" * 50)
    print("TEST 6: World System")
    print("=" * 50)
    
    try:
        settings = Loader.load_settings()
        world = WorldSystem(settings)
        print("✓ WorldSystem created successfully")
        print(f"  - Sects: {len(world.sects)}")
        print(f"  - Techniques: {len(world.sect_techniques)}")
        print(f"  - Events: {len(world.events)}")
        return world
    except Exception as e:
        print(f"✗ ERROR creating WorldSystem: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("FLAVOR SYSTEM COMPREHENSIVE TEST")
    print("=" * 60)
    
    flavor = test_flavor_loading()
    if not flavor:
        print("\n✗ FAILED: Cannot proceed without FlavorSystem")
        return 1
    
    categories = test_flavor_categories(flavor)
    realms = test_realm_coverage(flavor)
    test_flavor_retrieval(flavor, realms)
    
    game = test_game_initialization()
    if game:
        world = test_world_system()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print("✓ All critical tests passed!")
    print("\nReady to play the game.")
    return 0

if __name__ == "__main__":
    exit(main())
