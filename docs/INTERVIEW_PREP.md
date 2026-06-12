# System Design Interview Preparation

Complete guide for interviewing for engineering roles using the Carpool project as examples.

---

## System Design Interview Strategy

### Framework: DARE
1. **D**efine requirements
2. **A**rchitecture design
3. **R**efine & optimize
4. **E**xplain trade-offs

---

## Interview Question 1: Scale to 1M Users

**Q: How would you scale this system from 10K to 1M daily rides?**

### Answer Structure

**1. Define Requirements**
```
Current:
- 10K rides/day
- ~1000 concurrent users
- 19 API endpoints
- Single PostgreSQL instance
- Single backend server

Target:
- 1M rides/day (100x growth)
- 100K concurrent users (100x)
- Global coverage (multiple regions)
- 99.99% availability
- Sub-200ms latency P95
```

**2. Bottleneck Analysis**

```
Database:
- 10K rides = 10K writes/day = 0.1 writes/sec (trivial)
- 1M rides = 1M writes/day = 11.6 writes/sec (still trivial)
- BUT: 100K concurrent queries = 100K reads/sec
- Single PostgreSQL instance can handle ~1000 writes/sec, ~5000 reads/sec
- → Need read replicas + sharding at 100K reads/sec

Network:
- 100K users × 4 API calls = 400K requests/sec
- Each request = ~1KB → 400MB/sec bandwidth
- Single backend instance = bottleneck
- → Need 100+ backend instances

Cache:
- Most queries are repetitive (same source/dest pairs)
- 80/20 rule: 20% of routes handle 80% of queries
- → Aggressive caching essential
```

**3. Architecture for 1M Scale**

```
┌────────────────────────────────────────────────────────┐
│                    Global CDN (CloudFront)             │
│                   (Static assets)                      │
└─────────────────────┬──────────────────────────────────┘
                      │
    ┌─────────────────┼─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
┌─────────┐      ┌─────────┐      ┌─────────┐
│AWS US   │      │AWS EU   │      │AWS APAC │
│Region   │      │Region   │      │Region   │
│Route 53 │      │Route 53 │      │Route 53 │
└────┬────┘      └────┬────┘      └────┬────┘
     │                │                │
     ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ ALB          │ │ ALB          │ │ ALB          │
│ ASG(50)      │ │ ASG(50)      │ │ ASG(50)      │
└───┬──────────┘ └───┬──────────┘ └───┬──────────┘
    │                │                │
    ├────────────────┼────────────────┤
    │                │                │
    ▼                ▼                ▼
  Redis Cluster (3 nodes, 10GB each)
  (Global cache, 100K requests/sec)
    
    │
    ▼
  PostgreSQL Primary (Write)
    │
    ├─► PostgreSQL Replica 1 (Read)
    ├─► PostgreSQL Replica 2 (Read)
    └─► PostgreSQL Replica 3 (Read) [Different region]
    
  Kafka Cluster (5 brokers)
  (Event stream, 1M events/day)
    │
    ├─► Stream Processor 1 (Matcher service)
    ├─► Stream Processor 2 (Analytics)
    └─► Stream Processor 3 (Notifications)
```

**4. Database Sharding Strategy**

```python
# Shard by user_id to keep data locally
user_shard = user_id % NUM_SHARDS  # 100 shards

# Connection routing
def get_db_connection(user_id):
    shard_id = user_id % 100
    return SHARD_POOL[shard_id]

# Read replicas within shard
# Shard 0: {Primary US-East, Replica US-West, Replica EU}
# Shard 1: {Primary US-East, Replica US-West, Replica EU}
```

**5. Caching Strategy**

```
Level 1: Browser cache (HTTP headers)
- Static assets: 1 year
- User profile: 1 hour
- Rides: 5 minutes

Level 2: CDN cache (CloudFront)
- Popular routes: 10 minutes
- City-level aggregates: 30 minutes

Level 3: Application cache (Redis)
- Hot rides (matches): 5 minutes
- User preferences: 30 minutes
- Spatial indexes: in-memory (per instance)

Cache Invalidation:
- Time-based: 5 minute TTL
- Event-based: Publish INVALIDATION event on ride cancel
- LRU: Keep top 1M rides in cache
```

