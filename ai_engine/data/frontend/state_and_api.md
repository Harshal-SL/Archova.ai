layer: frontend
topic: state-management

State strategy:
- global store for user session and feature flags
- query cache for API responses with stale-while-revalidate

API handling:
- call backend REST APIs through a typed client
- include correlation-id header for tracing
- show graceful fallbacks for timeout and 5xx errors

Shared terms: Redis cache invalidation events, JWT session lifecycle.
