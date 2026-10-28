---
tags: [concurrency, locking, double-booking, race-condition, inventory]
title: Concurrency Control and Double-Booking Prevention
---

# Concurrency & Mutual Exclusion Checklist

1. **State Reservation Window**:
   - Use atomic hold transitions with finite TTLs (e.g., 5-10 minutes) for reservations.
   - Prevent simultaneous acquisition using row-level pessimistic locks (`SELECT FOR UPDATE NOWAIT`) or distributed locks (Redis Redlock).
2. **Optimistic Versioning**:
   - Include version numbers on aggregate roots where contention is moderate.
   - Fail or retry when `UPDATE table SET version = version + 1 WHERE id = :id AND version = :expected_version` returns 0 rows.
3. **Pessimistic Order Locking**:
   - If multiple resources must be acquired together, always sort IDs ascending to avoid deadlocks.
4. **Idempotent Checkout**:
   - Couple hold tokens to an idempotency key before finalizing payments or transfers.
5. **Background Release Worker**:
   - An asynchronous sweeper or TTL expiry must release abandoned or unpaid locks automatically.
