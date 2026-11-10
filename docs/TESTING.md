# Testing and Validation

## 1. Overview

ResilienceLab was tested locally to validate application health monitoring, simulated service management, Docker node monitoring, failure injection, automatic recovery, request routing, cluster health reporting, and state persistence.

Testing was performed using FastAPI endpoints, Swagger UI, Docker commands, and the web dashboard.

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
| Testing Interface | Swagger UI and Web Dashboard |

The test environment uses one FastAPI application container and three independent Docker node containers.

## 3. Functional Test Cases

| Test Case | Expected Result | Observed Result |
|---|---|---|
| API health check | Returns running status | Passed |
| Service listing | Displays available simulated services | Passed |
| Service failure | Changes service status to failed | Passed |
| Automatic service recovery | Restores service after recovery interval | Passed |
| Docker node listing | Returns actual node health information | Passed |
| Docker node failure | Stops the selected Docker container | Passed |
| Manual node recovery | Restarts container and verifies health | Passed |
| Automatic node recovery | Restarts failed Docker container | Passed |
| Round-robin routing | Distributes requests across healthy nodes | Passed |
| Failed-node exclusion | Skips unhealthy nodes | Passed |
| Cluster health | Reports healthy, degraded, or down status | Passed |
| System monitoring | Returns host CPU, memory, disk, and uptime metrics | Passed |
| Event logging | Stores and retrieves system events | Passed |
| State persistence | Preserves saved states using SQLite | Passed |

## 4. Docker Node Failure and Recovery Validation

The Docker node failure workflow was tested using actual containers.

The following steps were verified:

1. All three Docker node containers were started.
2. Node health was checked through Docker status and HTTP health endpoints.
3. A node was stopped using the failure injection API.
4. The application detected the node failure.
5. The failed node was excluded from request routing.
6. Automatic recovery restarted the stopped container after the configured recovery delay.
7. The node health endpoint was checked again.
8. The restart counter was updated after successful automatic recovery.

Automatic recovery was verified by waiting approximately 65 seconds after failure injection.

## 5. Round-Robin Routing Validation

Round-robin routing was tested using six consecutive requests.

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

Node-2 was stopped to simulate a failure.

Four subsequent requests were routed as follows:

```text
Request 1 → node-1
Request 2 → node-3
Request 3 → node-1
Request 4 → node-3
```

This verified that the routing mechanism skipped the failed node and continued using healthy nodes.

## 6. Cluster Health Validation

The cluster health endpoint was tested under different node conditions.

The following cluster states are supported:

- `healthy` — All nodes are healthy.
- `degraded` — At least one node is healthy, but some nodes have failed.
- `down` — No nodes are healthy.

The all-healthy scenario was verified with three healthy Docker nodes.

## 7. State Persistence Validation

SQLite persistence was tested by rebuilding and restarting the application.

The following information is stored:

- Service states.
- Node states.
- Request counts.
- Restart counts.
- Failure timestamps.
- Event logs.

Previously saved state was successfully loaded after application rebuild and restart.

## 8. API Testing

The API endpoints were tested using FastAPI Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Testing covered:

- Application health.
- Service failure and recovery.
- Docker node failure and recovery.
- Request routing.
- Cluster health.
- System metrics.
- Event logs.

## 9. Current Limitations

- The application uses a single FastAPI coordinator.
- Docker node management depends on access to the local Docker Engine.
- The Docker socket provides powerful host-level access and must remain restricted to trusted local environments.
- Simulated application services are managed within the coordinator rather than running as independent service containers.
- The routing mechanism demonstrates application-level request forwarding, not production-grade external load balancing.
- System metrics represent the host machine rather than individual Docker nodes.
- Automated test coverage and production-scale performance benchmarks have not yet been implemented.

## 10. Conclusion

Local testing verified Docker-based node management, health checks, failure injection, automatic recovery, failure-aware round-robin routing, cluster health reporting, and SQLite state persistence.

These results demonstrate the core self-healing workflow of ResilienceLab in a local experimentation environment. Further automated testing, concurrency validation, benchmarking, and distributed deployment work remain necessary before production use.