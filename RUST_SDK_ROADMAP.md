# Optimizely Rust SDK Implementation Roadmap

## Overview

This document outlines the plan to implement a production-ready Rust SDK based on the existing Python SDK, maintaining 100% feature parity and API compatibility while achieving superior performance.

**Target**: Complete feature parity with Python SDK v5.4.0+
**Timeline**: ~2.5-3 months (70 days)
**Approach**: Incremental development with continuous testing and validation

---

## Workspace Structure

```
optimizely-rust-sdk/
├── Cargo.toml (workspace)
├── crates/
│   ├── optimizely-core/        # Domain entities, types
│   ├── optimizely-config/      # Datafile parsing, ProjectConfig
│   ├── optimizely-bucketing/   # MurmurHash3, bucketing logic
│   ├── optimizely-audience/    # Audience evaluation
│   ├── optimizely-decision/    # Decision service
│   ├── optimizely-events/      # Event processing, batching
│   ├── optimizely-user-profile/# User profile management
│   ├── optimizely-odp/         # ODP integration (Phase 7)
│   ├── optimizely-cmab/        # CMAB integration (Phase 7)
│   └── optimizely/             # Main SDK facade (public API)
└── tests/
    ├── integration/
    └── fixtures/               # Datafiles for testing
```

---

## Dependencies (Recommended Rust Crates)

```toml
# Essential (all phases)
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
thiserror = "1.0"
log = "0.4"

# Hashing (Phase 1)
murmur3 = "0.5" # or implement custom for exact compatibility

# HTTP & Async (Phase 5)
reqwest = { version = "0.11", features = ["json"] }
tokio = { version = "1", features = ["full"] }

# Events & Threading (Phase 5)
crossbeam-channel = "0.5"
parking_lot = "0.12" # Better mutex performance

# Semver (Phase 3)
semver = "1.0"

# Testing
mockito = "1.0" # HTTP mocking
proptest = "1.0" # Property-based testing
```

---

## Implementation Phases

### Phase 1: Foundation & Bucketing (Core Algorithm)

**Duration**: 3-5 days
**Goal**: Implement the deterministic bucketing algorithm - the heart of consistent user assignment

#### Components to Build

**Crate**: `optimizely-bucketing`

Key modules:
- MurmurHash3 implementation (equivalent to `lib/pymmh3.py`)
- Bucketer struct with methods:
  - `generate_bucket_value(bucketing_id: &str) -> u32`
  - `find_bucket(...) -> Option<String>`
  - `bucket(...) -> Option<Variation>`

**Crate**: `optimizely-core`

Basic entities (equivalent to `entities.py`):
```rust
pub struct Variation {
    pub id: String,
    pub key: String,
    pub variables: Vec<Variable>,
    // ... other fields
}

pub struct Experiment {
    pub id: String,
    pub key: String,
    pub status: String,
    pub traffic_allocation: Vec<TrafficAllocation>,
    // ... other fields
}

// Basic types and error handling
pub enum OptimizelyError {
    InvalidDatafile(String),
    InvalidInput(String),
    // ...
}
```

#### Python Files to Study
- `bucketer.py` - Core bucketing algorithm
- `lib/pymmh3.py` - MurmurHash3 implementation
- `entities.py` - Basic data structures

#### Testing Strategy
1. **Unit tests**: Test hash function produces same values as Python
2. **Bucketing compatibility**: Use test cases from `test_bucketing.py`
3. **Cross-validation**: Generate 1000 random user IDs, verify both SDKs bucket identically

#### Validation Criteria
```python
# Python script to validate:
for user_id in test_user_ids:
    python_bucket = python_bucketer.bucket(...)
    rust_bucket = rust_bucketer.bucket(...)
    assert python_bucket == rust_bucket
```

#### Success Criteria
✅ Bucketing produces identical results to Python for 10,000 random inputs

---

### Phase 2: Configuration Management (Datafile Parsing)

**Duration**: 5-7 days
**Goal**: Parse and index datafile into efficient lookup structures

#### Components to Build

**Crate**: `optimizely-config`

```rust
// Equivalent to project_config.py:
pub struct ProjectConfig {
    version: String,
    account_id: String,
    project_id: String,

    // Indexed maps for O(1) lookup
    experiment_id_map: HashMap<String, Experiment>,
    event_key_map: HashMap<String, Event>,
    feature_flag_key_map: HashMap<String, FeatureFlag>,
    // ... other maps

    pub fn from_datafile(datafile: &str) -> Result<Self, OptimizelyError>;
    pub fn get_experiment_from_key(&self, key: &str) -> Option<&Experiment>;
    // ... other getters
}
```

