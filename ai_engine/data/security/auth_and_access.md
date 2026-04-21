layer: security
topic: authz

Security baseline:
- JWT access token validation at API gateway or app middleware
- role-based access control for admin and member actions
- secure password policy and optional MFA for admins

Session and secrets:
- rotate signing keys regularly
- store secrets in runtime secret manager
- monitor invalid token spikes as security alerts
