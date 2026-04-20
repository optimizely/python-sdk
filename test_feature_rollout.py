"""
============================================================
Feature Rollouts Bug Bash -- Python SDK
============================================================

OVERVIEW:
Feature Rollouts are a new rule type in Optimizely Feature Experimentation
that combines the simplicity of Targeted Deliveries (single variation,
traffic slider) with the measurement power of A/B tests (impressions,
conversion metrics with confidence intervals). This bug bash validates
that the Python SDK correctly evaluates Feature Rollout rules, dispatches
impression/conversion events, and handles edge cases.

OPTIMIZELY PROJECT SETUP:
1. Create or reuse a Feature Experimentation project.
2. Go to left sidebar -> Events -> "Create New Event..."
   - Create an event (e.g., Name: "feature_rollout_event", Key: "feature_rollout_event").
   - IMPORTANT: Events must be created BEFORE adding rules with metrics.
3. Go to left sidebar -> Flags -> "Create New Flag..."
   - Name: "feature_rollout_test", Key: "feature_rollout_test"
   - This creates default variations: "on" (featureEnabled: true) and
     "off" (featureEnabled: false).
4. On the flag's Ruleset page, click "Add Rule" -> "Feature Rollout".
   - Name: "rollout_rule", Key: "rollout-rule"
   - Variation: Change dropdown from "Off" to "On"
     (IMPORTANT: defaults to "Off" -- you must change it!)
   - Audience: "Everyone" (default)
   - Traffic Allocation: 100%
   - Metrics: Click "+ Add Metric" -> select your event ("feature_rollout_event")
   - Click "Save"
5. Activate the rule (two-step process):
   a. Click "Run" on the rule -> confirm the "Ready to Run" dialog -> Ok
   b. Click "Run" on the ruleset (next to "Development -- Draft")
   Both must show "Running" status.
6. Find your SDK Key and Datafile URL:
   - Go to left sidebar -> Settings (project-level, NOT flag Settings)
   - Environments tab -> Development row
   - Copy the SDK Key and Datafile URL

ENVIRONMENT: Development

SDK SETUP:
1. git clone https://github.com/optimizely/python-sdk.git
2. cd python-sdk
3. pip install -r requirements/core.txt
4. Place this test file in the repo root
5. Fill in the CONFIGURATION section below with your Development values

RUNNING TESTS:
- Run one test at a time: python test_feature_rollout.py --test=basic_rollout
- To see available tests: python test_feature_rollout.py --test=help
- Each test has a UI SETUP comment -- read it and make any required
  UI changes BEFORE running that test
- After UI changes, wait ~1 min for the datafile to update on CDN

TEST CASES:
1. basic_rollout     -- Happy path: user gets rollout variation + impression
2. everyone_else     -- 0% traffic: user gets baseline "off" variation
3. traffic_split     -- 50% traffic: verify ~50/50 distribution
4. audience_targeting-- Audience match/miss behavior
5. forced_variation  -- Allowlist overrides bucketing
6. conversion_tracking -- track() dispatches conversion event
7. disable_decision_event -- DISABLE_DECISION_EVENT suppresses impression
8. flag_off          -- Paused ruleset returns default "off"

REPORTING RESULTS:
- Share your test output (PASS/FAIL) in the dedicated bug bash Teams channel
- If you find a bug, post: test name, actual vs expected, SDK language (Python)
============================================================
"""

import argparse
import sys
import time
import uuid
import logging

from optimizely import optimizely, logger as opt_logger
from optimizely.config_manager import PollingConfigManager
from optimizely.event_dispatcher import EventDispatcher as DefaultEventDispatcher
from optimizely.decision.optimizely_decide_option import OptimizelyDecideOption
from optimizely.helpers import enums as opt_enums


# ============================================================
# CONFIGURATION -- Update these values for your environment
# ============================================================
# Environment: Development
SDK_KEY = "your_sdk_key_here"               # From project Settings -> Environments tab -> Development
FLAG_KEY = "feature_rollout_flag"            # The flag key you created
EVENT_KEY = "feature_rollout_event"                       # The event key for tracking
DATAFILE_URL = "your_datafile_url_here"      # From project Settings -> Environments tab -> Development
# Example DATAFILE_URL: https://cdn.optimizely.com/datafiles/<SDK_KEY>.json


