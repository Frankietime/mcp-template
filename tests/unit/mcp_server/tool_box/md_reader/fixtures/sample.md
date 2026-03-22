# Software Architecture Guide

This document covers core topics in modern software design and system architecture.

## Authentication

Authentication is the process of verifying user identity before granting access.
Common authentication methods include OAuth2, JWT tokens, and API keys.

### OAuth2

OAuth2 provides token-based authentication for APIs and third-party integrations.

### JWT

JWT (JSON Web Tokens) are stateless authentication tokens used widely in microservices.
Multi-factor authentication adds an extra layer of security beyond passwords.

## Database Design

Database design involves choosing between relational and non-relational stores.
Indexes improve query performance significantly by reducing full-table scans.
Normalization reduces data redundancy in relational databases.
Connection pooling helps manage database connections efficiently under load.
Schema migrations must be applied carefully to avoid downtime in production.

## Caching

Caching improves application performance by storing frequently accessed data in memory.
Redis is a popular in-memory caching solution supporting strings, hashes, and sorted sets.
Cache invalidation is one of the hardest problems in computer science.
TTL (Time To Live) controls how long cached data remains valid before expiry.
Write-through and write-behind are two common cache update strategies.

## Deployment

Deployment pipelines automate the release process from code to production.
Docker containers package applications with their dependencies for consistency.
Kubernetes orchestrates containerized workloads at scale across clusters.
Blue-green deployment minimizes downtime during releases by running two environments.
Canary releases gradually roll out changes to a subset of users before full rollout.

## Monitoring

Monitoring tracks system health and application performance in real time.
Metrics, logs, and traces form the three pillars of observability.
Alerting notifies on-call teams when systems exceed defined thresholds.
Distributed tracing follows requests across multiple services in a microservices system.
SLOs (Service Level Objectives) define the reliability targets for each service.
