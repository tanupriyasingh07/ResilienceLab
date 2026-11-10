# Testing and Validation

## 1. Overview

ResilienceLab was tested locally to validate its service monitoring, failure simulation, automatic recovery, node management, load balancing, and event logging functionality.

Testing was performed through the FastAPI endpoints, Swagger UI, and the dashboard.

## 2. Test Environment

- Operating System: Windows 11
- Backend: Python, FastAPI
- Database: SQLite
- Monitoring: psutil
- API Server: Uvicorn
- Testing Interface: Swagger UI and web dashboard

## 3. Functional Test Cases

| Test Case | Expected Result | Status |
|---|---|---|
| API health check | Returns running status | Passed |
| Service listing | Displays available services | Passed |
| Service failure | Changes service status to failed | Passed |
| Automatic service recovery | Restores service after recovery interval | Passed |
| Node failure | Marks selected node as failed | Passed |
| Node recovery | Restores node health | Passed |
| Round-robin routing | Distributes requests across healthy nodes | Passed |
| Failed-node exclusion | Prevents routing requests to failed nodes | Passed |
| Cluster health | Reports healthy and failed nodes | Passed |
| System monitoring | Returns CPU, memory, disk and uptime metrics | Passed |
| Event logging | Stores and retrieves system events | Passed |
| State persistence | Preserves node and service states using SQLite | Passed |

## 4. Failure Recovery Validation

The following scenarios were manually verified:

1. A service was marked as failed through its API endpoint.
2. The system detected the failed state.
3. Automatic recovery restored the service after the configured recovery interval.
4. The restart counter increased after recovery.
5. The same process was verified for simulated cluster nodes.

## 5. Load Balancing Validation

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

A failed node was excluded from subsequent routing requests.

## 6. API Testing

API endpoints were tested using FastAPI's interactive Swagger interface:

`http://127.0.0.1:8000/docs`

The tests covered health checks, service management, node management, routing, cluster health, system metrics, and event logs.

## 7. Current Limitations

- Nodes and services are simulated within a single application process.
- Failure recovery operates on simulated application state.
- The current implementation does not restart real infrastructure or independent containers.
- Performance and scalability have not been benchmarked under production workloads.
- Tests are currently manual; automated test coverage is planned.

## 8. Conclusion

The tested MVP successfully demonstrates local service monitoring, failure simulation, automatic recovery, round-robin routing, cluster health reporting, and event persistence.

Further testing will be required as independent services, container orchestration, and production deployment are introduced.