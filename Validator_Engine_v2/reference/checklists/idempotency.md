---
tags: [idempotency, deduplication, retry, transactions, payments]
title: API Idempotency and Request Deduplication
---

# Idempotency Design Checklist

1. **Header-Based Keys**:
   - Mutating operations (POST / PUT) must accept `Idempotency-Key` headers (UUIDv4).
2. **Atomic Storage**:
   - Store idempotency keys with request fingerprints (hash of method + path + body).
   - Use atomic `SET key status EX 86400 NX` or unique database constraints.
3. **Execution State Transition**:
   - Statuses: `IN_PROGRESS`, `SUCCESS`, `FAILED`.
   - Reject concurrent duplicate requests with HTTP 409 or wait with short polling.
4. **Cached Response Replay**:
   - On matching completed key, return cached HTTP status code and response body without re-execution.
5. **Transactional Scope**:
   - Ensure external side effects (e.g. payment gateway charge, email notification) are guarded by the idempotency key.
