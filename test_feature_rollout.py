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
   - Name: "fr_rule", Key: "fr_rule"
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
3. traffic_split     -- 50% traffic: verify ~50/50 distribution + deterministic bucketing
4. audience_targeting-- Audience match/miss behavior
5. forced_variation  -- Allowlist overrides bucketing
6. conversion_tracking -- track() dispatches conversion event
7. disable_decision_event -- DISABLE_DECISION_EVENT suppresses impression
8. rule_fallthrough  -- Audience mismatch -> fallthrough, no impression
9. fr_skip_to_ab_rule -- FR audience miss -> lands in A/B test below

REPORTING RESULTS:
- Share your test output (PASS/FAIL) in the dedicated bug bash Teams channel
- If you find a bug, post: test name, actual vs expected, SDK language (Python)
============================================================
"""

import argparse
import math
import sys
import time
import uuid

from optimizely import optimizely, logger as opt_logger
from optimizely.config_manager import PollingConfigManager
from optimizely.event_dispatcher import EventDispatcher as DefaultEventDispatcher
from optimizely.decision.optimizely_decide_option import OptimizelyDecideOption
from optimizely.helpers import enums as opt_enums
from optimizely.lib import pymmh3 as mmh3


# ============================================================
# CONFIGURATION -- Update these values for your environment
# ============================================================
# Environment: Development
SDK_KEY = "your_sdk_key_here"               # From project Settings -> Environments tab -> Development
FLAG_KEY = "feature_rollout_flag"            # The flag key you created
EVENT_KEY = "feature_rollout_event"                       # The event key for tracking
DATAFILE_URL = "your_datafile_url_here"      # From project Settings -> Environments tab -> Development
# Example DATAFILE_URL: https://cdn.optimizely.com/datafiles/<SDK_KEY>.json
ROLLOUT_RULE_KEY = "fr_rule"    # Your Feature Rollout rule key
AB_RULE_KEY = "ab_test_rule"                 # Your A/B test rule key (for test_fr_skip_to_ab_rule)


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

    def get_impression_metadata(self):
        """Extract metadata dicts from all captured impression (decision) events.

        Returns a list of metadata dicts, each with keys:
        flag_key, rule_key, rule_type, variation_key, enabled.
        """
        results = []
        for event in self.captured_events:
            for visitor in event.params.get('visitors', []):
                for snapshot in visitor.get('snapshots', []):
                    for decision in snapshot.get('decisions', []):
                        metadata = decision.get('metadata')
                        if metadata:
                            results.append(metadata)
        return results

    def clear(self):
        self.captured_events.clear()


def _generate_bucket_value(bucketing_id):
    """Replicate SDK bucketing: MurmurHash3 -> bucket value in [0, 10000).

    This mirrors optimizely.bucketer.Bucketer._generate_bucket_value().
    """
    hash_val = mmh3.hash(bucketing_id, 1) & 0xFFFFFFFF
    ratio = float(hash_val) / math.pow(2, 32)
    return math.floor(ratio * 10000)


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

    dispatcher = CapturingEventDispatcher()
    client = create_client(event_dispatcher=dispatcher)
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    user = client.create_user_context(user_id)
    decision = user.decide(FLAG_KEY, [OptimizelyDecideOption.INCLUDE_REASONS])
    client.close()

    out.append(f"User: {user_id}")
    out.append(format_decision(decision))

    # Check impression event metadata
    metadata_list = dispatcher.get_impression_metadata()
    print(metadata_list)
    impression_ok = len(metadata_list) == 1
    metadata_detail = ""
    if impression_ok:
        md = metadata_list[0]
        out.append(f"Impression metadata: rule_key='{md.get('rule_key')}', variation_key='{md.get('variation_key')}'")
        if md.get('variation_key') != "on":
            impression_ok = False
            metadata_detail += f"Impression variation_key: expected 'on', got '{md.get('variation_key')}'. "
        if md.get('rule_key') != ROLLOUT_RULE_KEY:
            impression_ok = False
            metadata_detail += f"Impression rule_key: expected '{ROLLOUT_RULE_KEY}', got '{md.get('rule_key')}'. "
    else:
        metadata_detail += f"Expected 1 impression event, got {len(metadata_list)}. "

    passed = decision.enabled is True and decision.variation_key == "on" and impression_ok
    detail = ""
    if not (decision.enabled is True and decision.variation_key == "on"):
        detail = f"Expected enabled=True, variation_key='on'; got enabled={decision.enabled}, variation_key='{decision.variation_key}'. "
    detail += metadata_detail
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

    dispatcher = CapturingEventDispatcher()
    client = create_client(event_dispatcher=dispatcher)
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    user = client.create_user_context(user_id)
    decision = user.decide(FLAG_KEY, [OptimizelyDecideOption.INCLUDE_REASONS])
    client.close()

    out.append(f"User: {user_id}")
    out.append(format_decision(decision))

    # Check impression event metadata -- impression should still be dispatched
    metadata_list = dispatcher.get_impression_metadata()
    impression_ok = len(metadata_list) == 1
    metadata_detail = ""
    if impression_ok:
        md = metadata_list[0]
        out.append(f"Impression metadata: rule_key='{md.get('rule_key')}', variation_key='{md.get('variation_key')}'")
        if md.get('variation_key') != "off":
            impression_ok = False
            metadata_detail += f"Impression variation_key: expected 'off', got '{md.get('variation_key')}'. "
        if md.get('rule_key') != ROLLOUT_RULE_KEY:
            impression_ok = False
            metadata_detail += f"Impression rule_key: expected '{ROLLOUT_RULE_KEY}', got '{md.get('rule_key')}'. "
    else:
        metadata_detail += f"Expected 1 impression event (baseline), got {len(metadata_list)}. "

    passed = decision.variation_key == "off" and decision.enabled is False and impression_ok
    detail = ""
    if not (decision.variation_key == "off" and decision.enabled is False):
        detail = f"Expected variation_key='off', enabled=False; got variation_key='{decision.variation_key}', enabled={decision.enabled}. "
    detail += metadata_detail
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
    out = ["Test 3: traffic_split", "Verifying: 50% traffic split over 1000 users + deterministic bucketing"]

    dispatcher = CapturingEventDispatcher()
    client = create_client(event_dispatcher=dispatcher)

    # --- Part 1: Statistical distribution check ---
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

    on_pct = (on_count / total) * 100
    off_pct = (off_count / total) * 100

    out.append(f"Part 1 - Statistical distribution over {total} users:")
    out.append(f"  'on'  count: {on_count} ({on_pct:.1f}%)")
    out.append(f"  'off' count: {off_count} ({off_pct:.1f}%)")

    distribution_ok = 45.0 <= on_pct <= 55.0 and 45.0 <= off_pct <= 55.0

    # --- Part 2: Deterministic bucketing with specific user IDs ---
    # Get the experiment ID from the project config so we can compute bucket values
    config = client.config_manager.get_config()
    experiment = config.experiment_key_map.get(ROLLOUT_RULE_KEY)
    bucketing_detail = ""

    if experiment is None:
        bucketing_detail += f"Could not find experiment with key '{ROLLOUT_RULE_KEY}' in config. Skipping bucketing check. "
        bucketing_ok = False
    else:
        experiment_id = experiment.id
        out.append(f"\nPart 2 - Deterministic bucketing (experiment_id={experiment_id}):")

        # Test with specific user IDs -- compute expected variation via bucketing
        test_user_ids = [
            "bucketing_user_alpha",
            "bucketing_user_beta",
            "bucketing_user_gamma",
            "bucketing_user_delta",
            "bucketing_user_epsilon",
            "bucketing_user_zeta",
            "bucketing_user_eta",
            "bucketing_user_theta",
            "bucketing_user_iota",
            "bucketing_user_kappa",
        ]

        bucketing_ok = True
        dispatcher.clear()

        for uid in test_user_ids:
            # Compute expected bucket value using the same algorithm as the SDK
            bucketing_key = f"{uid}{experiment_id}"
            bucket_value = _generate_bucket_value(bucketing_key)

            # For 50% traffic: bucket < 5000 -> "on", bucket >= 5000 -> "off"
            expected_variation = "on" if bucket_value < 5000 else "off"

            user = client.create_user_context(uid)
            decision = user.decide(FLAG_KEY)

            match = decision.variation_key == expected_variation
            status = "OK" if match else "MISMATCH"
            out.append(f"  {uid}: bucket={bucket_value}, expected='{expected_variation}', "
                       f"got='{decision.variation_key}' [{status}]")

            if not match:
                bucketing_ok = False
                bucketing_detail += f"User '{uid}' (bucket={bucket_value}): expected '{expected_variation}', got '{decision.variation_key}'. "

    client.close()

    passed = distribution_ok and bucketing_ok
    detail = ""
    if not distribution_ok:
        detail += f"Distribution outside 45-55% tolerance: on={on_pct:.1f}%, off={off_pct:.1f}%. "
    detail += bucketing_detail
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

    dispatcher = CapturingEventDispatcher()
    client = create_client(event_dispatcher=dispatcher)

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

    # Check impression metadata for US user
    metadata_list = dispatcher.get_impression_metadata()
    impression_ok = True
    metadata_detail = ""
    # Find the impression for the US user (should have rule_key matching rollout)
    us_impressions = [md for md in metadata_list if md.get('rule_key') == ROLLOUT_RULE_KEY]
    if len(us_impressions) == 0:
        impression_ok = False
        metadata_detail += f"No impression event found with rule_key='{ROLLOUT_RULE_KEY}' for US user. "
    elif us_impressions[0].get('variation_key') != "on":
        impression_ok = False
        metadata_detail += f"US user impression variation_key: expected 'on', got '{us_impressions[0].get('variation_key')}'. "
    else:
        out.append(f"US user impression: rule_key='{us_impressions[0].get('rule_key')}', variation_key='{us_impressions[0].get('variation_key')}'")

    passed = us_passed and uk_skipped_rollout and impression_ok
    detail = ""
    if not us_passed:
        detail += f"US user: expected on/enabled=True, got {us_decision.variation_key}/enabled={us_decision.enabled}. "
    if not uk_skipped_rollout:
        detail += f"UK user: expected to skip rollout rule, but got same rule_key='{uk_decision.rule_key}' with variation='on'. "
    detail += metadata_detail
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

    dispatcher = CapturingEventDispatcher()
    client = create_client(event_dispatcher=dispatcher)

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

    # Check impression metadata for forced user
    metadata_list = dispatcher.get_impression_metadata()
    impression_ok = True
    metadata_detail = ""
    forced_impressions = [md for md in metadata_list
                          if md.get('variation_key') == "on" and md.get('rule_key') == ROLLOUT_RULE_KEY]
    if len(forced_impressions) == 0:
        impression_ok = False
        metadata_detail += f"No impression with variation_key='on' and rule_key='{ROLLOUT_RULE_KEY}' found for forced user. "
    else:
        out.append(f"Forced user impression: rule_key='{forced_impressions[0].get('rule_key')}', "
                   f"variation_key='{forced_impressions[0].get('variation_key')}'")

    passed = forced_passed and regular_passed and impression_ok
    detail = ""
    if not forced_passed:
        detail += f"Forced user: expected 'on'/enabled=True, got '{forced_decision.variation_key}'/enabled={forced_decision.enabled}. "
    if not regular_passed:
        detail += f"Regular user: expected 'off'/enabled=False, got '{regular_decision.variation_key}'/enabled={regular_decision.enabled}. "
    detail += metadata_detail
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

    # Check impression metadata from decide() before clearing
    metadata_list = dispatcher.get_impression_metadata()
    impression_ok = True
    metadata_detail = ""
    if len(metadata_list) == 1:
        md = metadata_list[0]
        out.append(f"Impression metadata: rule_key='{md.get('rule_key')}', variation_key='{md.get('variation_key')}'")
        if md.get('variation_key') != "on":
            impression_ok = False
            metadata_detail += f"Impression variation_key: expected 'on', got '{md.get('variation_key')}'. "
        if md.get('rule_key') != ROLLOUT_RULE_KEY:
            impression_ok = False
            metadata_detail += f"Impression rule_key: expected '{ROLLOUT_RULE_KEY}', got '{md.get('rule_key')}'. "
    else:
        impression_ok = False
        metadata_detail += f"Expected 1 impression from decide(), got {len(metadata_list)}. "

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
    passed = decision_ok and conversion_dispatched and impression_ok
    detail = ""
    if not decision_ok:
        detail = f"User did not qualify for rollout (expected on/True, got {decision.variation_key}/{decision.enabled}). "
    if not conversion_dispatched:
        detail += f"Conversion event for '{EVENT_KEY}' was NOT dispatched -- expected it to be sent. "
    detail += metadata_detail
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

    # Check impression metadata for the normal (non-suppressed) call
    metadata_list = dispatcher2.get_impression_metadata()
    metadata_ok = True
    metadata_detail = ""
    if len(metadata_list) == 1:
        md = metadata_list[0]
        out.append(f"Normal call impression metadata: rule_key='{md.get('rule_key')}', variation_key='{md.get('variation_key')}'")
        if md.get('variation_key') != "on":
            metadata_ok = False
            metadata_detail += f"Normal call impression variation_key: expected 'on', got '{md.get('variation_key')}'. "
        if md.get('rule_key') != ROLLOUT_RULE_KEY:
            metadata_ok = False
            metadata_detail += f"Normal call impression rule_key: expected '{ROLLOUT_RULE_KEY}', got '{md.get('rule_key')}'. "
    elif impression_after_normal:
        metadata_ok = False
        metadata_detail += f"Expected 1 impression metadata, got {len(metadata_list)}. "

    decisions_ok = (
        decision_suppressed.enabled is True
        and decision_suppressed.variation_key == "on"
        and decision_normal.enabled is True
        and decision_normal.variation_key == "on"
    )
    suppression_ok = not impression_after_suppressed
    normal_ok = impression_after_normal

    passed = decisions_ok and suppression_ok and normal_ok and metadata_ok
    detail = ""
    if not decisions_ok:
        detail += "One or both decisions returned unexpected values. "
    if not suppression_ok:
        detail += "DISABLE_DECISION_EVENT did NOT suppress the impression -- event was still dispatched. "
    if not normal_ok:
        detail += "Normal decide() did NOT dispatch an impression -- expected one. "
    detail += metadata_detail
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
#   5. NO impression event is dispatched (Targeted Deliveries
#      do not dispatch impression events)
# ============================================================
def test_rule_fallthrough():
    out = ["Test 8: rule_fallthrough",
           "Verifying: audience mismatch causes fallthrough to next rule, no impression"]

    dispatcher = CapturingEventDispatcher()
    client = create_client(event_dispatcher=dispatcher)

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

    # Targeted Deliveries should NOT dispatch impression events
    no_impression = not dispatcher.has_impression()
    out.append(f"Impression dispatched: {dispatcher.has_impression()} (expected: False)")

    passed = got_on and skipped_rollout and no_impression
    detail = ""
    if not got_on:
        detail += f"Expected enabled=True, variation_key='on'; got enabled={decision.enabled}, variation_key='{decision.variation_key}'. Is the Targeted Delivery variation set to 'On'? "
    if not skipped_rollout:
        detail += f"User was bucketed into the Feature Rollout rule (rule_key='{decision.rule_key}') instead of falling through. Is the rollout audience set to 'US Users'? "
    if not no_impression:
        detail += "Impression event was dispatched but should NOT be for a Targeted Delivery fallthrough. "
    out.append(format_result("rule_fallthrough", passed, detail))
    print_report(out)


# ============================================================
# TEST 9: fr_skip_to_ab_rule
# ============================================================
# When a user does not match the Feature Rollout rule's audience
# but DOES match the audience of an A/B test rule placed below it,
# the user should skip the FR and be bucketed into the A/B test.
#
# UI SETUP:
#   1. Keep the Feature Rollout rule with Audience = "US Users",
#      Traffic = 100%, Variation = "On"
#   2. Add an A/B Test rule BELOW the Feature Rollout (and below
#      any Targeted Delivery if present):
#      - Click "Add Rule" -> "A/B Test"
#      - Name / Key: match AB_RULE_KEY in config above
#      - Traffic Allocation: 100%
#      - Audience: "Everyone"
#      - Variations: use default "on" and "off"
#      - Metrics: add your event ("feature_rollout_event")
#      - Save the rule
#   3. Make sure all rules and the ruleset are Running
#   4. Wait ~1 min for datafile to update
#
# Expected:
#   1. User with country="UK" skips the Feature Rollout rule
#   2. User is bucketed into the A/B test rule
#   3. decide() returns rule_key matching AB_RULE_KEY
#   4. An impression event IS dispatched (A/B tests send impressions)
#   5. Impression metadata has the A/B rule's rule_key and the
#      correct variation_key
# ============================================================
def test_fr_skip_to_ab_rule():
    out = ["Test 9: fr_skip_to_ab_rule",
           "Verifying: user skips FR (audience mismatch), falls into A/B test"]

    dispatcher = CapturingEventDispatcher()
    client = create_client(event_dispatcher=dispatcher)

    # UK user should NOT match "US Users" audience on the FR rule,
    # skip it, and land in the A/B test rule below
    user_id = f"ab_fallthrough_{uuid.uuid4().hex[:8]}"
    user = client.create_user_context(user_id, {"country": "UK"})
    decision = user.decide(FLAG_KEY, [OptimizelyDecideOption.INCLUDE_REASONS])
    client.close()

    out.append(f"User: {user_id} (country=UK)")
    out.append(format_decision(decision))

    # Decision should come from the AB rule, not the FR rule
    skipped_rollout = decision.rule_key != ROLLOUT_RULE_KEY
    in_ab_rule = decision.rule_key == AB_RULE_KEY

    # Impression event should be dispatched for A/B test
    has_impression = dispatcher.has_impression()
    metadata_list = dispatcher.get_impression_metadata()

    impression_ok = True
    metadata_detail = ""
    if not has_impression:
        impression_ok = False
        metadata_detail += "No impression event dispatched -- A/B tests should dispatch impressions. "
    elif len(metadata_list) >= 1:
        md = metadata_list[0]
        out.append(f"Impression metadata: rule_key='{md.get('rule_key')}', variation_key='{md.get('variation_key')}'")
        if md.get('rule_key') != AB_RULE_KEY:
            impression_ok = False
            metadata_detail += f"Impression rule_key: expected '{AB_RULE_KEY}', got '{md.get('rule_key')}'. "
        if md.get('variation_key') != decision.variation_key:
            impression_ok = False
            metadata_detail += (f"Impression variation_key mismatch: decision says '{decision.variation_key}', "
                                f"impression says '{md.get('variation_key')}'. ")

    passed = skipped_rollout and in_ab_rule and impression_ok
    detail = ""
    if not skipped_rollout:
        detail += f"User was bucketed into the Feature Rollout rule (rule_key='{decision.rule_key}') instead of skipping. "
    if not in_ab_rule:
        detail += f"Expected rule_key='{AB_RULE_KEY}', got '{decision.rule_key}'. "
    detail += metadata_detail
    out.append(format_result("fr_skip_to_ab_rule", passed, detail))
    print_report(out)


# ============================================================
# CLI RUNNER
# ============================================================

TESTS = {
    # "basic_rollout": test_basic_rollout,
    # "everyone_else": test_everyone_else,
    # "traffic_split": test_traffic_split,
    "audience_targeting": test_audience_targeting,
    # "forced_variation": test_forced_variation,
    # "conversion_tracking": test_conversion_tracking,
    # "disable_decision_event": test_disable_decision_event,
    # "rule_fallthrough": test_rule_fallthrough,
    # "fr_skip_to_ab_rule": test_fr_skip_to_ab_rule,
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