**6. API Optimization**

```
Compression:
- gzip for all text responses (-70% payload)
- WebP for images (-50% vs JPEG)

Pagination:
- Cursor-based (not offset)
- Max 100 results per request

Query Optimization:
- SELECT only needed fields
- Join optimization with PostGIS indexes
- N+1 query prevention

Batching:
- Allow /api/matches/batch?ride_ids=1,2,3
- Reduce round-trips
```

**7. Monitoring at Scale**

```
Metrics dashboard:
- Requests per second (by endpoint)
- Latency distribution (P50, P95, P99)
- Error rate (5xx, 4xx)
- Database connections
- Cache hit ratio
- Message queue depth

Alerts:
- Latency > 500ms
- Error rate > 1%
- Queue depth > 10K
- Database replication lag > 1s
```

---

## Interview Question 2: Fraud & Abuse Detection

**Q: How would you detect and prevent fraud in the matching system?**

### Answer

**Fraud Types**:
1. **Bot accounts**: Creating fake profiles, flooding with fake rides
2. **Scams**: Drivers canceling after payment, riders ghosting
3. **Collusion**: Coordinated fake matches to game ratings
4. **Spam**: Posting 100+ rides to clog system

**Detection Strategies**:

```python
# 1. Rule-based checks
def check_fraud_heuristics(user):
    if user.created_days_ago < 1 and user.rides_count > 10:
        return {"risk": "high", "reason": "new_user_high_activity"}
    
    if user.cancellation_rate > 0.7:
        return {"risk": "high", "reason": "high_cancellation"}
    
    if user.avg_response_time_sec < 2:
        return {"risk": "medium", "reason": "unnatural_response_time"}
    
    return {"risk": "low"}

# 2. Anomaly detection (Isolation Forest)
from sklearn.ensemble import IsolationForest

model = IsolationForest(contamination=0.05)
features = [
    rides_per_day,
    messages_per_ride,
    cancellation_rate,
    average_rating,
    time_between_rides_sec
]

anomalies = model.predict(features)
if anomalies == -1:  # Anomaly
    flag_for_review(user_id)

# 3. Behavioral changes
def detect_behavior_change(user_id):
    current_stats = get_user_stats(user_id, days=7)
    historical_stats = get_user_stats(user_id, days=30)
    
    if current_stats['avg_rating'] < historical_stats['avg_rating'] - 1.0:
        return {"risk": "medium", "reason": "rating_drop"}
    
    if current_stats['rides_per_day'] > historical_stats['avg_rides_per_day'] * 5:
        return {"risk": "high", "reason": "activity_spike"}

# 4. Graph-based detection (co-occurrence)
def detect_collusion_ring(user_id):
    # Find users who frequently match with this user
    frequent_matches = db.query(
        Match.rider_id,
        func.count().label('count')
    ).filter(
        Match.driver_id == user_id
    ).group_by(Match.rider_id).all()
    
    # If too frequent with same riders, possible collusion
    for rider_id, count in frequent_matches:
        if count > 20:  # Suspiciously high
            # Check if those riders also rate highly
            if same_rider_group_all_5_stars(rider_id):
                alert_fraud_team(f"Possible collusion ring: {user_id}, {rider_id}")
```

**Prevention Measures**:

```
1. KYC (Know Your Customer):
   - Email verification (required)
   - Phone verification (required)
   - ID verification (photo) (optional but recommended)
   - Driver's license scan (for drivers)

2. Rate Limiting:
   - Max 5 rides posted per hour
   - Max 10 matches accepted per day (new users)
   - Max 10 messages per ride

3. Escrow System:
   - Money held until ride completed
   - Released after both rate each other

4. Gradual Access:
   - New users: Limited to 5 matches/day
   - After 10 successful rides: Unlimited
   - Reputation score gate: <50 trust score = limited

5. Review System:
   - Human review of flagged users
   - Suspension for verified fraud
   - Appeal process
```

