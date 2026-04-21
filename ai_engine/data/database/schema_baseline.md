layer: database
topic: schema

Primary store is PostgreSQL.
Core tables:
- users(id, email, role, created_at)
- tasks(id, title, status, assignee_id, due_date, updated_at)
- task_events(id, task_id, event_type, payload, created_at)

Indexes:
- tasks(status, due_date)
- tasks(assignee_id, status)
- task_events(task_id, created_at)

Use soft deletes where audit requirements apply.
