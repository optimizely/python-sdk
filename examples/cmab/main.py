"""
CMAB Testing Example for Optimizely Python SDK
This file contains comprehensive test scenarios for CMAB functionality

To run: python examples/cmab/main.py
To run specific test: python examples/cmab/main.py --test=cache_hit
"""

import argparse
import json
import time
import threading
from typing import Any

from optimizely import optimizely
from optimizely.config_manager import PollingConfigManager
from optimizely.decision.optimizely_decide_option import OptimizelyDecideOption
from optimizely import logger as opt_logger
from optimizely.helpers import enums

# SDK Key and Flag Key - UPDATE THESE WITH YOUR PROJECT CONFIGURATION
SDK_KEY = "DCx4eoV52jhgaC9MSab3g"  # rc (prep)
FLAG_KEY = "flag-cmab-1"

# Test user IDs
USER_QUALIFIED = "test_user_99"  # Will be bucketed into CMAB
USER_NOT_BUCKETED = "test_user_1"  # Won't be bucketed (traffic allocation)
USER_CACHE_TEST = "cache_user_123"


def main():
    parser = argparse.ArgumentParser(description='CMAB Testing Suite')
    parser.add_argument('--test', default='all', help='Specific test case to run')
    args = parser.parse_args()

    # Enable debug logging to see CMAB activity
    logging = opt_logger.SimpleLogger(min_level=enums.LogLevels.DEBUG)

    print("=== CMAB Testing Suite for Python SDK ===")
    print(f"Testing CMAB with rc environment")
    print(f"SDK Key: {SDK_KEY}")
    print(f"Flag Key: {FLAG_KEY}\n")

    # Create config manager with rc URL template
    config_manager = PollingConfigManager(
        sdk_key=SDK_KEY,
        url_template="https://optimizely-staging.s3.amazonaws.com/datafiles/{sdk_key}.json",  # rc
        logger=logging
    )

    # Initialize Optimizely client
    optimizely_client = optimizely.Optimizely(
        sdk_key=SDK_KEY,
        config_manager=config_manager,
        logger=logging
    )

    # Wait for datafile to load
    print("Waiting for datafile to load...")
    time.sleep(2)

    # Run tests based on argument
    test_cases = {
        'basic': test_basic_cmab,
        'cache_hit': test_cache_hit,
        'cache_miss': test_cache_miss_on_attribute_change,
        'ignore_cache': test_ignore_cache_option,
        'reset_cache': test_reset_cache_option,
        'invalidate_user': test_invalidate_user_cache_option,
        'concurrent': test_concurrent_requests,
        'error': test_error_handling,
        'fallback': test_fallback_when_not_qualified,
        'traffic': test_traffic_allocation,
        'forced': test_forced_variation_override,
        'event_tracking': test_event_tracking,
        'attribute_types': test_attribute_types,
        'performance': test_performance_benchmarks,
        'cache_expiry': test_cache_expiry,
    }

    if args.test in test_cases:
        test_cases[args.test](optimizely_client)
    elif args.test == 'all':
        for test_name, test_func in test_cases.items():
            test_func(optimizely_client)
            print("\n" + "=" * 80 + "\n")
    else:
        print(f"Unknown test case: {args.test}\n")
        print("Available test cases:")
        print("  basic, cache_hit, cache_miss, ignore_cache, reset_cache,")
        print("  invalidate_user, concurrent, error, fallback, traffic,")
        print("  forced, event_tracking, attribute_types, performance, cache_expiry, all")

    optimizely_client.close()


# Test 1: Basic CMAB functionality
def test_basic_cmab(optimizely_client):
    print("\n--- Test 1: Basic CMAB Functionality ---")
    print("Expected: User qualifies for CMAB, gets CMAB variation\n")

    # Test with user who qualifies for CMAB
    user_context = optimizely_client.create_user_context(
        USER_QUALIFIED,
        {"country": "us"}
    )

    decision = user_context.decide(FLAG_KEY)
    print_decision("CMAB Qualified User", decision)

    print("\n✓ Basic CMAB Test Complete")


