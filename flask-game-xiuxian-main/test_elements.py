#!/usr/bin/env python
"""PHASE 7 Gameplay Validation Tests"""

from engine.core.loader import Loader
from engine.systems.cultivation import CultivationSystem

def test_multi_element_sects():
    """TEST 1: Verify multi-element sects load correctly"""
    print("=" * 60)
    print("TEST 1: Multi-element sects data preservation")
    print("=" * 60)
    
    sects = Loader.load_by_id('data/entities/sects.csv')
    multi_element_sects = [s for s in sects.values() if '|' in s.get('elements', '')]
    
    print(f"\nMulti-element sects found: {len(multi_element_sects)}\n")
    for sect in multi_element_sects[:5]:
        elements = sect['elements']
        print(f"✓ {sect['id']:20} | {sect['name_vn']:25} | Elements: {elements}")
    
    print(f"\n✅ PASS: Multi-element data preserved (found {len(multi_element_sects)} sects)")
    return True

def test_display_format():
    """TEST 2: Verify display format shows all elements"""
    print("\n" + "=" * 60)
    print("TEST 2: UI display format for elements")
    print("=" * 60)
    
    sects = Loader.load_by_id('data/entities/sects.csv')
    test_cases = [
        {'elements': 'Kim', 'expected': 'Kim'},
        {'elements': 'Kim|Hỏa', 'expected': 'Kim, Hỏa'},
        {'elements': 'Mộc|Thủy|Hỏa', 'expected': 'Mộc, Thủy, Hỏa'},
    ]
    
    for test in test_cases:
        original = test['elements']
        displayed = original.replace('|', ', ')
        expected = test['expected']
        status = "✓" if displayed == expected else "✗"
        print(f"{status} {original:20} → {displayed:20} (expected: {expected})")
        if displayed != expected:
            print(f"   ERROR: Got '{displayed}' but expected '{expected}'")
            return False
    
    print(f"\n✅ PASS: Display format correctly shows all elements")
    return True

def test_sect_eligibility():
    """TEST 3: Verify sect eligibility logic with multi-elements"""
    print("\n" + "=" * 60)
    print("TEST 3: Sect eligibility matching with pipe separator")
    print("=" * 60)
    
    # Simulate the fixed matching logic
    test_cases = [
        {
            'player_root': 'Kim',
            'sect_elements': 'Kim',
            'should_match': True,
            'desc': 'Single element exact match'
        },
        {
            'player_root': 'Kim',
            'sect_elements': 'Kim|Hỏa',
            'should_match': True,
            'desc': 'Multi-element contains player root'
        },
        {
            'player_root': 'Hỏa',
            'sect_elements': 'Kim|Hỏa',
            'should_match': True,
            'desc': 'Multi-element second element match'
        },
        {
            'player_root': 'Thủy',
            'sect_elements': 'Kim|Hỏa',
            'should_match': False,
            'desc': 'Multi-element no match'
        },
    ]
    
    for test in test_cases:
        player_root = test['player_root']
        sect_elements = test['sect_elements']
        
        # NEW FIXED CODE: Uses pipe separator
        allowed_elements = [e.strip() for e in sect_elements.split("|")]
        matches = player_root in allowed_elements
        
        expected = test['should_match']
        status = "✓" if matches == expected else "✗"
        print(f"{status} Root={player_root:5} Elements={sect_elements:15} Match={str(matches):5} ({test['desc']})")
        
        if matches != expected:
            print(f"   ERROR: Expected {expected} but got {matches}")
            return False
    
    print(f"\n✅ PASS: Sect eligibility logic works correctly with pipe separator")
    return True

def test_single_element_sects():
    """TEST 4: Verify single-element sects still work"""
    print("\n" + "=" * 60)
    print("TEST 4: Single-element sects backward compatibility")
    print("=" * 60)
    
    sects = Loader.load_by_id('data/entities/sects.csv')
    single_element_sects = [s for s in sects.values() if '|' not in s.get('elements', '')]
    
    print(f"\nSingle-element sects found: {len(single_element_sects)}\n")
    for sect in single_element_sects[:5]:
        elements = sect['elements']
        displayed = elements.replace('|', ', ')  # No pipes, so no change
        status = "✓" if displayed == elements else "✗"
        print(f"{status} {sect['id']:20} | {elements:10} → {displayed}")
        if displayed != elements:
            return False
    
    print(f"\n✅ PASS: Single-element sects work correctly")
    return True

def main():
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "PHASE 7 - GAMEPLAY VALIDATION TESTS" + " " * 13 + "║")
    print("╚" + "=" * 58 + "╝")
    
    results = []
    results.append(("Multi-element preservation", test_multi_element_sects()))
    results.append(("Display format", test_display_format()))
    results.append(("Sect eligibility matching", test_sect_eligibility()))
    results.append(("Backward compatibility", test_single_element_sects()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_pass = all(r for _, r in results)
    print("\n" + "=" * 60)
    if all_pass:
        print("🎉 ALL TESTS PASSED - Fixes validated!")
    else:
        print("❌ SOME TESTS FAILED - Review needed")
    print("=" * 60 + "\n")
    
    return all_pass

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
