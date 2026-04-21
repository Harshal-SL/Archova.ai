layer: frontend
topic: architecture

Use a component-based SPA architecture with route-level code splitting.
Frontend modules:
- auth module for login and token refresh
- dashboard module for analytics cards and activity stream
- settings module for profile and notification controls

Use JWT access token in memory and refresh token via secure cookie strategy.
Use optimistic UI updates for task status changes.
