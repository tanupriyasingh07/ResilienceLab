# Project Overview

## 1. Introduction

ResilienceLab is a locally runnable project that demonstrates core reliability concepts used in distributed systems. It provides a controlled environment to simulate service and node failures, observe component health, test automatic recovery, and understand how requests can be distributed across available nodes.

The project combines a Python backend, a browser-based dashboard, and SQLite event storage.

## 2. Problem Statement

Applications that depend on multiple services and servers must handle component failures without losing visibility into system health.

Developers need ways to understand:

- What happens when a service becomes unavailable?
- How can a system identify failed components?
- How should requests be handled when a node is unhealthy?
- How can recovery events be tracked?
- How can system health be presented clearly?

ResilienceLab explores these questions through a small, interactive simulation.

## 3. Project Objectives

1. Demonstrate service and node failure scenarios.
2. Implement basic health-state tracking.
3. Simulate automatic recovery after a configured interval.
4. Distribute requests across healthy nodes using round-robin routing.
5. Prevent failed nodes from receiving routed requests.
6. Store important system events in SQLite.
7. Present health information through a live dashboard.
8. Provide REST API endpoints for interacting with the simulation.

## 4. Intended Users

The current version is intended for:

- Computer science students learning distributed systems.
- Developers exploring failure handling and recovery concepts.
- Learners practising backend development and REST APIs.
- Technical interview candidates demonstrating system reliability concepts.

A future expanded version could be useful as a learning and testing environment for development teams.

## 5. Core Components

### Service Monitoring

The application maintains three simulated services:

- API Server
- Database
- Worker

Their health states can be viewed and changed through the dashboard or API.

### Node Monitoring

The simulation contains three nodes. Each node has a health state, failure timestamp, and request counter.

### Failure and Recovery

Users can manually trigger failures. The application records the failure time and automatically restores simulated components after the configured recovery interval.

### Load Balancing

A round-robin strategy distributes incoming test requests among healthy nodes. Failed nodes are excluded from routing.

### System Monitoring

The dashboard displays CPU usage, memory usage, disk usage, and uptime for the machine running the application.

### Event Logging

SQLite stores system events, including failures, recoveries, and routing activity.

## 6. Technology Choices

| Technology | Purpose |
|---|---|
| Python | Application logic |
| FastAPI | Backend and REST API |
| HTML | Dashboard structure |
| CSS | Dashboard styling |
| JavaScript | Dashboard interactions and live updates |
| SQLite | Persistent event and state storage |
| psutil | Local system metrics |
| Uvicorn | Application server |

## 7. Current Project Scope

The current implementation is a single-process local simulation.

The services and nodes are represented inside the application rather than running as independent machines or containers. The routing logic demonstrates request distribution but does not provide production network load balancing.

This distinction is important when evaluating the current capabilities.

## 8. Expected Learning Outcomes

The project provides practical experience with:

- Backend application design.
- REST API development.
- Health-state management.
- Failure detection concepts.
- Recovery workflows.
- Round-robin scheduling.
- Persistent event logging.
- System resource monitoring.
- Dashboard development.
- Testing failure scenarios.

## 9. Future Direction

The project can evolve toward a more realistic reliability-testing platform through independent service processes, container-based environments, configurable health checks, additional routing algorithms, historical metrics, alerting, and remote deployment.

These capabilities belong to the future development plan and are not part of the current implementation.