# Test 2: Cache hit - same user and attributes
def test_cache_hit(optimizely_client):
    print("\n--- Test 2: Cache Hit (Same User & Attributes) ---")
    print("Expected:")
    print("  1. Decision 1 with country=us → CMAB API call → Cache stored")
    print("  2. Decision 2 with country=fr → Cache miss (different attribute) → CMAB API call")
    print("  3. Decision 3 with country=fr → Cache hit (same as Decision 2)\n")

    user_context = optimizely_client.create_user_context(
        USER_CACHE_TEST,
        {"country": "us"}
    )

    # First decision - should call CMAB service
    print("First decision (CMAB call):")
    decision1 = user_context.decide(FLAG_KEY)
    print_decision("Decision 1", decision1)

    user_context2 = optimizely_client.create_user_context(
        USER_CACHE_TEST,
        {"country": "fr"}
    )

    # Second decision - miss cache
    print("\nSecond decision (Cache miss - different country):")
    decision2 = user_context2.decide(FLAG_KEY)
    print_decision("Decision 2", decision2)

    # Third decision - should use cache
    print("\nThird decision (Cache hit - same country as Decision 2):")
    decision3 = user_context2.decide(FLAG_KEY)
    print_decision("Decision 3", decision3)

    print("\n✓ Cache Hit Test Complete")


# Test 3: Cache miss when relevant attributes change
def test_cache_miss_on_attribute_change(optimizely_client):
    print("\n--- Test 3: Cache Miss on Attribute Change ---")
    print("Expected:")
    print("  1. Decision 1: 'hello' → CMAB API call → Cache stored")
    print("  2. Decision 2: 'world' → Cache miss (different value) → CMAB API call")
    print("  3. Decision 3: 'world' → Cache hit (same as Decision 2)\n")

    # First decision with valid attribute
    user_context1 = optimizely_client.create_user_context(
        USER_CACHE_TEST + "_attr",
        {"cmab_test_attribute": "hello"}
    )

    print("Decision with 'hello':")
    decision1 = user_context1.decide(FLAG_KEY)
    print_decision("Decision 1", decision1)

    # Second decision with changed valid attribute
    user_context2 = optimizely_client.create_user_context(
        USER_CACHE_TEST + "_attr",
        {"cmab_test_attribute": "world"}  # Changed value
    )

    print("\nDecision with 'world' (cache miss expected):")
    decision2 = user_context2.decide(FLAG_KEY)
    print_decision("Decision 2", decision2)

    # Third decision with same user and attributes
    user_context3 = optimizely_client.create_user_context(
        USER_CACHE_TEST + "_attr",
        {"cmab_test_attribute": "world"}  # Same as decision2
    )

    print("\nDecision with same user and attributes (cache hit expected):")
    decision3 = user_context3.decide(FLAG_KEY)
    print_decision("Decision 3", decision3)

    print("\n✓ Cache Miss Test Complete")


# Test 4: IGNORE_CMAB_CACHE option
def test_ignore_cache_option(optimizely_client):
    print("\n--- Test 4: IGNORE_CMAB_CACHE Option ---")
    print("Expected:")
    print("  1. Decision 1 → CMAB API call → Cache stored")
    print("  2. Decision 2 with IGNORE_CMAB_CACHE → Cache bypassed → New CMAB API call")
    print("  3. Decision 3 → Cache hit (uses original cache from Decision 1)\n")

    user_context = optimizely_client.create_user_context(
        USER_CACHE_TEST + "_ignore",
        {"country": "fr"}
    )

    # First decision - populate cache
    print("First decision (populate cache):")
    decision1 = user_context.decide(FLAG_KEY)
    print_decision("Decision 1", decision1)

    # Second decision with IGNORE_CMAB_CACHE
    print("\nSecond decision with IGNORE_CMAB_CACHE:")
    decision2 = user_context.decide(
        FLAG_KEY,
        [OptimizelyDecideOption.IGNORE_CMAB_CACHE]
    )
    print_decision("Decision 2 (ignored cache)", decision2)

    # Third decision - should use original cache
    print("\nThird decision (should use original cache):")
    decision3 = user_context.decide(FLAG_KEY)
    print_decision("Decision 3", decision3)

    print("\n✓ Ignore Cache Test Complete")


