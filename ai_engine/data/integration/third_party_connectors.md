layer: integration
topic: connectors

Third-party connectors:
- email provider for notification dispatch
- analytics sink for usage metrics
- optional identity provider for SSO

Connector reliability:
- timeout and retry policy per provider
- idempotency key on outbound calls
- capture provider response metadata for debugging

Shared terms: JWT, Redis, deployment observability.
