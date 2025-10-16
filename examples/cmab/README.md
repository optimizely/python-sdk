# CMAB Testing Guide for Optimizely Python SDK

This directory contains comprehensive test scenarios for Contextual Multi-Armed Bandit (CMAB) functionality in the Optimizely Python SDK.

## Prerequisites

Before running these tests, you need to configure your own project in the Optimizely RC (Prep) environment:

1. **Create a CMAB-enabled flag experiment**:
   - In the Optimizely UI, create a new flag experiment
   - Enable CMAB by clicking two UI buttons (as per CMAB setup process)

2. **Configure audience targeting**:
   - Add a custom attribute named `cmab_test_attribute`
   - Set up audience conditions: `cmab_test_attribute` equals "hello" OR `cmab_test_attribute` equals "world"

3. **Update configuration in main.py**:
   - Replace `SDK_KEY` with your project's SDK key
   - Replace `FLAG_KEY` with your flag key

4. **Environment details**:
   - Datafile URL: `https://optimizely-staging.s3.amazonaws.com/datafiles/{sdk_key}.json`
   - CMAB endpoint: `https://prep.prediction.cmab.optimizely.com/`

## Running the Tests

From the python-sdk root directory, run:

```bash
# Run all tests
python examples/cmab/main.py

# Run a specific test
python examples/cmab/main.py --test=basic
python examples/cmab/main.py --test=cache_hit
python examples/cmab/main.py --test=concurrent
```

## Available Test Cases

### Core Tests (1-6): Basic Functionality and Cache Management

1. **basic** - Basic CMAB functionality
   - Tests fundamental CMAB decision-making
   - Validates cache behavior across multiple calls with different attributes
   - Expected: First call with new attributes makes API call, subsequent calls with same attributes use cache

2. **cache_hit** - Cache hit with same user and attributes
   - Tests cache retrieval when user and attributes are identical
   - Expected: First decision makes CMAB API call, second with same params uses cache

3. **cache_miss** - Cache miss when attributes change
   - Tests cache invalidation when relevant attributes change
   - Expected: Different attribute values trigger fresh API calls

4. **ignore_cache** - IGNORE_CMAB_CACHE option
   - Tests bypassing cache without clearing it
   - Expected: Cache ignored for current call but preserved for future calls

5. **reset_cache** - RESET_CMAB_CACHE option
   - Tests clearing entire CMAB cache
   - Expected: All cached decisions removed, new API calls for all users

6. **invalidate_user** - INVALIDATE_USER_CMAB_CACHE option
   - Tests clearing cache for specific user only
   - Expected: Only specified user's cache cleared, other users' cache preserved

### Advanced Tests (7-14): Edge Cases and Performance

7. **concurrent** - Concurrent requests for same user
   - Tests thread safety and cache consistency
   - Expected: All concurrent threads return same variation (cache synchronization)
   - Note: Known issue - may show race condition with inconsistent variations

8. **error** - Error handling with invalid attributes
   - Tests graceful fallback when attribute types don't match
   - Expected: Falls back to rollout, no CMAB API call

9. **fallback** - Fallback when not qualified for CMAB
   - Tests behavior when user doesn't match audience
   - Expected: Falls to rollout variation, no CMAB API call

10. **traffic** - Traffic allocation check
    - Tests user bucketing with traffic allocation
    - Note: Requires manual configuration of 50% traffic allocation in UI
    - Expected: Some users get CMAB, others fall to rollout

11. **forced** - Forced variation override
    - Tests forced variation precedence over CMAB
    - Note: Requires forced variations configured in datafile
    - Expected: Forced variations bypass CMAB API calls

12. **event_tracking** - Event tracking with CMAB UUID
    - Tests impression and conversion event metadata
    - Expected: Impression events include CMAB UUID, conversion events do not

13. **attribute_types** - Attribute types and filtering
    - Tests attribute validation and filtering
    - Expected: Only valid CMAB attributes sent to API

14. **performance** - Performance benchmarks
    - Measures API call vs cache performance
    - Expected: Cached calls <10ms, API calls <500ms

15. **cache_expiry** - Cache expiry (simulated)
    - Tests TTL-based cache invalidation
    - Note: Real expiry requires 30+ minute wait
    - Expected: Cache entries expire after TTL

## Expected Behaviors

### Cache Behavior
- **Cache Key**: Generated from user ID + rule ID
- **Cache Hit**: Same user + same filtered attributes = cached result
- **Cache Miss**: Different user OR different filtered attributes = new API call
- **Attribute Filtering**: Only CMAB-configured attributes included in cache key

### Performance Targets
- Cached decisions: < 10ms
- API calls: < 500ms
- Cache TTL: 30 minutes (default)

### Thread Safety
- Uses lock striping (1000 locks) for concurrent access
- Same user+rule combination uses same lock
- Different combinations can execute in parallel

## Known Issues

1. **Concurrent Test (Test 7)**:
   - Race condition may cause inconsistent variations across simultaneous requests
   - All threads should return same variation, but timing issues may occur

2. **Traffic Allocation Test (Test 10)**:
   - Requires manual configuration of 50% traffic allocation in Optimizely UI
   - Keep at 100% for other tests to ensure consistent behavior

## Validation Checklist

When running tests, verify:
- [ ] CMAB-qualified users trigger API calls (check debug logs)
- [ ] Cache hits don't trigger new API calls
- [ ] Cache options (ignore, reset, invalidate) work as expected
- [ ] Non-qualified users fall back to rollout
- [ ] Performance metrics meet targets
- [ ] Events are tracked correctly

## Troubleshooting

**No CMAB API calls appearing:**
- Verify flag is CMAB-enabled in UI
- Check audience targeting matches test attributes
- Ensure traffic allocation is 100% (unless testing traffic split)

**All calls hitting API (no cache):**
- Check that attributes remain consistent between calls
- Verify cache isn't being reset between calls
- Look for attribute filtering issues

**Inconsistent variations:**
- May indicate concurrency issue (Test 7)
- Check if forced variations are configured
- Verify user ID is consistent

## Additional Resources

- Python SDK Documentation: https://docs.developers.optimizely.com/full-stack/docs/python-sdk
- CMAB Overview: https://docs.developers.optimizely.com/feature-experimentation/docs/contextual-multi-armed-bandits
- Go SDK CMAB Example: https://github.com/optimizely/go-sdk/tree/mpirnovar-gosdk-bash/examples/cmab
