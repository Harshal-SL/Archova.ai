layer: backend
topic: services

Backend is organized as modular services:
- auth service for token issue and refresh
- task service for create, update, and assignment operations
- reporting service for summary analytics

Apply layered architecture: router -> service -> repository.
Use Redis for hot cache of dashboard counters.
Publish domain events on task updates for integration consumers.