# ============================================================
# HELPERS
# ============================================================
class CapturingEventDispatcher:
    """Event dispatcher that captures events for verification while still dispatching them."""

    def __init__(self):
        self.default_dispatcher = DefaultEventDispatcher()
        self.captured_events = []

    def dispatch_event(self, event):
        self.captured_events.append(event)
        self.default_dispatcher.dispatch_event(event)

    def has_impression(self):
        """Check if any impression (decision) event was dispatched."""
        for event in self.captured_events:
            for visitor in event.params.get('visitors', []):
                for snapshot in visitor.get('snapshots', []):
                    if snapshot.get('decisions'):
                        return True
        return False

    def has_conversion(self, event_key):
        """Check if a conversion event with the given key was dispatched."""
        for event in self.captured_events:
            for visitor in event.params.get('visitors', []):
                for snapshot in visitor.get('snapshots', []):
                    for evt in snapshot.get('events', []):
                        if evt.get('key') == event_key:
                            return True
        return False

    def clear(self):
        self.captured_events.clear()

def create_client(event_dispatcher=None):
    """Initialize a fresh Optimizely client with debug logging."""
    config_manager = PollingConfigManager(
        sdk_key=SDK_KEY,
        update_interval=30,
        url=DATAFILE_URL
    )
    kwargs = {
        'config_manager': config_manager,
        'logger': opt_logger.SimpleLogger(min_level=opt_enums.LogLevels.DEBUG),
    }
    if event_dispatcher is not None:
        kwargs['event_dispatcher'] = event_dispatcher
    client = optimizely.Optimizely(**kwargs)
    # Wait for the datafile to be fetched
    time.sleep(3)

    config = client.config_manager.get_config()
    if config is None:
        print("ERROR: Failed to fetch datafile. Check your SDK_KEY and network.")
        print(f"  SDK_KEY: {SDK_KEY}")
        sys.exit(1)
    client.logger.debug("Optimizely client initialized")
    return client


def format_decision(decision, label="Decision"):
    """Format decision details as a string."""
    lines = [f"{label}:"]
    lines.append(f"  enabled:       {decision.enabled}")
    lines.append(f"  variation_key: {decision.variation_key}")
    lines.append(f"  rule_key:      {decision.rule_key}")
    lines.append(f"  flag_key:      {decision.flag_key}")
    if decision.variables:
        lines.append(f"  variables:     {decision.variables}")
    if decision.reasons:
        lines.append(f"  reasons:")
        for reason in decision.reasons:
            lines.append(f"    - {reason}")
    return '\n'.join(lines)


def format_result(test_name, passed, detail=""):
    """Format PASS/FAIL result as a string."""
    status = "PASS" if passed else "FAIL"
    msg = f"{'=' * 50}"
    msg += f"\n{status}: {test_name}"
    if detail:
        msg += f"\nDetail: {detail}"
    msg += f"\n{'=' * 50}"
    return msg


def print_report(lines):
    """Print buffered test report after SDK logs are done."""
    print(f"\n{'=' * 50}")
    print("TEST REPORT")
    print(f"{'=' * 50}")
    for line in lines:
        print(line)
    print()


# ============================================================
# TEST 1: basic_rollout
# ============================================================
# Happy path: user qualifies for the rollout and receives the
# rollout variation. Impression event is dispatched.
#
# UI SETUP: None (use the default setup from project setup above --
#   Feature Rollout rule at 100% traffic to "on", audience=Everyone,
#   rule and ruleset both Running)
#
# Expected:
#   1. decide() returns variation_key="on", enabled=True
#   2. rule_key matches your rollout rule key
#   3. Debug logs show an impression event dispatched with
#      rule_type="feature-test"
# ============================================================
def test_basic_rollout():
    out = ["Test 1: basic_rollout", "Verifying: user gets rollout variation at 100% traffic"]

    client = create_client()
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    user = client.create_user_context(user_id)
    decision = user.decide(FLAG_KEY, [OptimizelyDecideOption.INCLUDE_REASONS])
    client.close()

    out.append(f"User: {user_id}")
    out.append(format_decision(decision))

    passed = decision.enabled is True and decision.variation_key == "on"
    detail = ""
    if not passed:
        detail = f"Expected enabled=True, variation_key='on'; got enabled={decision.enabled}, variation_key='{decision.variation_key}'"
    out.append(format_result("basic_rollout", passed, detail))
    print_report(out)


