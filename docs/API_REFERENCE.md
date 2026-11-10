# ResilienceLab — API Reference

## 1. Overview

ResilienceLab exposes REST API endpoints through FastAPI. The API allows clients to monitor application health, inspect services and Docker nodes, inject failures, trigger recovery, route requests, and retrieve system metrics and event logs.

### Base URL

```text
http://127.0.0.1:8000
```

### Interactive API Documentation

```text
http://127.0.0.1:8000/docs
```

## 2. Endpoint Summary

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check application health |
| GET | `/api/services` | Retrieve simulated service states |
| POST | `/api/services/{service_id}/fail` | Simulate service failure |
| POST | `/api/services/{service_id}/recover` | Recover a service |
| GET | `/api/nodes` | Retrieve Docker node states |
| POST | `/api/nodes/{node_id}/fail` | Stop a Docker node container |
| POST | `/api/nodes/{node_id}/recover` | Manually recover a Docker node |
| POST | `/api/route` | Route a request to a healthy node |
| GET | `/api/cluster-health` | Retrieve cluster health |
| GET | `/api/system` | Retrieve local system metrics |
| GET | `/api/logs` | Retrieve recorded event logs |

## 3. Application Health

### GET `/api/health`

Checks whether the ResilienceLab application is running.

Example response:

```json
{
  "status": "running",
  "project": "ResilienceLab"
}
```

## 4. Service Endpoints

These endpoints manage simulated application services.

Available service IDs:

- `api-server`
- `database`
- `worker`

### GET `/api/services`

Returns the current state of all simulated services.

### POST `/api/services/{service_id}/fail`

Marks the specified service as failed and records its failure timestamp.

Example:

```text
POST /api/services/api-server/fail
```

### POST `/api/services/{service_id}/recover`

Manually restores the specified service.

Example:

```text
POST /api/services/api-server/recover
```

The recovery operation updates the service state and records the event.

## 5. Docker Node Endpoints

ResilienceLab manages three independent Docker node containers.

Available node IDs:

- `node-1`
- `node-2`
- `node-3`

### GET `/api/nodes`

Returns node information, including:

- Node name.
- Actual health status.
- Request count.
- Failure timestamp.
- Restart count.

Node health is checked using Docker container status and the node's HTTP health endpoint.

### POST `/api/nodes/{node_id}/fail`

Stops the corresponding Docker container to simulate an actual node failure.

Example:

```text
POST /api/nodes/node-2/fail
```

### POST `/api/nodes/{node_id}/recover`

Attempts to restart the selected Docker container and verify its health.

Example:

```text
POST /api/nodes/node-2/recover
```

The endpoint returns an error if the node cannot be recovered or its health check fails.

## 6. Request Routing

### POST `/api/route`

Routes a test request to a healthy Docker node.

The routing mechanism:

1. Selects nodes using round-robin scheduling.
2. Checks node availability.
3. Skips unhealthy nodes.
4. Sends an HTTP request to the selected node's `/process` endpoint.
5. Records successful request counts.

Example:

```text
POST /api/route
```

Failed nodes are excluded from routing.

If no healthy nodes are available, the API returns:

```text
HTTP 503 Service Unavailable
```

## 7. Cluster Health

### GET `/api/cluster-health`

Returns the current health summary of the Docker node cluster.

The response includes:

- Total nodes.
- Healthy nodes.
- Failed nodes.
- Overall cluster status.

Possible cluster status values:

- `healthy` — All nodes are healthy.
- `degraded` — At least one node is healthy, but some nodes have failed.
- `down` — No nodes are healthy.

## 8. System Metrics

### GET `/api/system`

Returns local system metrics collected using `psutil`.

Metrics include:

- CPU utilization.
- Memory utilization.
- Disk utilization.
- System uptime.

These metrics describe the machine running the ResilienceLab application, not individual Docker nodes.

## 9. Event Logs

### GET `/api/logs`

Retrieves recorded system events stored in SQLite.

Events may include:

- Service failure and recovery.
- Docker node failure detection.
- Automatic and manual node recovery.
- Request routing and failures.

Event records are persisted in the local SQLite database.

## 10. Testing with Swagger UI

1. Start Docker Desktop.
2. Start the ResilienceLab application and Docker nodes.
3. Open `http://127.0.0.1:8000/docs`.
4. Expand the endpoint you want to test.
5. Click **Try it out**.
6. Enter the required path parameters, if applicable.
7. Click **Execute**.
8. Inspect the response and HTTP status code.

## 11. Suggested API Test Sequence

1. Call `/api/health`.
2. Retrieve `/api/services`.
3. Retrieve `/api/nodes`.
4. Stop `node-2` using `/api/nodes/node-2/fail`.
5. Check `/api/cluster-health`.
6. Send multiple requests using `POST /api/route`.
7. Verify that requests are routed to healthy nodes.
8. Recover `node-2` using `/api/nodes/node-2/recover`.
9. Verify node health using `/api/nodes`.
10. Retrieve `/api/logs`.

## 12. API Limitations

- The API is currently designed for local experimentation.
- Docker node management depends on access to the local Docker Engine.
- The routing mechanism demonstrates application-level request selection and forwarding; it is not a production-grade external load balancer.
- The application uses a single FastAPI coordinator.
- System metrics represent the host machine rather than per-node resource metrics.
- The current implementation has not been validated for production-scale workloads.