---

## Interview Question 3: ML Model Drift

**Q: How would you monitor for ML model performance degradation in production?**

### Answer

**Common Drift Scenarios**:
```
1. Data drift:
   - User behavior changes (peak hours shift)
   - New cities with different patterns
   - Seasonal changes (college semester breaks)

2. Concept drift:
   - User preferences change over time
   - External factors (fuel prices, traffic patterns)
   - Trust score calibration outdated

3. Label drift:
   - "Good match" definition changes
   - User expectations evolve
```

**Monitoring Strategy**:

```python
# 1. Monitor input feature distributions
def detect_data_drift():
    current_features = get_recent_features(days=7)
    historical_features = get_features(days=30, end_offset=7)
    
    # Kullback-Leibler divergence for each feature
    for feature in FEATURE_NAMES:
        current_dist = current_features[feature]
        historical_dist = historical_features[feature]
        
        kl_div = entropy(current_dist, historical_dist)
        if kl_div > 0.1:  # Threshold
            alert(f"Data drift detected in {feature}: KL={kl_div}")

# 2. Monitor model performance
def monitor_model_performance():
    # A/B test: old model vs new model
    users_group_a = new_model.predict(features)  # 10% of traffic
    users_group_b = old_model.predict(features)  # 90% of traffic
    
    # Calculate acceptance rates
    acceptance_a = get_acceptance_rate(users_group_a)
    acceptance_b = get_acceptance_rate(users_group_b)
    
    if acceptance_a < acceptance_b - 0.05:  # >5% worse
        rollback_model()
        alert("Model performance degraded, rollback initiated")

# 3. Retrain trigger
def should_retrain_model():
    metrics = get_model_metrics(window_days=30)
    
    # Trigger retrain if:
    # - Accuracy drops >2%
    # - Data drift > threshold
    # - 30 days since last training
    # - New data available (>1000 samples)
    
    if (
        metrics['accuracy'] < model['baseline_accuracy'] - 0.02 or
        metrics['data_drift'] > 0.1 or
        days_since_training > 30 or
        new_samples_count > 1000
    ):
        trigger_retraining_pipeline()

# 4. Shadow model deployment
# Deploy new model as shadow (no user impact)
# Log predictions from both old and new models
# Compare metrics before cutover
```

---

## Interview Question 4: Rate Limiting & Throttling

**Q: Design a rate limiting system to prevent API abuse.**

### Answer

```python
# Token bucket algorithm (most flexible)
from dataclasses import dataclass
from time import time

@dataclass
class RateLimitConfig:
    requests_per_second: float  # 10.0
    burst_size: int  # 50
    
class TokenBucket:
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_size
        self.last_refill = time()
    
    def is_allowed(self):
        now = time()
        elapsed = now - self.last_refill
        
        # Refill tokens
        self.tokens = min(
            self.config.burst_size,
            self.tokens + elapsed * self.config.requests_per_second
        )
        self.last_refill = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

# Per-user rate limiting (Redis)
def rate_limit_check(user_id: str, limit_config: RateLimitConfig):
    key = f"rate_limit:{user_id}"
    
    # Get current tokens from Redis
    tokens = redis.get(key)
    
    if tokens is None:
        # New user, full bucket
        redis.setex(key, 3600, limit_config.burst_size - 1)
        return True
    
    tokens = int(tokens)
    if tokens > 0:
        redis.decr(key)
        return True
    
    return False

# Per-IP rate limiting (DDoS prevention)
def check_global_rate_limit(ip_address: str):
    key = f"global_limit:{ip_address}"
    count = redis.incr(key)
    redis.expire(key, 60)  # 1-minute window
    
    if count > 1000:  # 1000 requests/minute = 16.6/sec
        return False  # Block
    
    return True

# API endpoint with rate limiting
@router.get("/api/rides/search")
async def search_rides(
    request: Request,
    current_user = Depends(get_current_user)
):
    # Check both user and IP limits
    if not rate_limit_check(str(current_user.id), USER_LIMIT_CONFIG):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 10 requests/sec per user.",
            headers={"Retry-After": "60"}
        )
    
    if not check_global_rate_limit(request.client.host):
        raise HTTPException(status_code=429, detail="Service overloaded")
    
    # Process request...
```

