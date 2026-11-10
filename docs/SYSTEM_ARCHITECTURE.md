# ResilienceLab â€” System Architecture

## 1. Architecture Overview

ResilienceLab follows a client-server architecture with Docker-based server node isolation.

The browser dashboard communicates with a FastAPI backend through REST API endpoints. The backend manages simulated application services, monitors independent Docker-based server nodes, performs health checks, routes requests, and coordinates automatic recovery.

Docker SDK for Python enables the backend to interact with Docker containers, while HTTP health endpoints allow it to verify the operational status of individual nodes.

SQLite provides persistent storage for application states and system events.

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
        +-----------+------------+
        |           |            |
        v           v            v
   Service       Node        Load Balancer
   Manager       Monitor     (Round Robin)
        |           |            |
        |           v            |
        |      Docker SDK        |
        |           |            |
        |           v            |
        |     Docker Engine      |
        |           |            |
        |      +----+----+-------+
        |      |    |    |
        |      v    v    v
        |    Node  Node  Node
        |     1     2     3
        |      |    |    |
        |      +----+----+
        |           |
        |      HTTP Health
        |      & Processing
        |           |
        +-----------+
                    |
             +------+------+
             |             |
             v             v
         SQLite DB     System Metrics
       State & Logs       (psutil)
```

## 3. Main Components

### 3.1 Frontend â€” Browser Dashboard

The frontend is implemented using HTML, CSS, and JavaScript.

Responsibilities:

- Display system metrics.
- Show service and Docker node health.
- Trigger service and node failure actions.
- Trigger manual recovery operations.
- Send test requests to the load balancer.
- Display cluster health and traffic distribution.
- Retrieve and display system event logs.
- Refresh dashboard data periodically.

### 3.2 Backend â€” FastAPI

FastAPI handles application logic and exposes REST API endpoints.

Responsibilities:

- Manage simulated service states.
- Monitor Docker-based server nodes.
- Handle failure and recovery requests.
- Perform Docker container health checks.
- Execute round-robin request routing.
- Exclude unhealthy nodes from request distribution.
- Coordinate automatic recovery.
- Calculate cluster health.
- Retrieve system metrics.
- Read and write persistent application data.

Uvicorn runs the FastAPI application.

### 3.3 Service Manager

The service manager maintains the state of three simulated services:

- API Server
- Database
- Background Worker

It supports:

- Manual failure simulation.
- Manual recovery.
- Restart tracking.
- Automatic recovery after a configured interval.

These services are currently represented through application-level state rather than independent Docker containers.

### 3.4 Docker Node Manager

The node manager monitors three independent Docker containers:

- Node 1 â€” `resiliencelab-node-1`
- Node 2 â€” `resiliencelab-node-2`
- Node 3 â€” `resiliencelab-node-3`

Each node runs an independent FastAPI server inside its own Docker container.

The Docker SDK communicates with the Docker Engine to retrieve container information and manage container lifecycle operations.

The node manager tracks:

- Container health.
- HTTP health-check responses.
- Failure timestamps.
- Recovery status.
- Restart counts.
- Request counts.

### 3.5 Node Server

Each Docker node exposes two HTTP endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Return node health and runtime information |
| `/process` | GET | Process a request and return node information |

The main application uses these endpoints to verify node availability and forward processing requests.

### 3.6 Load Balancer

The load balancer uses a health-aware round-robin strategy.

Its responsibilities include:

- Check the health of candidate nodes.
- Select the next available healthy node.
- Forward requests to the selected node.
- Skip unhealthy nodes.
- Update request counts.
- Return HTTP 503 when no healthy node is available.

A failed node is excluded from request routing until it becomes healthy again.

### 3.7 Automatic Recovery Manager

The recovery manager runs as a background asynchronous task.

It periodically checks the status of simulated services and Docker-based nodes.

For Docker nodes, it:

1. Checks container status.
2. Calls the node's HTTP health endpoint.
3. Detects unhealthy or stopped containers.
4. Records the failure timestamp.
5. Waits for the configured recovery interval.
6. Attempts to restart the failed container.
7. Verifies recovery through subsequent health checks.
8. Updates node state and restart counters.
9. Records recovery events.

The current Docker node recovery interval is configured in the backend.

### 3.8 System Metrics

The psutil library collects metrics from the machine running ResilienceLab.

Metrics include:

- CPU utilization.
- Memory utilization.
- Disk utilization.
- System uptime.

These metrics describe the host environment, not individual Docker node resource utilization.

### 3.9 Database Layer

SQLite provides persistent storage.

The application uses two main tables:

**`logs`**

Stores system events such as:

- Service failures.
- Docker node failures.
- Successful request processing.
- Automatic recovery.
- Manual recovery.
- Request-processing errors.

**`system_state`**

Stores persisted component state, including:

- Component identifier.
- Component type.
- Health status.
- Restart count.
- Request count.
- Failure timestamp.

## 4. Request Flow

A typical request follows this sequence:

1. The dashboard sends a POST request to `/api/route`.
2. FastAPI acquires the routing lock.
3. The backend checks candidate Docker node health.
4. The round-robin algorithm selects an eligible node.
5. The backend forwards the request to the selected node's `/process` endpoint.
6. The node processes the request and returns a response.
7. The backend updates the persistent request count.
8. The routing event and state changes are stored in SQLite.
9. The response is returned to the dashboard.

If a node is unhealthy, the load balancer skips it and checks the next candidate.

If no healthy node can process the request, the API returns HTTP 503.

## 5. Failure Detection and Recovery Flow

### Failure Detection

1. A user triggers a Docker node failure through the dashboard or API.
2. The backend stops the selected Docker container.
3. The node becomes unavailable.
4. The monitoring task detects the stopped container or failed health check.
5. The failure timestamp is recorded.
6. A failure event is persisted in SQLite.

### Failure-Aware Routing

1. The load balancer checks node health.
2. Unhealthy nodes are excluded.
3. Requests are distributed across the remaining healthy nodes.
4. If all nodes are unavailable, the routing API returns HTTP 503.

### Automatic Recovery

1. The background recovery task identifies the failed node.
2. It waits for the configured recovery interval.
3. The Docker SDK retrieves the container.
4. If the container is stopped, the backend attempts to start it.
5. Subsequent health checks verify the node's availability.
6. The node state is updated to healthy after successful verification.
7. Restart information and recovery events are persisted.

## 6. Cluster Health Monitoring

The cluster health endpoint evaluates the health of all configured Docker nodes.

It reports:

- Total number of nodes.
- Number of healthy nodes.
- Number of failed nodes.
- Overall cluster status.

Cluster status is classified as:

| Condition | Cluster Status |
|---|---|
| All nodes healthy | Healthy |
| At least one node healthy, but not all | Degraded |
| No healthy nodes | Down |

## 7. Background Tasks and Concurrency

ResilienceLab uses asynchronous background processing for automatic recovery.

The routing endpoint uses an asynchronous lock to prevent simultaneous requests within the application process from racing the round-robin index.

Blocking Docker SDK and HTTP operations are executed through worker threads to avoid blocking the main asynchronous event loop.

The current implementation is designed for a single FastAPI application instance.

## 8. Container Architecture

The project uses separate container images for the main application and server nodes.

**Main application:**

- Built using `Dockerfile`.
- Runs the FastAPI backend.
- Exposes port 8000.
- Persists application data through a mounted directory.
- Uses the Docker socket to manage node containers.

**Server nodes:**

- Built using `Dockerfile.node`.
- Run independent FastAPI node servers.
- Expose port 9000 internally.
- Communicate through the Docker Compose network.

The three server nodes are currently created as separate Docker containers using Docker CLI commands.

The main application and node containers communicate through their shared Docker network.

## 9. Current Architecture Limitations

The current implementation is a local distributed systems experimentation platform, not a production-grade orchestration system.

- The monitoring backend runs as a single FastAPI application instance.
- Three server nodes run as independent Docker containers.
- Application-level service failure simulation is separate from actual Docker node failures.
- The load balancer operates at the application layer and is not a general-purpose external network load balancer.
- The Docker socket provides powerful host-level access and is intended for local development.
- SQLite is currently used for persistence.
- Large-scale distributed deployment and production workloads have not yet been validated.
- Advanced concurrency, fault-tolerance, and stress-testing scenarios remain areas for further improvement.

## 10. Planned Architecture Improvements

Future development may introduce:

- Prometheus-based metrics collection.
- Grafana observability dashboards.
- Latency and throughput measurements.
- Advanced load-balancing algorithms.
- Circuit breakers, retries, and timeout policies.
- Configurable fault injection.
- Stress testing and recovery-time analysis.
- PostgreSQL-based persistence.
- Distributed messaging through Kafka or RabbitMQ where appropriate.
- Advanced container orchestration experiments.
- Cloud deployment and multi-instance monitoring.

These are planned enhancements and are not part of the current implementation.
```
