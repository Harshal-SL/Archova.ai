layer: integration
topic: events

Integration style:
- publish task lifecycle events using event bus
- support inbound webhooks from partner systems
- validate webhook signature and replay protection

Contract patterns:
- version event schema using schema_version field
- use outbox pattern with PostgreSQL for reliable publish
- dead-letter queue for failed event processing
