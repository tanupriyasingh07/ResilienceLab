# ResilienceLab — Technical Documentation

## 1. Technical Overview

ResilienceLab is a Python-based self-healing distributed systems experimentation platform.

It uses FastAPI as the central coordinator and manages three independent Docker node containers. The application monitors node health, detects failures, performs recovery operations, routes requests across healthy nodes, and stores application state and event logs using SQLite.

The platform integrates Prometheus for application metrics collection and Grafana for monitoring visualization.

A browser-based dashboard provides visibility into application health, node status, cluster health, request distribution, and system events.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Backend programming language |
| FastAPI | REST API framework |
| Uvicorn | ASGI application server |
| Docker Engine | Container runtime |
| Docker SDK for Python | Container monitoring and management |
| Docker Compose | Application and monitoring stack |
| HTML | Dashboard structure |
| CSS | Dashboard styling |
| JavaScript | Dashboard interactions and API communication |
| SQLite | Persistent state and event storage |
| psutil | Host system metrics |
| prometheus-client | Application metrics instrumentation |
| Prometheus | Metrics collection and storage |
| Grafana | Monitoring visualization |
| HTTP | Communication between coordinator and nodes |

## 3. Application Structure

```text
ResilienceLab/
├── app/
│   ├── __init__.py
│   └── main.py
├── nodes/
│   └── node_server.py
├── static/
│   └── index.html
├── assets/
│   ├── architecture/
│   ├── demo/
│   └── screenshots/
├── monitoring/
│   └── prometheus/
│       └── prometheus.yml
├── docs/
├── data/
├── Dockerfile
├── Dockerfile.node
├── compose.yaml
├── requirements.txt
├── .dockerignore
├── .gitignore
├── LICENSE
└── README.md
```

The `data/` directory is used for runtime SQLite database storage. The local database file is excluded from Git.

The `venv/` directory contains the local Python virtual environment and should not be committed.

## 4. Backend Implementation

The main backend implementation is located in `app/main.py`.

It contains:

- FastAPI application initialization and lifecycle management.
- REST API route definitions.
- Simulated service state management.
- Docker node state management.
- Docker container operations.
- Node health checks.
- Failure injection and recovery operations.
- Round-robin request routing.
- Cluster health calculation.
- System metrics collection.
- SQLite database operations.
- Background recovery monitoring.
- Prometheus metrics instrumentation.

The application acts as the central coordinator for the Docker nodes.

## 5. Docker Node Architecture

The project uses three independent Docker containers:

| Node ID | Container Name | Internal Port |
|---|---|---|
| node-1 | resiliencelab-node-1 | 9000 |
| node-2 | resiliencelab-node-2 | 9000 |
| node-3 | resiliencelab-node-3 | 9000 |

Each node runs the FastAPI application defined in `nodes/node_server.py`.

### Node Endpoints

**GET `/health`**

Returns node health information, uptime, and request count.

**GET `/process`**

Processes a test request and increments the node's request counter.

The nodes communicate with the central application over a shared Docker network.

## 6. Service Management

The application maintains three simulated application services:

| Service ID | Display Name |
|---|---|
| api-server | API Server |
| database | Database |
| worker | Background Worker |

Each service maintains its health status, failure timestamp, and restart count.

Users can trigger service failures and request manual recovery through the dashboard or REST API.

The background recovery mechanism restores failed simulated services after the configured recovery interval.

These services are application-level simulations, not separate Docker containers.

## 7. Docker Node Management

The central application uses Docker SDK for Python to interact with the local Docker Engine.

Node management includes:

- Retrieving Docker container status.
- Checking node HTTP health endpoints.
- Stopping containers for failure injection.
- Starting containers during recovery.
- Tracking node request and restart counts.
- Updating node state and event logs.

Node health is determined using both Docker container status and HTTP health checks.

## 8. Load-Balancing Logic

ResilienceLab implements application-level round-robin request routing across healthy Docker nodes.

The routing process:

1. Acquires the routing lock.
2. Selects the next node using the round-robin position.
3. Checks node availability.
4. Skips unhealthy nodes.
5. Sends an HTTP request to the selected node's `/process` endpoint.
6. Updates request counters and records the event.

If no healthy nodes are available, the API returns HTTP 503 Service Unavailable.

The routing implementation demonstrates failure-aware request distribution rather than production-grade external load balancing.

## 9. Automatic Recovery

A background asynchronous task periodically monitors simulated services and Docker nodes.

The configured recovery delay for failed components is 60 seconds.

### Docker Node Recovery Workflow