# ============================================================
# TEST 2: everyone_else
# ============================================================
# User is in the audience but falls outside traffic distribution,
# so they receive the "everyone else" (baseline) variation.
#
# UI SETUP: Change the Feature Rollout's traffic allocation to 0%.
#   - On the flag's Ruleset page, edit the rollout rule
#   - Set traffic allocation slider to 0%
#   - Save the rule
#   - Wait ~1 min for datafile to update
#
# Expected:
#   1. decide() returns variation_key="off", enabled=False
#   2. An impression event is STILL dispatched (user is in the
#      experiment, just assigned to the baseline)
# ============================================================
def test_everyone_else():
    out = ["Test 2: everyone_else", "Verifying: 0% traffic -> user gets baseline 'off' variation"]

    client = create_client()
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    user = client.create_user_context(user_id)
    decision = user.decide(FLAG_KEY, [OptimizelyDecideOption.INCLUDE_REASONS])
    client.close()

    out.append(f"User: {user_id}")
    out.append(format_decision(decision))

    passed = decision.variation_key == "off" and decision.enabled is False
    detail = ""
    if not passed:
        detail = f"Expected variation_key='off', enabled=False; got variation_key='{decision.variation_key}', enabled={decision.enabled}"
    out.append(format_result("everyone_else", passed, detail))
    print_report(out)


# ============================================================
# TEST 3: traffic_split
# ============================================================
# Verify correct traffic distribution between the rollout
# variation and the "everyone else" baseline.
#
# UI SETUP: Set the Feature Rollout traffic allocation to 50%.
#   - Edit the rollout rule, set traffic slider to 50%
#   - Save the rule
#   - Wait ~1 min for datafile to update
#
# Expected:
#   1. Over 1000 users, approximately 50% get "on" and 50% get "off"
#   2. Tolerance: +/- 5% (i.e., 45%-55% for each variation)
# ============================================================
def test_traffic_split():
    out = ["Test 3: traffic_split", "Verifying: 50% traffic split over 1000 users"]

    client = create_client()

    on_count = 0
    off_count = 0
    total = 1000

    for i in range(total):
        user_id = f"split_user_{i}_{uuid.uuid4().hex[:6]}"
        user = client.create_user_context(user_id)
        decision = user.decide(FLAG_KEY)

        if decision.variation_key == "on":
            on_count += 1
        elif decision.variation_key == "off":
            off_count += 1

    client.close()

    on_pct = (on_count / total) * 100
    off_pct = (off_count / total) * 100

    out.append(f"Results over {total} users:")
    out.append(f"  'on'  count: {on_count} ({on_pct:.1f}%)")
    out.append(f"  'off' count: {off_count} ({off_pct:.1f}%)")

    passed = 45.0 <= on_pct <= 55.0 and 45.0 <= off_pct <= 55.0
    detail = ""
    if not passed:
        detail = f"Distribution outside 45-55% tolerance: on={on_pct:.1f}%, off={off_pct:.1f}%"
    out.append(format_result("traffic_split", passed, detail))
    print_report(out)


# ============================================================
# TEST 4: audience_targeting
# ============================================================
# Users matching the audience qualify for the rollout rule.
# Users not matching skip the rule and fall through to the
# next rule or get the default.
#
# UI SETUP:
#   1. Create a custom audience (left sidebar -> Audiences):
#      - Name: "US Users"
#      - Condition: custom attribute "country" equals "US"
#   2. Edit the Feature Rollout rule:
#      - Change Audience from "Everyone" to "US Users"
#      - Set traffic allocation back to 100%
#      - Save the rule
#   3. Wait ~1 min for datafile to update
#
# Expected:
#   1. User with country="US" gets the rollout variation ("on")
#   2. User with country="UK" (or no country) does NOT get a
#      decision from this rollout rule -- they skip it and
#      fall through to the next rule or targeted delivery
# ============================================================
def test_audience_targeting():
    out = ["Test 4: audience_targeting", "Verifying: audience match/miss behavior"]

    client = create_client()

    us_user_id = f"us_user_{uuid.uuid4().hex[:8]}"
    us_user = client.create_user_context(us_user_id, {"country": "US"})
    us_decision = us_user.decide(FLAG_KEY, [OptimizelyDecideOption.INCLUDE_REASONS])

    uk_user_id = f"uk_user_{uuid.uuid4().hex[:8]}"
    uk_user = client.create_user_context(uk_user_id, {"country": "UK"})
    uk_decision = uk_user.decide(FLAG_KEY, [OptimizelyDecideOption.INCLUDE_REASONS])

    client.close()

    out.append(f"US User: {us_user_id}")
    out.append(format_decision(us_decision, label="US user decision"))
    out.append(f"UK User: {uk_user_id}")
    out.append(format_decision(uk_decision, label="UK user decision"))

    us_passed = us_decision.enabled is True and us_decision.variation_key == "on"
    uk_skipped_rollout = uk_decision.rule_key != us_decision.rule_key or uk_decision.variation_key != "on"

    passed = us_passed and uk_skipped_rollout
    detail = ""
    if not us_passed:
        detail += f"US user: expected on/enabled=True, got {us_decision.variation_key}/enabled={us_decision.enabled}. "
    if not uk_skipped_rollout:
        detail += f"UK user: expected to skip rollout rule, but got same rule_key='{uk_decision.rule_key}' with variation='on'."
    out.append(format_result("audience_targeting", passed, detail))
    print_report(out)