# Test 5: RESET_CMAB_CACHE option
def test_reset_cache_option(optimizely_client):
    print("\n--- Test 5: RESET_CMAB_CACHE Option ---")
    print("Expected:")
    print("  1. User 1 → CMAB API call → Cache stored for User 1")
    print("  2. User 2 → CMAB API call → Cache stored for User 2")
    print("  3. User 1 + RESET_CMAB_CACHE → Entire cache cleared → New CMAB API call")
    print("  4. User 2 → Cache was cleared → New CMAB API call\n")

    # Setup two different users
    user_context1 = optimizely_client.create_user_context(
        "reset_user_1",
        {"cmab_test_attribute": "hello"}
    )

    user_context2 = optimizely_client.create_user_context(
        "reset_user_2",
        {"cmab_test_attribute": "hello"}
    )

    # Populate cache for both users
    print("Populating cache for User 1:")
    decision1 = user_context1.decide(FLAG_KEY)
    print_decision("User 1 Decision", decision1)

    print("\nPopulating cache for User 2:")
    decision2 = user_context2.decide(FLAG_KEY)
    print_decision("User 2 Decision", decision2)

    # Reset entire cache
    print("\nResetting entire CMAB cache:")
    decision3 = user_context1.decide(
        FLAG_KEY,
        [OptimizelyDecideOption.RESET_CMAB_CACHE]
    )
    print_decision("User 1 after RESET", decision3)

    # Check if User 2's cache was also cleared
    print("\nUser 2 after cache reset (should refetch):")
    decision4 = user_context2.decide(FLAG_KEY)
    print_decision("User 2 after reset", decision4)

    print("\n✓ Reset Cache Test Complete")


# Test 6: INVALIDATE_USER_CMAB_CACHE option
def test_invalidate_user_cache_option(optimizely_client):
    print("\n--- Test 6: INVALIDATE_USER_CMAB_CACHE Option ---")
    print("Expected:")
    print("  1. User 1 → CMAB API call → Cache stored for User 1")
    print("  2. User 2 → CMAB API call → Cache stored for User 2")
    print("  3. User 1 + INVALIDATE_USER_CMAB_CACHE → Only User 1's cache cleared → New CMAB API call")
    print("  4. User 2 → User 2's cache preserved → Cache hit\n")

    # Setup two different users
    user_context1 = optimizely_client.create_user_context(
        "invalidate_user_1",
        {"cmab_test_attribute": "hello"}
    )

    user_context2 = optimizely_client.create_user_context(
        "invalidate_user_2",
        {"cmab_test_attribute": "hello"}
    )

    # Populate cache for both users
    print("Populating cache for User 1:")
    decision1 = user_context1.decide(FLAG_KEY)
    print_decision("User 1 Initial", decision1)

    print("\nPopulating cache for User 2:")
    decision2 = user_context2.decide(FLAG_KEY)
    print_decision("User 2 Initial", decision2)

    # Invalidate only User 1's cache
    print("\nInvalidating User 1's cache only:")
    decision3 = user_context1.decide(
        FLAG_KEY,
        [OptimizelyDecideOption.INVALIDATE_USER_CMAB_CACHE]
    )
    print_decision("User 1 after INVALIDATE", decision3)

    # Check if User 2's cache is still valid
    print("\nUser 2 after User 1 invalidation (should use cache):")
    decision4 = user_context2.decide(FLAG_KEY)
    print_decision("User 2 still cached", decision4)

    print("\n✓ Invalidate User Cache Test Complete")


