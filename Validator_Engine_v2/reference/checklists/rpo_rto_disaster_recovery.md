---
tags: [rpo, rto, backup, disaster-recovery, restore, business-continuity]
title: Recovery Point Objective (RPO) and Recovery Time Objective (RTO)
---

# RPO / RTO & Disaster Recovery Checklist

1. **Target Definitions**:
   - Explicitly define metrics: e.g. RPO <= 5 minutes (data loss ceiling) and RTO <= 30 minutes (restore duration).
2. **Automated Snapshot Cadence**:
   - Continuous WAL archiving to durable object store (S3 Multi-AZ).
   - Daily automated full snapshots with 30-day retention and point-in-time recovery (PITR).
3. **Cross-Region Replication**:
   - Replicate primary database and storage backups asynchronously to a secondary disaster recovery region.
4. **Restore Drills**:
   - Documented automated restore playbook verified on a regular drill cadence.
5. **Cold vs Warm Standby**:
   - State clearly whether DR topology is active-passive, warm standby, or pilot light.