# ============================================================
# TEST 5: forced_variation
# ============================================================
# Allowlist (forced variations) overrides normal bucketing.
#
# UI SETUP:
#   1. Edit the Feature Rollout rule
#   2. Change Audience back to "Everyone"
#   3. Set traffic allocation to 0% (so nobody normally gets "on")
#   4. In the Allowlist section, add user ID "forced_user_123"
#      and force them into the "on" variation
#   5. Save the rule
#   6. Wait ~1 min for datafile to update
#
# Expected:
#   1. User "forced_user_123" gets variation "on" despite 0% traffic
#   2. Any other user gets "off" (0% traffic, no allowlist entry)
# ============================================================
def test_forced_variation():
    out = ["Test 5: forced_variation", "Verifying: allowlist overrides normal bucketing"]

    client = create_client()

    forced_user = client.create_user_context("forced_user_123")
    forced_decision = forced_user.decide(FLAG_KEY, [OptimizelyDecideOption.INCLUDE_REASONS])

    regular_user_id = f"regular_{uuid.uuid4().hex[:8]}"
    regular_user = client.create_user_context(regular_user_id)
    regular_decision = regular_user.decide(FLAG_KEY, [OptimizelyDecideOption.INCLUDE_REASONS])

    client.close()

    out.append("Forced user: forced_user_123")
    out.append(format_decision(forced_decision, label="Forced user decision"))
    out.append(f"Regular user: {regular_user_id}")
    out.append(format_decision(regular_decision, label="Regular user decision"))

    forced_passed = forced_decision.variation_key == "on" and forced_decision.enabled is True
    regular_passed = regular_decision.variation_key == "off" and regular_decision.enabled is False

    passed = forced_passed and regular_passed
    detail = ""
    if not forced_passed:
        detail += f"Forced user: expected 'on'/enabled=True, got '{forced_decision.variation_key}'/enabled={forced_decision.enabled}. "
    if not regular_passed:
        detail += f"Regular user: expected 'off'/enabled=False, got '{regular_decision.variation_key}'/enabled={regular_decision.enabled}."
    out.append(format_result("forced_variation", passed, detail))
    print_report(out)


# ============================================================
# TEST 6: conversion_tracking
# ============================================================
# track() dispatches a conversion event for feature rollout users.
#
# UI SETUP: Reset to the basic setup:
#   1. Remove any allowlist entries
#   2. Set Audience back to "Everyone"
#   3. Set traffic allocation to 100%
#   4. Save the rule
#   5. Wait ~1 min for datafile to update
#
# Expected:
#   1. decide() returns "on" (user qualifies)
#   2. track() call dispatches a conversion event
#   3. Debug logs show the conversion event with the event key
# ============================================================
def test_conversion_tracking():
    out = ["Test 6: conversion_tracking", "Verifying: track() dispatches conversion event"]

    dispatcher = CapturingEventDispatcher()
    client = create_client(event_dispatcher=dispatcher)
    user_id = f"track_user_{uuid.uuid4().hex[:8]}"
    user = client.create_user_context(user_id)
    decision = user.decide(FLAG_KEY)

    # Clear events from decide() so we only check track() below
    dispatcher.clear()
    user.track_event(EVENT_KEY)
    client.close()

    conversion_dispatched = dispatcher.has_conversion(EVENT_KEY)

    out.append(f"User: {user_id}")
    out.append(format_decision(decision))
    out.append(f"track('{EVENT_KEY}') called")
    out.append(f"Conversion event dispatched: {conversion_dispatched}")

    decision_ok = decision.enabled is True and decision.variation_key == "on"
    passed = decision_ok and conversion_dispatched
    detail = ""
    if not decision_ok:
        detail = f"User did not qualify for rollout (expected on/True, got {decision.variation_key}/{decision.enabled}). "
    if not conversion_dispatched:
        detail += f"Conversion event for '{EVENT_KEY}' was NOT dispatched -- expected it to be sent."
    out.append(format_result("conversion_tracking", passed, detail))
    print_report(out)