#### Key Implementation Details
1. Use `serde` for JSON deserialization
2. Build all lookup HashMaps during construction (same as Python)
3. Support datafile versions V2, V3, V4
4. Parse holdouts (equivalent to `entities.py:104-132`)

#### Python Files to Study
- `project_config.py` - Datafile parsing and indexing
- `entities.py` - All entity types
- `config_manager.py` - Configuration management patterns

#### Testing Strategy
1. **Datafile parsing**: Use actual Optimizely datafiles from `tests/` directory
2. **Lookup verification**: Verify all maps populated correctly
3. **Cross-validation**: Compare parsed entities with Python SDK

#### Validation Criteria
```rust
#[test]
fn test_datafile_parsing_matches_python() {
    let datafile = include_str!("../../fixtures/datafile.json");
    let rust_config = ProjectConfig::from_datafile(datafile).unwrap();

    // Verify counts match Python
    assert_eq!(rust_config.experiments.len(), 10);
    assert_eq!(rust_config.feature_flags.len(), 5);
    // ... more assertions
}
```

#### Success Criteria
✅ Parse all test datafiles without errors
✅ All lookup maps contain correct entities

---

### Phase 3: Audience Evaluation Engine

**Duration**: 7-10 days
**Goal**: Evaluate complex user attribute conditions for targeting

#### Components to Build

**Crate**: `optimizely-audience`

```rust
// Equivalent to helpers/condition.py:
pub trait ConditionEvaluator {
    fn evaluate(&self, attributes: &UserAttributes) -> Option<bool>;
}

pub struct CustomAttributeConditionEvaluator {
    // Implements exact, gt, lt, substring, semver_*, qualified matching
}

pub struct ConditionTreeEvaluator {
    // Implements AND, OR, NOT logic
}

// Match types from helpers/condition.py:45-58
pub enum MatchType {
    Exact,
    Exists,
    GreaterThan,
    GreaterThanOrEqual,
    LessThan,
    LessThanOrEqual,
    Substring,
    SemverEq,
    SemverGe,
    SemverGt,
    SemverLe,
    SemverLt,
    Qualified, // for ODP segments
}
```

#### Key Implementation Details
1. Implement semantic version comparison (use `semver` crate)
2. Handle null/missing/invalid attribute values correctly
3. Recursive condition evaluation for AND/OR/NOT trees
4. Type coercion matching Python behavior exactly

#### Python Files to Study
- `helpers/condition.py` - Condition evaluation logic
- `helpers/condition_tree_evaluator.py` - Tree evaluation
- `helpers/audience.py` - Audience matching
- `helpers_tests/test_condition.py` - Comprehensive test cases

#### Testing Strategy
1. **Unit tests**: Each match type with edge cases
2. **Complex conditions**: Nested AND/OR/NOT from `helpers_tests/test_condition.py`
3. **Cross-validation**: Same audience + attributes should give same result

#### Validation Criteria
```rust
#[test]
fn test_audience_evaluation_parity() {
    let test_cases = load_test_cases_from_python();
    for case in test_cases {
        let python_result = case.python_result;
        let rust_result = evaluator.evaluate(&case.attributes);
        assert_eq!(python_result, rust_result);
    }
}
```

#### Success Criteria
✅ Pass all audience evaluation tests from Python test suite
✅ Semantic version comparisons match Python exactly

---

### Phase 4: Core Decision Service (A/B Testing)

**Duration**: 7-10 days
**Goal**: Make experiment/feature flag decisions (no user profiles yet)

#### Components to Build

**Crate**: `optimizely-decision`

```rust
// Equivalent to decision_service.py:
pub struct DecisionService {
    bucketer: Bucketer,
}

impl DecisionService {
    pub fn get_variation(
        &self,
        config: &ProjectConfig,
        experiment: &Experiment,
        user_id: &str,
        attributes: &UserAttributes,
    ) -> Decision;

    pub fn get_variation_for_feature(
        &self,
        config: &ProjectConfig,
        feature_flag: &FeatureFlag,
        user_id: &str,
        attributes: &UserAttributes,
    ) -> Decision;
}

pub struct Decision {
    pub experiment: Option<Experiment>,
    pub variation: Option<Variation>,
    pub source: DecisionSource,
    pub reasons: Vec<String>, // for logging/debugging
}
```