1. The background task checks the node's actual health.
2. A failed node is marked as failed.
3. Its failure timestamp is recorded.
4. After the recovery delay, the application checks the Docker container.
5. If the container is stopped, the application attempts to start it.
6. The node health endpoint is checked again.
7. On successful health verification, the node is marked healthy and its restart count is updated.

Docker operations are executed using `asyncio.to_thread()` to avoid blocking the asynchronous application event loop.

Manual recovery is also available through the node recovery API.

## 10. Database Design

ResilienceLab uses SQLite for local persistence.

### logs

Stores recorded system events, including:

- Service failures and recoveries.
- Docker node failure detection.
- Automatic and manual recovery events.
- Request routing and failures.

### system_state

Stores persisted component state, including relevant status and counter information.

The database is stored at:

```text
data/resilience.db
```

The database directory is mounted into the application container so that data can persist across container rebuilds.

## 11. System Metrics

The application uses `psutil` to collect host-level system metrics.

Metrics include:

- CPU utilization.
- Memory utilization.
- Disk utilization.
- System uptime.

These values describe the machine running the ResilienceLab application, not individual Docker node resource consumption.

## 12. Prometheus Metrics Instrumentation

ResilienceLab integrates the Prometheus Python client library through `prometheus-client`.

The FastAPI application exposes a `/metrics` endpoint that provides metrics in Prometheus exposition format.

### Implemented Metrics

| Metric | Type | Description |
|---|---|---|
| `resiliencelab_http_requests_total` | Counter | Total HTTP requests grouped by method, endpoint, and status |
| `resiliencelab_http_request_duration_seconds` | Histogram | HTTP request duration observations |
| `resiliencelab_active_nodes` | Gauge | Number of healthy Docker nodes |
| `resiliencelab_total_nodes` | Gauge | Total configured Docker nodes |

### Request Instrumentation

HTTP middleware records:

- HTTP method.
- Endpoint path.
- Response status code.
- Request duration.

Requests to `/metrics` are excluded from the custom HTTP request counter and duration observations.

### Cluster Metrics

The cluster health endpoint updates the active-node and total-node gauges based on the current node health information.

**Current implementation limitation:** These gauges are refreshed when `/api/cluster-health` is requested. A periodic background refresh mechanism is a potential improvement.

## 13. Prometheus Configuration

Prometheus runs as an independent Docker container and scrapes the FastAPI application's metrics endpoint.

Configuration file:

```text
monitoring/prometheus/prometheus.yml
```

Current configuration:

```yaml
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: "resiliencelab"
    metrics_path: "/metrics"
    static_configs:
      - targets: ["resiliencelab:8000"]
```

The target uses the Docker Compose service name `resiliencelab` for internal container-to-container communication.

Prometheus is exposed locally on port `9090`.

Data retention is configured for three days.

## 14. Grafana Monitoring Dashboard

Grafana runs as an independent Docker container and uses Prometheus as its metrics data source.

The Prometheus data source URL configured inside Grafana is:

```text
http://prometheus:9090
```

### Dashboard

**ResilienceLab Cluster & Request Analytics**

The combined dashboard contains seven panels:

| Panel | Purpose |
|---|---|
| HTTP Request Rate | Displays HTTP request traffic over time |
| Failed Nodes | Displays the number of failed nodes |
| Healthy Nodes | Displays the number of healthy nodes |
| Total Nodes | Displays the total configured nodes |
| Request Duration (Latency) | Displays average HTTP request duration |
| Total HTTP Requests | Displays accumulated HTTP request count |
| Active Nodes | Displays the number of currently healthy nodes |

### Monitoring Access

| Service | Local URL |
|---|---|
| Prometheus | http://localhost:9090 |
| Prometheus Targets | http://localhost:9090/targets |
| Grafana | http://localhost:3000 |
| Application Metrics | http://localhost:8000/metrics |

## 15. Docker Compose Configuration

Docker Compose manages the main application and monitoring services.

### Services

| Service | Container Name | Port |
|---|---|---|
| FastAPI Application | resiliencelab-app | 8000 |
| Prometheus | resiliencelab-prometheus | 9090 |
| Grafana | resiliencelab-grafana | 3000 |

Prometheus and Grafana have individual memory limits of 256 MB.

Grafana data is persisted through the `grafana-data` Docker volume.

The three server node containers are currently created separately using the Docker CLI rather than being declared as Compose services.

## 16. Dashboard Communication

The frontend is implemented using HTML, CSS, and JavaScript in `static/index.html`.

The dashboard communicates with the FastAPI backend through HTTP API requests.

It displays:

- System overview.
- Simulated service health.
- Docker cluster health.
- Node status.
- Load-balancing activity.
- Request distribution.
- Event logs.

Dashboard information is refreshed periodically to reflect updated application and cluster state.

## 17. Configuration and Dependencies

