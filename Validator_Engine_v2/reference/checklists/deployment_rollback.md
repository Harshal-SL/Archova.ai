---
tags: [deployment, rollback, blue-green, canary, ci_cd, zero-downtime]
title: Zero-Downtime Deployment and Automated Rollback
---

# Deployment & Rollback Checklist

1. **Deployment Strategy**:
   - Zero-downtime Blue-Green or Canary deployment with automated health verification.
2. **Backward Compatible Migrations**:
   - Database migrations must follow Expand/Contract pattern: never drop columns or rename columns in the same release as code deployment.
3. **Automated Rollback Criteria**:
   - Automatic rollback triggered if HTTP 5xx error rate exceeds 1% or healthcheck fails within 5 minutes of deployment.
4. **Immutable Artifacts**:
   - Build container image once in CI; promote unchanged image tag through staging to production.
5. **Configuration Decoupling**:
   - Runtime configuration supplied via environment variables / AWS SSM Parameter Store, not baked into container images.