# Test 7: Concurrent requests for same user - thread safety
def test_concurrent_requests(optimizely_client):
    print("\n--- Test 7: Concurrent Requests ---")
    print("Testing thread safety with concurrent decide() calls")
    print("Expected: 1 CMAB API call + 4 cache hits, all threads return same variation\n")

    user_context = optimizely_client.create_user_context(
        "concurrent_user",
        {"cmab_test_attribute": "hello"}
    )

    # List to collect results
    results = []
    lock = threading.Lock()

    def make_decision(thread_id):
        decision = user_context.decide(FLAG_KEY)
        print(f"  Thread {thread_id} completed")
        with lock:
            results.append(decision)

    # Launch 5 concurrent threads
    print("Launching 5 concurrent decide calls...")
    threads = []
    for i in range(5):
        thread = threading.Thread(target=make_decision, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Count variations
    variations = {}
    for decision in results:
        var_key = decision.variation_key
        variations[var_key] = variations.get(var_key, 0) + 1

    # All should return the same variation (only one CMAB call)
    print("\nResults:")
    for variation, count in variations.items():
        print(f"  Variation '{variation}': {count} times")

    if len(variations) == 1:
        print("✓ Concurrent handling correct: All returned same variation")
    else:
        print("⚠ Issue with concurrent handling: Different variations returned")
        print("  This may indicate a race condition or timing issue")


# Test 8: Error handling simulation
def test_error_handling(optimizely_client):
    print("\n--- Test 8: Error Handling ---")
    print("Testing with invalid attribute types (integer instead of string)")
    print("Expected: Falls back to rollout variation, no CMAB API call\n")

    # Test with invalid/malformed attributes that might cause issues
    user_context = optimizely_client.create_user_context(
        "error_test_user",
        {"cmab_test_attribute": 12345}  # Invalid type (should be string)
    )

    print("Testing with invalid attribute types:")
    decision = user_context.decide(FLAG_KEY)
    print_decision("Error scenario", decision)

    if decision.reasons:
        print("Reasons for decision:")
        for reason in decision.reasons:
            print(f"  - {reason}")

    print("\n✓ Error Handling Test Complete")


# Test 9: Fallback when user doesn't qualify for CMAB
def test_fallback_when_not_qualified(optimizely_client):
    print("\n--- Test 9: Fallback When Not Qualified for CMAB ---")
    print("Expected: User without required attributes falls back to rollout, no CMAB API call\n")

    # User with attributes that don't match CMAB audience
    user_context = optimizely_client.create_user_context(
        "fallback_user",
        {}
    )

    decision = user_context.decide(FLAG_KEY)
    print_decision("Non-CMAB User", decision)

    if decision.rule_key != "exp_1":
        print("✓ Fallback working: Decision from non-CMAB rule")
    else:
        print("⚠ Fallback issue: Still received CMAB decision")

    print("Expected: No CMAB API call in debug logs above")


# Test 10: Traffic allocation check
def test_traffic_allocation(optimizely_client):
    print("\n--- Test 10: Traffic Allocation Check ---")
    print("Note: Set CMAB experiment traffic allocation to 50% in Optimizely UI for this test")
    print("Expected: With 50% traffic, one user gets CMAB, other falls to rollout\n")

    # User not in traffic allocation (test_user_1)
    user_context1 = optimizely_client.create_user_context(
        USER_NOT_BUCKETED,
        {"cmab_test_attribute": "hello"}
    )

    decision1 = user_context1.decide(FLAG_KEY)
    print_decision("User Not in Traffic", decision1)

    # User in traffic allocation (test_user_99)
    user_context2 = optimizely_client.create_user_context(
        USER_QUALIFIED,
        {"cmab_test_attribute": "hello"}
    )

    decision2 = user_context2.decide(FLAG_KEY)
    print_decision("User in Traffic", decision2)

    print("\nExpected: Only second user triggers CMAB API call (if traffic at 50%)")


# Test 11: Forced variation override
def test_forced_variation_override(optimizely_client):
    print("\n--- Test 11: Forced Variation Override ---")
    print("Note: Forced variations must be configured in Optimizely UI or datafile")
    print("Expected: If forced variation exists, no CMAB API call\n")

    # Note: This test shows the concept but forced variations
    # would need to be configured in the datafile or via whitelisting
    user_context = optimizely_client.create_user_context(
        "forced_user",
        {"cmab_test_attribute": "hello"}
    )

    decision = user_context.decide(FLAG_KEY)
    print_decision("Potential Forced User", decision)

    print("Note: Forced variations would be configured in datafile")
    print("Expected: If forced variation exists, no CMAB API call")


# Test 12: Event tracking with CMAB UUID
def test_event_tracking(optimizely_client):
    print("\n--- Test 12: Event Tracking with CMAB UUID ---")
    print("Expected: Impression events include CMAB UUID, conversion events do NOT\n")

    user_context = optimizely_client.create_user_context(
        "event_user",
        {"cmab_test_attribute": "hello"}
    )

    # Make CMAB decision
    decision = user_context.decide(FLAG_KEY)
    print_decision("Decision for Events", decision)

    # Track a conversion event
    user_context.track_event("event1", {})

    print("\nConversion event tracked: 'event1'")
    print("Expected: Impression events contain CMAB UUID, conversion events do NOT")
    print("Check event processor logs for CMAB UUID only in impression events")


# Test 13: Attribute types and formatting
def test_attribute_types(optimizely_client):
    print("\n--- Test 13: Attribute Types and Formatting ---")
    print("Expected: Only valid CMAB attributes sent to API, invalid ones filtered\n")

    user_context = optimizely_client.create_user_context(
        "attr_user",
        {}  # Missing cmab_test_attribute - should cause fallback
    )

    decision = user_context.decide(FLAG_KEY)
    print_decision("Mixed Attribute Types", decision)

    print("\nExpected in API request:")
    print("- Valid attribute: cmab_test_attribute sent to CMAB API")
    print("- Invalid attributes: filtered out, not sent to CMAB API")
    print("- Only cmab_test_attribute should appear in CMAB request body")


# Test 14: Performance benchmarks
def test_performance_benchmarks(optimizely_client):
    print("\n--- Test 14: Performance Benchmarks ---")
    print("Measuring API call vs cache performance")
    print("Targets: Cached calls <10ms, API calls <500ms\n")

    user_context = optimizely_client.create_user_context(
        "perf_user",
        {"cmab_test_attribute": "hello"}
    )

    # Measure first call (API call)
    start = time.time()
    decision1 = user_context.decide(FLAG_KEY)
    api_duration = (time.time() - start) * 1000  # Convert to milliseconds

    print_decision("First Call (API)", decision1)
    print(f"API call duration: {api_duration:.2f}ms")

    # Measure cached calls
    cached_durations = []
    for i in range(10):
        start = time.time()
        user_context.decide(FLAG_KEY)
        cached_durations.append((time.time() - start) * 1000)

    # Calculate average cached duration
    avg_cached = sum(cached_durations) / len(cached_durations)

    print(f"Average cached call duration: {avg_cached:.4f}ms (10 calls)")
    print(f"\nPerformance Targets:")
    print(f"- Cached calls: <10ms (actual: {avg_cached:.4f}ms)")
    print(f"- API calls: <500ms (actual: {api_duration:.2f}ms)")

    if avg_cached < 10:
        print("✓ Cached performance: PASS")
    else:
        print("✗ Cached performance: FAIL")

    if api_duration < 500:
        print("✓ API performance: PASS")
    else:
        print("✗ API performance: FAIL")


# Test 15: Cache expiry
def test_cache_expiry(optimizely_client):
    print("\n--- Test 15: Cache Expiry (Simulated) ---")
    print("Note: Real cache expiry test requires 30+ minute wait (default TTL)")
    print("Expected: Cache entries expire after TTL and trigger new API calls\n")

    user_context = optimizely_client.create_user_context(
        "expiry_user",
        {"cmab_test_attribute": "hello"}
    )

    # First decision
    print("Decision at T=0:")
    decision1 = user_context.decide(FLAG_KEY)
    print_decision("Initial Decision", decision1)

    # Simulate time passing (in real scenario this would be 30+ minutes)
    print("\nSimulating cache expiry...")
    time.sleep(2)

    # For actual testing, you would need to wait 30+ minutes or manipulate cache TTL
    print("Decision after simulated expiry:")
    decision2 = user_context.decide(FLAG_KEY)
    print_decision("After Expiry", decision2)

    print("\nNote: Real cache expiry test requires 30+ minute wait")
    print("Expected: New CMAB API call after expiry")


# Helper function to print decision details
def print_decision(label: str, decision):
    print(f"\n{label}:")
    print(f"  Enabled: {decision.enabled}")
    print(f"  Variation: {decision.variation_key}")
    print(f"  Rule: {decision.rule_key}")

    if decision.variables:
        print(f"  Variables: {decision.variables.to_dict()}")

    if decision.reasons:
        print(f"  Reasons:")
        for reason in decision.reasons:
            print(f"    - {reason}")

    # CMAB UUID and API calls visible in debug logs
    print(f"  [Check debug logs above for CMAB UUID and API calls]")


# Additional helper to pretty print JSON (for debugging)
def pretty_print(label: str, data: Any):
    try:
        formatted = json.dumps(data, indent=2)
        print(f"{label}:\n{formatted}")
    except Exception as e:
        print(f"{label}: Error formatting - {e}")


if __name__ == "__main__":
    main()
