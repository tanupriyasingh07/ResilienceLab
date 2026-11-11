# Testing and Validation

## 1. Overview

ResilienceLab was tested locally to validate application health monitoring, simulated service management, Docker node monitoring, failure injection, automatic recovery, request routing, cluster health reporting, state persistence, and application observability.

Testing was performed using FastAPI endpoints, PowerShell commands, Docker commands, Prometheus, Grafana, and the web dashboard.

## 2. Test Environment

| Component | Technology |
|---|---|
| Operating System | Windows 11 |
| Backend | Python 3.12, FastAPI |
| API Server | Uvicorn |
| Container Runtime | Docker Engine |
| Container Management | Docker SDK, Docker Compose |
| Node Communication | HTTP |
| Database | SQLite |
| System Monitoring | psutil |
| Metrics Instrumentation | prometheus-client |
| Metrics Collection | Prometheus |
| Visualization | Grafana |
| Testing Interface | PowerShell, Swagger UI, Web Dashboard |

The test environment uses one FastAPI application container, three independent Docker node containers, one Prometheus container, and one Grafana container.

## 3. Functional Test Cases

| Test Case | Expected Result | Observed Result |
|---|---|---|
| API health check | Returns running status | Passed |
| Service listing | Displays available simulated services | Previously tested |
| Service failure | Changes service status to failed | Previously tested |
| Automatic service recovery | Restores service after recovery interval | Previously tested |
| Docker node listing | Returns actual node health information | Passed |
| Docker node failure | Stops the selected Docker container | Passed |
| Manual node recovery | Restarts container and verifies health | Previously tested |
| Automatic node recovery | Restarts failed Docker container | Passed |
| Round-robin routing | Distributes requests across healthy nodes | Passed |
| Failed-node exclusion | Skips unhealthy nodes | Passed |
| Cluster health | Reports healthy, degraded, or down status | Passed |
| System monitoring | Returns host CPU, memory, disk, and uptime metrics | Previously tested |
| Event logging | Stores and retrieves system events | Previously tested |
| State persistence | Preserves saved states using SQLite | Previously tested |
| Prometheus metrics endpoint | Exposes application metrics | Passed |
| Prometheus target scraping | Collects application metrics successfully | Passed |
| Grafana integration | Visualizes Prometheus metrics | Passed |
| Monitoring dashboard | Displays all seven configured panels | Passed |

## 4. Docker Node Failure and Recovery Validation

The Docker node failure workflow was tested using actual containers.

The following steps were verified:

1. All three Docker node containers were started.
2. Node health was checked through Docker status and HTTP health endpoints.
3. Node 2 was stopped using the failure injection API.
4. The application detected the node failure.
5. The cluster health endpoint reported two healthy nodes and one failed node.
6. The failed node was excluded from request routing.
7. Automatic recovery restarted the stopped container after the configured recovery delay.
8. The node health endpoint was checked again.
9. The node status and restart count were retrieved through the node listing endpoint.

Automatic recovery was verified by waiting approximately 65–70 seconds after failure injection.

### Observed Cluster State

| Condition | Total Nodes | Healthy Nodes | Failed Nodes | Cluster Status |
|---|---:|---:|---:|---|
| Before failure | 3 | 3 | 0 | healthy |
| Node 2 stopped | 3 | 2 | 1 | degraded |
| After automatic recovery | 3 | 3 | 0 | healthy |

## 5. Round-Robin Routing Validation

Round-robin routing was tested using six consecutive requests in an earlier validation.

The observed sequence was:

```text
Request 1 → node-1
Request 2 → node-2
Request 3 → node-3
Request 4 → node-1
Request 5 → node-2
Request 6 → node-3
```

### Failure-Aware Routing

Node 2 was stopped to simulate a failure.

Four subsequent requests were routed as follows:

```text
Request 1 → node-1
Request 2 → node-3
Request 3 → node-1
Request 4 → node-3
```

All four requests completed successfully.

This verified that the routing mechanism skipped the failed node and continued using healthy nodes.

## 6. Cluster Health Validation

The cluster health endpoint was tested under different node conditions.