#### Key Implementation Details
1. Integrate bucketing (Phase 1)
2. Integrate audience evaluation (Phase 3)
3. Handle forced variations (whitelisting)
4. Rollout rules for feature flags
5. Holdout evaluation (equivalent to `project_config.py:92-132`)

#### Python Files to Study
- `decision_service.py` - Core decision logic
- `test_decision_service.py` - Decision test cases
- `test_decision_service_holdout.py` - Holdout tests
- `bucketer.py` - Integration with bucketing

#### Testing Strategy
1. **Decision flow tests**: From `test_decision_service.py`
2. **Holdout tests**: From `test_decision_service_holdout.py`
3. **Feature flag tests**: Rollout targeting logic

#### Validation Criteria
```rust
#[test]
fn test_decisions_match_python() {
    // For 100 users across 10 experiments:
    for (user_id, experiment_key) in test_matrix {
        let python_decision = python_sdk.get_variation(...);
        let rust_decision = rust_sdk.get_variation(...);
        assert_eq!(python_decision.variation_key, rust_decision.variation_key);
    }
}
```

#### Success Criteria
✅ 100% decision parity with Python SDK across 1000 user/experiment combinations
✅ Holdout logic works identically to Python

---

### Phase 5: Event Processing & HTTP

**Duration**: 5-7 days
**Goal**: Track events and send them to Optimizely backend

#### Components to Build

**Crate**: `optimizely-events`

```rust
// Equivalent to event/ package:
pub struct EventFactory {
    pub fn create_impression_event(...) -> LogEvent;
    pub fn create_conversion_event(...) -> LogEvent;
}

pub struct BatchEventProcessor {
    event_queue: Sender<UserEvent>,
    batch_size: usize,
    flush_interval: Duration,

    pub fn process(&self, user_event: UserEvent);
    pub fn start(&self); // Background thread
    pub fn stop(&self);
}

pub struct EventDispatcher {
    client: reqwest::Client,
    pub async fn dispatch_event(&self, log_event: LogEvent) -> Result<()>;
}
```

#### Key Implementation Details
1. Async HTTP client with `reqwest`
2. Background thread for event batching (use `crossbeam-channel`)
3. Flush on: batch size reached OR timeout OR shutdown signal
4. Match Python event payload structure exactly

#### Python Files to Study
- `event/event_processor.py` - Batching logic
- `event/event_factory.py` - Event construction
- `event/user_event_factory.py` - User event creation
- `event_builder.py` - Event building
- `event_dispatcher.py` - HTTP dispatching

#### Testing Strategy
1. **Event construction**: Verify JSON payload matches Python
2. **Batching logic**: Test flush triggers
3. **Mock HTTP**: Use `mockito` to verify dispatched events

#### Validation Criteria
```rust
#[test]
fn test_event_payload_matches_python() {
    let python_payload = python_sdk.create_impression_event(...);
    let rust_payload = rust_sdk.create_impression_event(...);
    assert_json_eq!(python_payload, rust_payload);
}
```

#### Success Criteria
✅ Event payloads are byte-for-byte identical to Python
✅ Batching logic matches Python behavior exactly

---

### Phase 6: Main SDK Facade & User Profiles

**Duration**: 7-10 days
**Goal**: Public API that users interact with + persistent bucketing

#### Components to Build

**Crate**: `optimizely` (main public crate)

```rust
// Equivalent to optimizely.py:
pub struct Optimizely {
    config_manager: Arc<dyn ConfigManager>,
    decision_service: DecisionService,
    event_processor: Arc<dyn EventProcessor>,
    notification_center: NotificationCenter,
}

impl Optimizely {
    pub fn new(config: OptimizelyConfig) -> Result<Self>;

    // Core API matching Python:
    pub fn activate(
        &self,
        experiment_key: &str,
        user_id: &str,
        attributes: Option<&UserAttributes>,
    ) -> Option<String>;

    pub fn track(
        &self,
        event_key: &str,
        user_id: &str,
        attributes: Option<&UserAttributes>,
        event_tags: Option<&EventTags>,
    );

    pub fn is_feature_enabled(
        &self,
        feature_key: &str,
        user_id: &str,
        attributes: Option<&UserAttributes>,
    ) -> bool;

    pub fn get_feature_variable_boolean(...) -> Option<bool>;
    pub fn get_feature_variable_double(...) -> Option<f64>;
    pub fn get_feature_variable_integer(...) -> Option<i64>;
    pub fn get_feature_variable_string(...) -> Option<String>;

    // Decide API (new Python SDK style):
    pub fn create_user_context(&self, user_id: &str) -> UserContext;
}

pub struct UserContext {
    pub fn decide(&self, flag_key: &str) -> OptimizelyDecision;
    pub fn decide_all(&self) -> HashMap<String, OptimizelyDecision>;
    pub fn decide_for_keys(&self, keys: &[&str]) -> HashMap<String, OptimizelyDecision>;
    pub fn set_attribute(&mut self, key: &str, value: AttributeValue);
    pub fn track_event(&self, event_key: &str);
}
```

