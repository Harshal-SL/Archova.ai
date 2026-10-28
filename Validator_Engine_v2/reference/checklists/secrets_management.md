---
tags: [secrets, vault, kms, encryption, keys, compliance]
title: Secrets Management and Key Rotation
---

# Secrets Management Checklist

1. **Zero Hardcoded Secrets**:
   - Zero API keys, database passwords, or private certificates committed in Git repository or hardcoded in source.
2. **Centralized Secret Stores**:
   - Use dedicated secrets managers: AWS Secrets Manager, HashiCorp Vault, or Azure Key Vault.
3. **Automated Secret Rotation**:
   - Database credentials and API keys rotated automatically every 90 days.
4. **Envelope Encryption**:
   - Master key in KMS protects Data Encryption Keys (DEKs) used for at-rest storage encryption.
5. **Least-Privilege Secret Access**:
   - IAM roles grant access only to the specific secrets required by each workload.