---

## Question 5: Database Query Optimization

**Q: How would you optimize a slow query for finding nearby riders?**

### Answer

**Original Query (Slow)**:
```sql
SELECT r.*, u.name, u.trust_score
FROM rides r
JOIN users u ON r.user_id = u.id
WHERE r.status = 'active'
AND SQRT(
    POW(r.source_lat - 29.8757, 2) +
    POW(r.source_lng - 77.8974, 2)
) < 0.05  -- ~5km radius using Pythagorean distance
AND r.departure_datetime > NOW()
ORDER BY r.departure_datetime ASC
LIMIT 100;
```

**Problems**:
- Pythagorean distance wrong for geographic coordinates
- No index on calculated column
- Full table scan without spatial index

**Optimization**:

```sql
-- 1. Add PostGIS index
CREATE INDEX idx_rides_source_geom 
ON rides USING GIST(ST_GeogFromText(
    'POINT(' || source_lng || ' ' || source_lat || ')'
));

-- 2. Use optimized query with PostGIS
SELECT r.id, r.source_address, r.destination_address, 
       r.departure_datetime, u.name, u.trust_score,
       ST_Distance(
           ST_GeogFromText('POINT(77.8974 29.8757)'),
           ST_GeogFromText('POINT(' || r.source_lng || ' ' || r.source_lat || ')')
       ) as distance_m
FROM rides r
JOIN users u ON r.user_id = u.id
WHERE r.status = 'active'
AND ST_DWithin(
    ST_GeogFromText('POINT(' || r.source_lng || ' ' || r.source_lat || ')'),
    ST_GeogFromText('POINT(77.8974 29.8757)'),
    5000  -- 5km in meters
)
AND r.departure_datetime BETWEEN NOW() AND NOW() + INTERVAL '2 hours'
AND r.user_id != ?  -- Don't show own rides
ORDER BY r.departure_datetime ASC, distance_m ASC
LIMIT 100;

-- 3. Add composite index
CREATE INDEX idx_rides_active_time 
ON rides(status, departure_datetime) 
WHERE status = 'active';

-- 4. Partition table by date
CREATE TABLE rides_2024_q1 PARTITION OF rides
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

-- 5. Use connection pooling + caching
# Python with SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True  # Verify connections
)
```

**Performance Comparison**:
```
Before optimization: 2.5 seconds
After optimization: 45ms

Bottleneck breakdown:
- Index scan: 5ms
- Post-filter: 35ms
- Join: 5ms
```

---

## Tips for Interview Success

1. **Start broad, drill down**: Don't jump to implementation
2. **State assumptions**: "Assuming we start with 10K users..."
3. **Think out loud**: Show your reasoning process
4. **Ask clarifying questions**: "Is availability or consistency more important?"
5. **Use framework**: DARE (Define, Architecture, Refine, Explain)
6. **Draw diagrams**: ASCII art or hand-draw during video call
7. **Discuss trade-offs**: No perfect solution, only trade-offs
8. **Know your project**: Be able to explain your Carpool system deeply
9. **Prepare metrics**: Have numbers ready (latency, throughput, etc.)
10. **Practice online**: Use SystemsExpert or Educative

---

## Practice Questions to Prepare

- How would you implement a real-time notification system?
- Design a surge pricing algorithm
- How would you handle payment processing?
- Design a driver routing optimization system
- How would you ensure data privacy (GDPR compliance)?
- Design a referral/loyalty program system
- How would you implement search and filtering?

---

## Resources

- **Books**: Designing Data-Intensive Applications (Kleppmann)
- **Videos**: System Design Interview on Educative
- **Blogs**: ByteByteGo blog, High Scalability blog
- **Practice**: LeetCode Medium questions, SystemsExpert

