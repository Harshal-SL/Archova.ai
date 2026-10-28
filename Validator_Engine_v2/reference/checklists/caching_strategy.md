---
tags: [caching, redis, cache-invalidation, performance, latency]
title: Caching Strategy and Invalidation
---

# Caching & Invalidation Checklist

1. **Topology & Sizing**:
   - Specify distributed cache cluster (e.g. AWS ElastiCache Redis Cluster / KeyDB) with read replicas.
2. **Cache Pattern**:
   - Cache-Aside for read-heavy entities; Write-Through or Event-Driven Invalidation for frequently updated records.
3. **Invalidation Invariants**:
   - Avoid unbounded TTLs; every key must possess an explicit TTL (e.g. 300s to 3600s).
   - Invalidate on entity update/delete via transactional outbox or CDC events.
4. **Stampede & Penetration Defense**:
   - Mutex locks on cache misses or probabilistic early expiration (XFetch) to prevent thundering herds.
   - Cache negative results (null markers) with short TTL (e.g., 30s) to prevent DB penetration on non-existent keys.