# ============================================================
# TEST 7: disable_decision_event
# ============================================================
# DISABLE_DECISION_EVENT decide option suppresses the impression
# event while still returning the correct decision.
#
# UI SETUP: None (use basic setup from test 6 -- 100% traffic,
#   audience=Everyone, rule and ruleset Running)
#
# Expected:
#   1. decide() with DISABLE_DECISION_EVENT returns the correct
#      variation ("on", enabled=True)
#   2. Debug logs should NOT show an impression event dispatched
#   3. Compare with a normal decide() call which SHOULD show
#      the impression event
# ============================================================
def test_disable_decision_event():
    out = ["Test 7: disable_decision_event", "Verifying: DISABLE_DECISION_EVENT suppresses impression"]

    # Call 1: decide() WITH DISABLE_DECISION_EVENT — should NOT dispatch impression
    dispatcher1 = CapturingEventDispatcher()
    client1 = create_client(event_dispatcher=dispatcher1)
    user_id = f"nodecision_{uuid.uuid4().hex[:8]}"
    user = client1.create_user_context(user_id)
    decision_suppressed = user.decide(
        FLAG_KEY,
        [OptimizelyDecideOption.DISABLE_DECISION_EVENT, OptimizelyDecideOption.INCLUDE_REASONS]
    )
    client1.close()
    impression_after_suppressed = dispatcher1.has_impression()

    # Call 2: decide() WITHOUT DISABLE_DECISION_EVENT — SHOULD dispatch impression
    dispatcher2 = CapturingEventDispatcher()
    client2 = create_client(event_dispatcher=dispatcher2)
    user2_id = f"withdecision_{uuid.uuid4().hex[:8]}"
    user2 = client2.create_user_context(user2_id)
    decision_normal = user2.decide(FLAG_KEY, [OptimizelyDecideOption.INCLUDE_REASONS])
    client2.close()
    impression_after_normal = dispatcher2.has_impression()

    out.append(f"Call 1 (DISABLE_DECISION_EVENT):")
    out.append(f"User: {user_id}")
    out.append(format_decision(decision_suppressed, label="Suppressed decision"))
    out.append(f"Impression dispatched: {impression_after_suppressed} (expected: False)")
    out.append(f"")
    out.append(f"Call 2 (normal):")
    out.append(f"User: {user2_id}")
    out.append(format_decision(decision_normal, label="Normal decision"))
    out.append(f"Impression dispatched: {impression_after_normal} (expected: True)")

    decisions_ok = (
        decision_suppressed.enabled is True
        and decision_suppressed.variation_key == "on"
        and decision_normal.enabled is True
        and decision_normal.variation_key == "on"
    )
    suppression_ok = not impression_after_suppressed
    normal_ok = impression_after_normal

    passed = decisions_ok and suppression_ok and normal_ok
    detail = ""
    if not decisions_ok:
        detail += "One or both decisions returned unexpected values. "
    if not suppression_ok:
        detail += "DISABLE_DECISION_EVENT did NOT suppress the impression -- event was still dispatched. "
    if not normal_ok:
        detail += "Normal decide() did NOT dispatch an impression -- expected one. "
    out.append(format_result("disable_decision_event", passed, detail))
    print_report(out)


