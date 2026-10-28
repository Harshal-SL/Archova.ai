---
tags: [multi-az, ha, availability, redundancy, failover, topology]
title: Multi-AZ High Availability and Fault Tolerance
---

# Multi-AZ High Availability Checklist

1. **Redundant Topology**:
   - Deploy compute instances across minimum 3 Availability Zones with auto-scaling groups.
   - Front with Multi-AZ Application Load Balancers (ALB) performing active health checks.
2. **Database Redundancy**:
   - Primary-Standby Multi-AZ deployment with synchronous block-level replication.
   - Automated DNS failover under 30 seconds with minimal write disruption.
3. **Zone-Aware Routing**:
   - Enable cross-zone load balancing for uniform traffic distribution.
4. **Stateless Compute**:
   - No in-memory session persistence on container nodes; offload sessions to distributed cache.
5. **Circuit Breakers & Graceful Degradation**:
   - Wrap inter-service network calls in circuit breakers (e.g. Resilience4j / Tenacity) with fallbacks.
