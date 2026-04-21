layer: database
topic: performance

Performance guidelines:
- use connection pooling with bounded pool size
- separate read-heavy endpoints with replicas when needed
- cache expensive aggregates in Redis with short TTL

Consistency patterns:
- transactional writes for task and task_events
- outbox table for reliable integration event publishing

Shared terms: backend service repository pattern, deployment health checks.
