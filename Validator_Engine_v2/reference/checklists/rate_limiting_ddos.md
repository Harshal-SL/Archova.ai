---
tags: [rate-limiting, token-bucket, throttling, ddos, waf, security]
title: Rate Limiting, Throttling, and DDoS Mitigation
---

# Rate Limiting & Abuse Defense Checklist

1. **Multi-Tier Limiting**:
   - Edge WAF rate limiting: e.g. 2,000 requests per 5 minutes per IP.
   - Application rate limiting: e.g. Token Bucket backed by Redis for authenticated users (120 req/min).
   - Strict auth endpoint limiting: e.g. 5 attempts per minute per IP for `/login` and password resets.
2. **Standard Headers**:
   - Return standard headers: `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset`, `Retry-After`.
3. **Response on Breach**:
   - HTTP 429 Too Many Requests with informative RFC 7807 problem detail payload.
4. **Graceful Bursting**:
   - Token bucket or sliding window algorithm with controlled burst capacity.
