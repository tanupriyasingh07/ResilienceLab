# ResilienceLab — System Architecture

## 1. Architecture Overview

ResilienceLab follows a lightweight client-server architecture.

The browser-based dashboard communicates with a FastAPI backend through REST API endpoints. The backend manages simulated services, simulated cluster nodes, request routing, system metrics, and event persistence.

SQLite stores application state and system event records.

## 2. High-Level Architecture

```text
             USER
              |
              v
      Browser Dashboard
       HTML / CSS / JS
              |
          REST API
              |
              v
       FastAPI Backend
              |
     +--------+---------+
     |        |         |
     v        v         v
  Service   Node     Load Balancer
 Manager   Manager    (Round Robin)
     |        |         |
     +--------+---------+
              |
       +------+------+
       |             |
       v             v
   SQLite DB     System Metrics
   State & Logs     (psutil)
```

## 3. Main Components

### 3.1 Frontend — Browser Dashboard

The frontend is implemented using HTML, CSS, and JavaScript.

Responsibilities:
- Display system metrics.
- Show service and node health.
- Trigger failure and recovery actions.
- Send test requests to the load balancer.
- Display cluster health and traffic distribution.
- Retrieve and display system event logs.
- Refresh dashboard data periodically.

### 3.2 Backend — FastAPI

FastAPI handles application logic and exposes REST API endpoints.

Responsibilities:
- Manage service states.
- Manage simulated node states.
- Handle failure and recovery requests.
- Execute round-robin request routing.
- Calculate cluster health.
- Retrieve system metrics.
- Read and write persistent application data.

Uvicorn runs the FastAPI application.

### 3.3 Service Manager

The service manager maintains the state of three simulated services:

- API Server
- Database
- Background Worker

It supports manual failure, recovery, restart tracking, and automatic recovery.

### 3.4 Node Manager

The node manager manages three simulated cluster nodes.

It tracks:
- Node health.
- Failure timestamps.
- Recovery status.
- Request counts.

Failed nodes are excluded from request routing.

### 3.5 Load Balancer

The load balancer uses a round-robin strategy.

It selects the next healthy node for each request. Failed nodes are skipped.

If no healthy node is available, the routing endpoint returns an HTTP 503 response.

### 3.6 System Metrics

The psutil library collects metrics from the machine running ResilienceLab.

Metrics include:
- CPU utilization.
- Memory utilization.
- Disk utilization.
- System uptime.

### 3.7 Database Layer

SQLite provides persistent storage.

The application uses two main tables:

- `logs`: stores system events such as failures, recoveries, and request routing.
- `system_state`: stores persisted component state.

## 4. Request Flow

A typical dashboard interaction follows this sequence:

1. The user performs an action on the dashboard.
2. JavaScript sends an HTTP request to a FastAPI endpoint.
3. FastAPI processes the request.
4. The relevant service, node, or routing logic updates its state.
5. Relevant events and state changes are persisted in SQLite.
6. The backend returns a response.
7. The dashboard updates the displayed information.

## 5. Failure and Recovery Flow

1. A user triggers a failure for a simulated service or node.
2. The backend marks the component as failed.
3. The failure timestamp is recorded.
4. The event is stored in SQLite.
5. The recovery checker periodically checks failed components.
6. Once the configured recovery interval has elapsed, the component is restored.
7. The restart count is updated where applicable.
8. A recovery event is recorded.
9. The dashboard displays the updated status.

## 6. Load-Balancing Flow

1. The dashboard sends a test request.
2. The backend identifies healthy nodes.
3. The round-robin selection logic chooses the next eligible node.
4. The selected node's request count is incremented.
5. The routing event is recorded.
6. The selected node information is returned to the dashboard.

## 7. Background Tasks

The application uses periodic background checks to inspect failed services and nodes.

The recovery checker runs at a configured interval and restores components when their recovery time has elapsed.

## 8. Current Architecture Limitations

The current version is a local simulation.

- Services and nodes are represented within one FastAPI application.
- Nodes are not independent physical or virtual servers.
- Request routing demonstrates application-level selection, not real network traffic distribution.
- Recovery changes simulated component state rather than restarting external processes.
- SQLite is used for local persistence.

## 9. Planned Architecture Improvements

Future versions may introduce:

- Independent service processes.
- Docker containers for service isolation.
- Real health-check endpoints.
- Configurable recovery policies.
- Additional load-balancing strategies.
- Prometheus metrics integration.
- Cloud deployment and multi-user access.

These improvements are planned and are not implemented in the current version.