The following cluster states are supported:

- `healthy` — All nodes are healthy.
- `degraded` — At least one node is healthy, but some nodes have failed.
- `down` — No nodes are healthy.

The following scenarios were verified:

- All three nodes healthy.
- One node stopped and two nodes healthy.
- All three nodes healthy again after automatic recovery.

## 7. State Persistence Validation

SQLite persistence was tested previously by rebuilding and restarting the application.

The following information is stored:

- Service states.
- Node states.
- Request counts.
- Restart counts.
- Failure timestamps.
- Event logs.

Previously saved state was successfully loaded after application rebuild and restart.

## 8. API Testing

The API endpoints were tested using PowerShell and FastAPI Swagger UI:

```text
http://localhost:8000/docs
```

Testing covered:

- Application health.
- Service failure and recovery.
- Docker node failure and recovery.
- Request routing.
- Cluster health.
- System metrics.
- Event logs.
- Prometheus metrics.

## 9. Prometheus Metrics Validation

Prometheus integration was tested using the application metrics endpoint and Prometheus Targets page.

### Metrics Endpoint

The following endpoint was verified:

```text
http://localhost:8000/metrics
```

The endpoint successfully exposed Python process metrics and ResilienceLab application metrics.

### Implemented Application Metrics

| Metric | Type | Validation |
|---|---|---|
| `resiliencelab_http_requests_total` | Counter | Passed |
| `resiliencelab_http_request_duration_seconds` | Histogram | Passed |
| `resiliencelab_active_nodes` | Gauge | Passed |
| `resiliencelab_total_nodes` | Gauge | Passed |

### Prometheus Target Validation

Prometheus target status was checked at:

```text
http://localhost:9090/targets
```

Observed configuration:

- Job name: `resiliencelab`
- Target: `resiliencelab:8000`
- Metrics path: `/metrics`
- Scrape interval: 5 seconds
- Target state: UP

The Prometheus target successfully scraped application metrics.

## 10. Grafana Dashboard Validation

Grafana was configured with Prometheus as its metrics data source.

The data source connection was tested successfully using:

```text
http://prometheus:9090
```

The combined dashboard was created and verified:

**ResilienceLab Cluster & Request Analytics**

The dashboard contains seven monitoring panels:

| Panel | Expected Information | Validation |
|---|---|---|
| HTTP Request Rate | HTTP request traffic over time | Passed |
| Failed Nodes | Number of failed nodes | Passed |
| Healthy Nodes | Number of healthy nodes | Passed |
| Total Nodes | Total configured nodes | Passed |
| Request Duration (Latency) | Average request duration | Passed |
| Total HTTP Requests | Accumulated HTTP request count | Passed |
| Active Nodes | Number of healthy nodes | Passed |

### Observed Monitoring Values

During the final monitoring validation:

- Active nodes: 3
- Healthy nodes: 3
- Failed nodes: 0
- Total nodes: 3
- HTTP request-duration observations: 27
- Prometheus target state: UP

The dashboard successfully displayed cluster statistics, HTTP request traffic, and request duration visualizations.

## 11. Current Limitations

- The application uses a single FastAPI coordinator.
- Docker node management depends on access to the local Docker Engine.
- The Docker socket provides powerful host-level access and must remain restricted to trusted local environments.
- Simulated application services are managed within the coordinator rather than running as independent service containers.
- The routing mechanism demonstrates application-level request forwarding, not production-grade external load balancing.
- System metrics represent the host machine rather than individual Docker nodes.
- Cluster node metrics are refreshed when the cluster-health endpoint is queried.
- Automated test coverage and production-scale performance benchmarks have not yet been implemented.

## 12. Conclusion

Local testing verified Docker-based node management, health checks, failure injection, automatic recovery, failure-aware round-robin routing, cluster health reporting, and SQLite state persistence.

Prometheus metrics collection and Grafana dashboard integration were also successfully validated.

These results demonstrate the core self-healing and monitoring workflows of ResilienceLab in a local experimentation environment. Further automated testing, concurrency validation, benchmarking, and distributed deployment work remain necessary before production use.