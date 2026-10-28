---
tags: [observability, metrics, tracing, logging, slo, sli, health]
title: Comprehensive Observability and Telemetry
---

# Observability Checklist

1. **Three Pillars of Observability**:
   - Structured JSON logs with context keys (`trace_id`, `span_id`, `user_id`, `service`).
   - Prometheus / OpenTelemetry RED metrics: Rate, Errors, Duration.
   - Distributed tracing across HTTP and asynchronous message queues via W3C TraceContext.
2. **SLI / SLO Definitions**:
   - Explicit latency targets: e.g. 99% of requests < 200ms over 30 days.
   - Availability targets: 99.9% success rate excluding client 4xx errors.
3. **Health and Readiness Probes**:
   - Separate `/live` (liveness probe - server is up) and `/ready` (readiness probe - DB and cache connected).
4. **Actionable Alerting Rules**:
   - Alert on symptoms (high error rate, exhausted connection pool, high queue lag) rather than individual host CPU spikes.