Python dependencies are listed in `requirements.txt`.

Install them locally using:

```powershell
pip install -r requirements.txt
```

Build and start the application and monitoring stack using:

```powershell
docker compose up -d --build
```

Build the node image using:

```powershell
docker build -f Dockerfile.node -t resiliencelab-node:v1 .
```

The three node containers are started separately on the shared Docker network, as described in the deployment guide.

The main application mounts the local Docker socket to manage containers. This provides powerful access to the Docker host and must remain restricted to trusted local environments.

## 18. Technical Limitations

- The system uses a single FastAPI coordinator.
- Docker management depends on access to the local Docker Engine.
- The Docker socket mount provides privileged access to the host.
- Simulated application services are not independently deployed containers.
- The routing mechanism is application-level request forwarding, not a production-grade external load balancer.
- System metrics represent the host machine rather than individual node resources.
- Cluster node metrics refresh when the cluster-health endpoint is queried.
- SQLite is used for local persistence.
- Production-scale performance, resilience, and security have not been validated.

## 19. Future Engineering Work

Potential future improvements include:

- Periodic background refresh of cluster health metrics.
- Per-node resource monitoring.
- Weighted and least-connections routing algorithms.
- Configurable health-check intervals and reusable failure scenarios.
- PostgreSQL-based persistence for larger deployments.
- Distributed messaging and advanced orchestration experiments.
- Authentication, authorization, and multi-user access.
- Secure public deployment and production-scale testing.

## 20. Version 2.0 Technical Implementation

Version 2.0 extends the original platform with reliability management, recovery coordination, experiment execution, and additional observability.

### 20.1 Recovery Management

The recovery subsystem is organized into the following components:

- **RecoveryManager:** Maintains recovery state, retry scheduling, retry limits, strategy selection, and circuit breaker coordination.
- **RecoveryExecutor:** Executes one authorized recovery callback without owning retry scheduling or recovery policy.
- **Retry Strategies:** Supports fixed retry and exponential backoff.
- **Circuit Breaker:** Supports CLOSED, OPEN, and HALF_OPEN states.
- **Recovery Coordination:** Uses per-node asynchronous locks to protect recovery operations.
- **Persistence:** Stores recovery state so it can be restored when the application restarts.

The automatic recovery workflow detects failed nodes, checks recovery eligibility, executes the recovery operation, verifies node health, and records the outcome.

### 20.2 Experiment Subsystem

The experiment subsystem supports repeatable failure and recovery experiments.

- **ExperimentRepository:** Stores experiment records and retrieves historical results from SQLite.
- **ExperimentRunner:** Injects a controlled node failure and observes the recovery outcome.
- **BenchmarkRunner:** Executes trials sequentially, groups them under a shared run ID, and aggregates results.
- **Comparison:** Compares between two and ten experiment records.
- **Reports:** Generates individual experiment reports and benchmark-group reports.

Experiment records include execution status, target node, recovery strategy, timestamps, duration, configuration, and result information.

### 20.3 Experiment API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/experiments` | Run an experiment |
| GET | `/api/experiments` | List experiment history |
| GET | `/api/experiments/{experiment_id}` | Retrieve an experiment |
| POST | `/api/experiments/benchmark` | Execute sequential benchmark trials |
| GET | `/api/experiments/compare?ids=id1,id2` | Compare experiment records |
| GET | `/api/experiments/{experiment_id}/report` | Generate an individual report |
| GET | `/api/experiments/groups/{run_group_id}/report` | Generate a benchmark-group report |

### 20.4 Recovery Observability

V2 exposes recovery-related Prometheus metrics through the `/metrics` endpoint, including:

- Recovery attempt counters.
- Recovery result counters.
- Recovery duration histogram.
- Recovery retry counts.
- Consecutive recovery failure counts.
- Circuit breaker state gauges.

A manually configured nine-panel Grafana dashboard provides a reliability overview.

### 20.5 Isolated V2 Deployment

V2 uses a separate Compose configuration named `compose.v2.yaml`.

Start the V2 stack using:

```powershell
docker compose -p resiliencelab-v2 -f compose.v2.yaml up -d --build
```

The isolated deployment uses:

| Component | Host Port |
|---|---:|
| FastAPI application | 8001 |
| Prometheus | 9091 |
| Grafana | 3001 |

V2 uses a separate Docker network and persistent data volume to keep its deployment isolated from V1.

### 20.6 Validation

The recorded full automated test run completed with 141 passing tests. Local Docker integration experiments also verified node failure injection, automatic recovery, experiment execution, benchmark aggregation, comparison, reporting, and recovery metrics.

These results describe local validation only. Production-scale performance, public deployment, and production security have not been established.