**Crate**: `optimizely-user-profile`

```rust
// Equivalent to user_profile.py:
pub trait UserProfileService: Send + Sync {
    fn lookup(&self, user_id: &str) -> Option<UserProfile>;
    fn save(&self, user_profile: &UserProfile);
}

pub struct UserProfile {
    user_id: String,
    experiment_bucket_map: HashMap<String, BucketDecision>,
}
```

#### Key Implementation Details
1. Thread-safe using `Arc` and `RwLock`/`Mutex`
2. Lazy initialization supported
3. Builder pattern for configuration
4. Notification center (observer pattern)

#### Python Files to Study
- `optimizely.py` - Main SDK class
- `optimizely_user_context.py` - User context
- `user_profile.py` - Profile persistence
- `optimizely_factory.py` - Factory pattern
- `notification_center.py` - Observer pattern

#### Testing Strategy
1. **API compatibility tests**: Call same methods as Python
2. **User profile persistence**: Verify sticky bucketing works
3. **End-to-end tests**: Full SDK workflow

#### Validation Criteria
```rust
#[test]
fn test_sdk_activate_matches_python() {
    let rust_sdk = Optimizely::new(config).unwrap();
    let python_sdk = create_python_sdk(config);

    for user_id in test_users {
        let rust_var = rust_sdk.activate("exp1", user_id, None);
        let python_var = python_sdk.activate("exp1", user_id, None);
        assert_eq!(rust_var, python_var);
    }
}
```

#### Success Criteria
✅ All public API methods match Python behavior
✅ User profile service maintains sticky bucketing

---

### Phase 7: Advanced Features (CMAB, ODP, Polling Config)

**Duration**: 10-14 days
**Goal**: Add ML-based decisions, audience segmentation, and auto-updating config

#### Components to Build

**Crate**: `optimizely-cmab`

```rust
// Equivalent to cmab/ package:
pub struct CmabClient {
    pub async fn get_decision(...) -> Result<CmabDecision>;
}

pub struct CmabService {
    client: CmabClient,
    cache: LruCache<String, CmabDecision>,

    pub async fn get_decision_for_experiment(...) -> Result<CmabDecision>;
}
```

**Crate**: `optimizely-odp`

```rust
// Equivalent to odp/ package:
pub struct OdpManager {
    segment_manager: OdpSegmentManager,
    event_manager: OdpEventManager,
}

pub struct OdpSegmentManager {
    pub async fn fetch_qualified_segments(&self, user_id: &str) -> Vec<String>;
}

pub struct OdpEventManager {
    pub fn send_event(&self, event: OdpEvent);
}
```

**Config Manager Enhancements**:

```rust
// Equivalent to config_manager.py:
pub struct PollingConfigManager {
    sdk_key: String,
    update_interval: Duration,
    // Spawns background task to poll CDN
}

pub struct AuthDatafilePollingConfigManager {
    datafile_access_token: String,
    // Authenticated polling
}
```

#### Python Files to Study
- `cmab/cmab_client.py` - CMAB client
- `cmab/cmab_service.py` - CMAB service with caching
- `odp/odp_manager.py` - ODP orchestration
- `odp/odp_segment_manager.py` - Segment fetching
- `odp/odp_event_manager.py` - Event streaming
- `config_manager.py` - Polling logic

#### Success Criteria
✅ CMAB produces same decisions as Python
✅ ODP segment fetching works identically
✅ Polling config manager updates automatically

---

### Phase 8: Performance Optimization & Production Hardening

**Duration**: 5-7 days
**Goal**: Make it production-ready and faster than Python

#### Performance Focus Areas