# ============================================================
# TEST 8: rule_fallthrough
# ============================================================
# When a user does not match the Feature Rollout rule's audience,
# they should skip it and fall through to the next rule.
#
# NOTE: 0% traffic does NOT cause fallthrough -- it puts the user
# into the "everyone else" baseline of the SAME rule. Only an
# audience mismatch causes the SDK to skip the rule entirely.
#
# UI SETUP:
#   1. If you haven't already, create a "US Users" audience
#      (left sidebar -> Audiences -> custom attribute "country"
#      equals "US"). You may have created this for test 4.
#   2. Edit the Feature Rollout rule:
#      - Set Audience to "US Users"
#      - Set Traffic to 100%, Variation to "On"
#      - Save the rule
#   3. Add a Targeted Delivery rule BELOW the Feature Rollout:
#      - Click "Add Rule" -> "Targeted Delivery"
#      - Name: "fallback_delivery"
#      - Variation: Change from "Off" to "On"
#        (IMPORTANT: defaults to "Off" -- you must change it!)
#      - Audience: "Everyone"
#      - Save the rule
#   4. Make sure both rules and the ruleset are Running
#      (Run each rule, then Run the ruleset)
#   5. Wait ~1 min for datafile to update
#
# Expected:
#   1. User with country="UK" does NOT match the Feature Rollout
#      audience ("US Users") -- SDK skips the rule entirely
#   2. User falls through to the Targeted Delivery rule
#   3. decide() returns enabled=True, variation_key="on"
#   4. rule_key is NOT the Feature Rollout rule key -- it should
#      be the Targeted Delivery's rule key
# ============================================================
ROLLOUT_RULE_KEY = "feature_rollout_rule"  # Your Feature Rollout rule key

def test_rule_fallthrough():
    out = ["Test 8: rule_fallthrough",
           "Verifying: audience mismatch causes fallthrough to next rule"]

    client = create_client()

    # UK user should NOT match the "US Users" audience on the Feature Rollout,
    # causing them to skip it and fall through to the Targeted Delivery
    user_id = f"fallthrough_{uuid.uuid4().hex[:8]}"
    user = client.create_user_context(user_id, {"country": "UK"})
    decision = user.decide(FLAG_KEY, [OptimizelyDecideOption.INCLUDE_REASONS])
    client.close()

    out.append(f"User: {user_id} (country=UK)")
    out.append(format_decision(decision))

    got_on = decision.enabled is True and decision.variation_key == "on"
    skipped_rollout = decision.rule_key != ROLLOUT_RULE_KEY

    passed = got_on and skipped_rollout
    detail = ""
    if not got_on:
        detail += f"Expected enabled=True, variation_key='on'; got enabled={decision.enabled}, variation_key='{decision.variation_key}'. Is the Targeted Delivery variation set to 'On'? "
    if not skipped_rollout:
        detail += f"User was bucketed into the Feature Rollout rule (rule_key='{decision.rule_key}') instead of falling through. Is the rollout audience set to 'US Users'?"
    out.append(format_result("rule_fallthrough", passed, detail))
    print_report(out)


# ============================================================
# CLI RUNNER
# ============================================================

TESTS = {
    # "basic_rollout": test_basic_rollout,
    # "everyone_else": test_everyone_else,
    # "traffic_split": test_traffic_split,
    # "audience_targeting": test_audience_targeting,
    # "forced_variation": test_forced_variation,
    "conversion_tracking": test_conversion_tracking,
    # "disable_decision_event": test_disable_decision_event,
    # "rule_fallthrough": test_rule_fallthrough,
}


def main():
    parser = argparse.ArgumentParser(
        description="Feature Rollouts Bug Bash - Python SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--test",
        default=None,
        help="Name of the test to run (e.g., basic_rollout). Use --test=help to list all.",
    )
    args = parser.parse_args()

    test_name = args.test.strip() if args.test else next(iter(TESTS))

    if test_name == "help" or test_name not in TESTS:
        print("\nAvailable tests:")
        print("-" * 50)
        for name in TESTS:
            # Extract the first line of the docstring-like comment
            print(f"  --test={name}")
        print("-" * 50)
        if test_name != "help":
            print(f"\nUnknown test: '{test_name}'")
        print("\nRun one test at a time. Read the UI SETUP comment in each")
        print("test before running -- some tests require UI changes first.")
        sys.exit(0)

    # Validate configuration
    if SDK_KEY == "your_sdk_key_here" or DATAFILE_URL == "your_datafile_url_here":
        print("ERROR: Please update the CONFIGURATION section at the top of this file.")
        print("  SDK_KEY and DATAFILE_URL must be set to your Development environment values.")
        print("  Find them in: project Settings -> Environments tab -> Development")
        sys.exit(1)

    print(f"\n{'=' * 50}")
    print(f"Feature Rollouts Bug Bash - Python SDK")
    print(f"Running test: {test_name}")
    print(f"{'=' * 50}")

    TESTS[test_name]()


if __name__ == "__main__":
    main()
