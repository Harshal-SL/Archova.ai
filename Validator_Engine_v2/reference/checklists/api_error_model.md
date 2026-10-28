---
tags: [error-model, rfc7807, problem-details, error_handling, api]
title: Standardized API Error Model and Problem Details
---

# API Error Handling Checklist

1. **RFC 7807 / RFC 9457 Compliance**:
   - Error responses must follow Problem Details JSON format: `type`, `title`, `status`, `detail`, `instance`.
2. **Deterministic Status Codes**:
   - `400` Validation failure, `401` Missing/invalid authentication, `403` Insufficient permissions, `404` Not found, `409` Conflict / concurrency collision, `422` Unprocessable entity, `429` Rate limit exceeded, `500` Internal server error.
3. **Structured Validation Errors**:
   - Validation failures must return field-level diagnostics array: `errors: [{field, code, message}]`.
4. **Information Leakage Prevention**:
   - Internal stack traces, raw SQL queries, or infrastructure names must never leak to API clients in production.
5. **Correlation ID Tracking**:
   - Every error response must include a unique `request_id` or `trace_id` for observability triage.