1. **Bucketing** (hot path):
   - Benchmark MurmurHash3 implementation
   - Consider SIMD optimizations for batch bucketing
   - Pre-compute traffic allocation lookup tables

2. **Audience Evaluation**:
   - Compile conditions to bytecode for repeated evaluation
   - Cache evaluation results with LRU
   - Parallel evaluation for multiple audiences

3. **Memory**:
   - Use `Arc` to share ProjectConfig across threads (zero-copy)
   - String interning for repeated IDs/keys
   - Consider `bytes::Bytes` for zero-copy string handling

4. **Event Processing**:
   - Lock-free queue for event batching
   - Connection pooling for HTTP client
   - Compress event payloads

#### Benchmarking Targets

Compare with Python SDK:
1. **Throughput**: 10,000+ decisions/sec (vs ~1,000 in Python)
2. **Memory**: 50% less memory for same datafile
3. **Latency**: <1ms p99 for decision (vs ~10ms in Python)
4. **Event processing**: Higher throughput, lower latency

#### Production Readiness Checklist

- [ ] Comprehensive error handling
- [ ] Graceful shutdown for background threads
- [ ] Metrics and observability hooks
- [ ] Documentation and examples
- [ ] Security audit (dependency scanning)
- [ ] Fuzz testing for datafile parsing
- [ ] Load testing under production scenarios

#### Success Criteria
✅ 10x throughput improvement over Python SDK
✅ Memory usage < 50% of Python SDK
✅ Zero crashes in 1M+ decision stress test

---

## Testing Strategy Summary

### Unit Tests (Each Phase)

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bucketing_parity() {
        // Test Python behavior parity
    }

    #[test]
    fn test_audience_evaluation_parity() {
        // Test Python behavior parity
    }
}
```

### Integration Tests (After Phase 6)

```rust
// tests/integration/compatibility.rs
// Load same datafile, verify same decisions

#[test]
fn test_full_sdk_python_parity() {
    let datafile = load_test_datafile();
    let rust_sdk = Optimizely::new(datafile).unwrap();
    let python_sdk = create_python_sdk(datafile);

    let test_matrix = load_compatibility_matrix();
    for case in test_matrix {
        let rust_result = rust_sdk.activate(case.exp_key, case.user_id, case.attrs);
        let python_result = python_sdk.activate(case.exp_key, case.user_id, case.attrs);
        assert_eq!(rust_result, python_result);
    }
}
```

### Property-Based Tests

```rust
use proptest::prelude::*;

proptest! {
    #[test]
    fn bucketing_is_deterministic(user_id in ".*", experiment_id in ".*") {
        let bucket1 = bucketer.bucket(&user_id, &experiment_id);
        let bucket2 = bucketer.bucket(&user_id, &experiment_id);
        assert_eq!(bucket1, bucket2);
    }

    #[test]
    fn decisions_are_deterministic(user_id in ".*", exp_key in ".*") {
        let decision1 = sdk.activate(exp_key, user_id, None);
        let decision2 = sdk.activate(exp_key, user_id, None);
        assert_eq!(decision1, decision2);
    }
}
```

### Cross-SDK Validation

Create Python test harness:

```python
# tests/python_validator.py
import json
from optimizely import optimizely

def validate_rust_sdk(rust_output_file):
    """Compare Rust SDK output with Python SDK"""
    with open(rust_output_file) as f:
        rust_results = json.load(f)

    python_sdk = optimizely.Optimizely(datafile=DATAFILE)

    for test_case in rust_results:
        python_result = python_sdk.activate(
            test_case['experiment_key'],
            test_case['user_id'],
            test_case['attributes']
        )
        assert python_result == test_case['rust_result'], \
            f"Mismatch for {test_case}"
```

---

## Migration Path (Python → Rust)

### Gradual Rollout Strategy

#### 1. Shadow Mode (Compare Results)
```python
rust_decision = rust_sdk.activate(exp_key, user_id)
python_decision = python_sdk.activate(exp_key, user_id)

if rust_decision != python_decision:
    log_discrepancy(exp_key, user_id, rust_decision, python_decision)
    metrics.increment('rust_sdk.discrepancy')

return python_decision  # Still use Python
```

#### 2. Canary Deployment (1% Traffic)
```python
if random.random() < 0.01:  # 1% traffic
    return rust_sdk.activate(exp_key, user_id)
