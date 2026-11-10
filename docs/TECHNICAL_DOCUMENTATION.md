# Technical Documentation

## 1. Introduction

This document explains the internal implementation of ResilienceLab, including its application structure, service and node state management, failure simulation, recovery logic, routing algorithm, monitoring, and database operations.

## 2. Application Entry Point

**File:** `app/main.py`

The FastAPI application acts as the central entry point. It handles HTTP requests, maintains simulation state, coordinates background recovery checks, and communicates with SQLite.

The application is started using:

```bash
uvicorn app.main:app --reload
```

The `--reload` option enables automatic application reloading during local development.

## 3. Service State Management

ResilienceLab maintains three simulated services:

| Service ID | Description |
|---|---|
| `api-server` | Represents an application API service |
| `database` | Represents a database service |
| `worker` | Represents a background processing service |

Each service has a health state. The application supports manual failure and recovery operations.

When a service fails, its state changes to failed and its failure timestamp is recorded.

## 4. Node State Management

The simulation maintains three nodes:

- `node-1`
- `node-2`
- `node-3`

Node information includes:

- Node identifier.
- Current health status.
- Failure timestamp.
- Restart count.
- Request count.

The node state determines whether the load balancer can select that node.

## 5. Failure Simulation

Failure simulation allows users to manually mark a service or node as unavailable.

The failure workflow is:

1. Receive a failure request.
2. Validate the requested component.
3. Update its health state.
4. Record the failure timestamp.
5. Persist the updated state.
6. Add an event to the log.

This creates a controlled failure scenario without stopping an actual server or service.

## 6. Automatic Recovery

The application runs periodic background checks to identify components that have remained failed beyond the configured recovery interval.

Current configuration:

| Parameter | Value |
|---|---:|
| Recovery interval | 10 seconds |
| Recovery checker interval | 2 seconds |

When the recovery condition is met:

1. The component is marked healthy.
2. Its failure timestamp is cleared.
3. The restart count is incremented for nodes.
4. The updated state is persisted.
5. A recovery event is recorded.

The recovery mechanism is part of the simulation and does not restart external processes.

## 7. Round-Robin Load Balancing

The routing endpoint distributes requests across available nodes using round-robin scheduling.

For example, with all three nodes healthy, the expected sequence is:

```text
Request 1 → node-1
Request 2 → node-2
Request 3 → node-3
Request 4 → node-1
Request 5 → node-2
Request 6 → node-3
```

### Failure-aware routing

Before selecting a node, the application considers only healthy nodes.

For example, if `node-2` is failed:

```text
Request 1 → node-1
Request 2 → node-3
Request 3 → node-1
Request 4 → node-3
```

If no healthy node is available, the routing endpoint returns HTTP 503.

## 8. Cluster Health Calculation

The cluster health endpoint evaluates the current node states.

It reports the number of healthy and failed nodes and an overall cluster status.

The current status interpretation is:

- **Healthy:** All nodes are healthy.
- **Degraded:** Some nodes have failed, but at least one remains healthy.
- **Unavailable:** No healthy nodes remain.

## 9. System Metrics

The application uses the `psutil` Python library to retrieve local machine metrics.

| Metric | Description |
|---|---|
| CPU | Current CPU utilization |
| Memory | System memory utilization |
| Disk | Disk usage |
| Uptime | Time since system boot |

These metrics are collected from the computer running the application.

## 10. Database Design

**Database:** SQLite  
**Location:** `data/resilience.db`

The application uses two main tables:

### 10.1 logs

Stores important system events.

Typical information includes:

- Event identifier.
- Event description or message.
- Event timestamp.

Events include failures, recoveries, and routing activity.

### 10.2 system_state

Stores relevant service and node state information so that the simulation can restore saved state when the application starts.

The stored failure timestamp supports the automatic recovery mechanism after a restart.

## 11. Dashboard Implementation

**File:** `static/index.html`

The dashboard is implemented using HTML, CSS, and JavaScript.

It provides:

- System overview.
- Service health cards.
- Cluster health.
- Node status and controls.
- Traffic distribution.
- System event logs.

The browser periodically calls the backend APIs and updates the displayed information.

The current refresh interval is approximately three seconds.

## 12. Dependencies

The project currently uses:

| Package | Purpose |
|---|---|
| FastAPI | REST API framework |
| Uvicorn | ASGI application server |
| psutil | System metrics |

Install dependencies with:

```bash
pip install -r requirements.txt
```

## 13. Error Handling

The API validates requested service and node identifiers.

Unknown identifiers should return an appropriate HTTP error rather than changing an unrelated component.

The routing endpoint returns HTTP 503 when no healthy node is available.

## 14. Current Technical Boundaries

- State management is designed for one application process.
- Simulated nodes do not represent independent machines.
- The current routing mechanism is not a production load balancer.
- Recovery is a state transition, not an infrastructure restart.
- SQLite is intended for the current local implementation.
- Monitoring covers the host machine rather than a remote cluster.

These limitations should be considered before using the project in a production environment.