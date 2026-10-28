---
tags: [db-integrity, isolation, serializable, constraints, acid, schema]
title: Database Integrity, Constraints, and Transaction Isolation
---

# Database Integrity & Isolation Checklist

1. **Foreign Key Integrity**:
   - Enforce explicit `ON DELETE RESTRICT` or `CASCADE` foreign key constraints across relational boundaries.
2. **Transaction Isolation Levels**:
   - Explicitly specify isolation levels: `READ COMMITTED` default, `REPEATABLE READ` or `SERIALIZABLE` for financial/inventory balancing.
3. **Optimistic Locking Columns**:
   - Entities subject to concurrent edits must include an integer `version` or timestamp column.
4. **Index Coverage for Query Patterns**:
   - Foreign key columns, lookup keys, and composite filter keys must have corresponding B-Tree indices.
5. **Data Purge and Retention Policy**:
   - Explicit archival or hard-delete schedule documented for transactional history to prevent unbounded table growth.