return python_sdk.activate(exp_key, user_id)
```

#### 3. Gradual Rollout (10% → 50% → 100%)
```python
rollout_percentage = get_rust_sdk_rollout_percentage()
if random.random() < rollout_percentage:
    return rust_sdk.activate(exp_key, user_id)
return python_sdk.activate(exp_key, user_id)
```

#### 4. Full Rollout
```python
return rust_sdk.activate(exp_key, user_id)
```

---

## Timeline Summary

| Phase | Focus | Duration | Cumulative | Deliverable |
|-------|-------|----------|------------|-------------|
| 1 | Foundation & Bucketing | 3-5 days | 5 days | Deterministic user assignment |
| 2 | Configuration Management | 5-7 days | 12 days | Datafile parsing |
| 3 | Audience Evaluation | 7-10 days | 22 days | User targeting |
| 4 | Decision Service | 7-10 days | 32 days | A/B testing decisions |
| 5 | Event Processing | 5-7 days | 39 days | Event tracking |
| 6 | Main SDK & User Profiles | 7-10 days | 49 days | Full public API |
| 7 | CMAB/ODP/Polling | 10-14 days | 63 days | Advanced features |
| 8 | Performance & Hardening | 5-7 days | **70 days** | Production ready |

**Total: ~2.5-3 months for full parity**

---

## Success Metrics

### Functional Parity
- ✅ 100% API compatibility with Python SDK
- ✅ Identical decision outcomes for all test cases
- ✅ Identical event payloads
- ✅ Support all datafile versions (V2, V3, V4)

### Performance Targets
- ✅ 10x throughput improvement (10,000+ decisions/sec)
- ✅ 50% memory reduction
- ✅ <1ms p99 latency for decisions
- ✅ Zero panics/crashes in stress testing

### Production Readiness
- ✅ Comprehensive test coverage (>90%)
- ✅ Full documentation
- ✅ Zero high-severity security vulnerabilities
- ✅ Successful canary deployment

---

## Risk Mitigation

### Technical Risks

1. **Behavioral Differences**
   - **Risk**: Subtle differences in bucketing/decisions
   - **Mitigation**: Extensive cross-validation tests, shadow mode deployment

2. **Performance Regression**
   - **Risk**: Rust SDK slower than expected
   - **Mitigation**: Continuous benchmarking, profiling, optimization phase

3. **Dependency Issues**
   - **Risk**: Rust crates have vulnerabilities or are unmaintained
   - **Mitigation**: Regular dependency audits, consider vendoring critical code

### Timeline Risks

1. **Underestimated Complexity**
   - **Risk**: Phases take longer than estimated
   - **Mitigation**: Build buffer time, prioritize core features over advanced

2. **Learning Curve**
   - **Risk**: Rust learning curve slows development
   - **Mitigation**: Start with simple modules, leverage community resources

---

## Resources & References

### Python SDK Files (Priority Study Order)

1. **Phase 1**: `bucketer.py`, `lib/pymmh3.py`, `entities.py`
2. **Phase 2**: `project_config.py`, `config_manager.py`
3. **Phase 3**: `helpers/condition.py`, `helpers/audience.py`, `helpers/condition_tree_evaluator.py`
4. **Phase 4**: `decision_service.py`
5. **Phase 5**: `event/event_processor.py`, `event/event_factory.py`, `event_dispatcher.py`
6. **Phase 6**: `optimizely.py`, `optimizely_user_context.py`, `user_profile.py`
7. **Phase 7**: `cmab/`, `odp/`

### Test Files (For Validation)

- `test_bucketing.py` - Bucketing test cases
- `test_bucketing_holdout.py` - Holdout bucketing
- `test_decision_service.py` - Decision tests
- `test_decision_service_holdout.py` - Holdout decision tests
- `helpers_tests/test_condition.py` - Audience evaluation tests
- `test_event_processor.py` - Event processing tests

### External Resources

- [Rust Book](https://doc.rust-lang.org/book/) - Rust fundamentals
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/) - Best practices
- [Tokio Tutorial](https://tokio.rs/tokio/tutorial) - Async programming
- [Serde Documentation](https://serde.rs/) - Serialization

---

## Next Steps

1. **Set up workspace**: Create Cargo workspace with initial crates
2. **Start Phase 1**: Implement bucketing algorithm
3. **Create test harness**: Python script to validate Rust output
4. **Establish CI/CD**: Automated testing and benchmarking

**Ready to begin implementation?** Start with Phase 1 - the bucketing module is self-contained and builds confidence in the approach.
