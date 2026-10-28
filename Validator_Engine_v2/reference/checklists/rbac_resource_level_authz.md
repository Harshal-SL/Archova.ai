---
tags: [rbac, abac, authorization, resource-level, authn_authz, security]
title: Role-Based and Resource-Level Authorization
---

# RBAC and Resource-Level Authorization Checklist

1. **Least Privilege Principles**:
   - Roles must follow principle of least privilege (Admin, Operator, User, Guest).
2. **Resource-Level Ownership Verification**:
   - Never authorize requests solely on role existence; verify resource tenancy:
     e.g., `WHERE id = :resource_id AND tenant_id = :current_user_tenant`.
   - Prevent Insecure Direct Object References (IDOR).
3. **Token Scoping & Claims**:
   - JWT tokens signed with RS256/EdDSA, containing subject `sub`, expiration `exp`, tenant `tid`, and permissions `scope`.
   - Refresh token rotation with family revocation on reuse.
4. **Endpoint Guarding**:
   - Every mutating and sensitive API endpoint must explicitly declare authorization policies.
5. **Audit Trails**:
   - Log all authorization rejections (HTTP 403) with actor, resource, and timestamp into tamper-evident log stream.
