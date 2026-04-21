layer: deployment
topic: topology

Deploy as containerized services behind a reverse proxy.
Suggested topology:
- API service replicas behind load balancer
- background worker for async jobs
- PostgreSQL managed instance
- Redis managed cache

Operational requirements:
- liveness and readiness probes
- rolling deployment with canary percentage
- centralized logs and metrics dashboards
