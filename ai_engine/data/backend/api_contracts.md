layer: backend
topic: api

Expose REST endpoints:
- POST /api/tasks
- GET /api/tasks/{id}
- PATCH /api/tasks/{id}/status
- GET /api/reports/summary

Security and reliability:
- verify JWT on protected routes
- enforce request id and idempotency key for writes
- return problem+json style error payloads

Shared terms: PostgreSQL transactions, integration event outbox.
