layer: deployment
topic: observability

Observability standards:
- correlation id propagated from frontend to backend
- structured JSON logs with request id and tenant id
- latency/error dashboards and alert thresholds

Reliability controls:
- retry with backoff for transient integration failures
- circuit breaker on unstable downstream dependencies
- daily backup verification for PostgreSQL
