---
tags: [stride, threat-model, spoofing, tampering, repudiation, elevation]
title: STRIDE Threat Modeling and Countermeasure Mapping
---

# STRIDE Threat Modeling Checklist

1. **Spoofing**:
   - Countermeasures: Mutual TLS for inter-service, OpenID Connect / JWT with strict audience checking for clients.
2. **Tampering**:
   - Countermeasures: TLS 1.3 in-transit, HMAC-SHA256 payload integrity signatures, read-only container root filesystems.
3. **Repudiation**:
   - Countermeasures: Append-only write-once audit log stream with cryptographic signing.
4. **Information Disclosure**:
   - Countermeasures: Column-level encryption for sensitive PII, zero credentials in client bundles, strict CORS and security headers.
5. **Denial of Service (DoS)**:
   - Countermeasures: Tiered rate limiters, AWS WAF, request body size limits, database query timeouts.
6. **Elevation of Privilege**:
   - Countermeasures: Non-root container users, parameterized IAM roles with permission boundaries.
