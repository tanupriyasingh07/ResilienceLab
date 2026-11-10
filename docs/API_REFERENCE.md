# ResilienceLab — API Reference

## 1. Overview

ResilienceLab exposes REST API endpoints through FastAPI. These endpoints allow clients to inspect application health, retrieve service and node states, simulate failures, recover components, route requests, and retrieve system information.

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
| GET | `/api/health` | Application health |
| GET | `/api/services` | Retrieve service states |
| POST | `/api/services/{service_id}/fail` | Simulate service failure |
| POST | `/api/services/{service_id}/recover` | Recover a service |
| GET | `/api/nodes` | Retrieve node states |
| POST | `/api/nodes/{node_id}/fail` | Simulate node failure |
| POST | `/api/nodes/{node_id}/recover` | Recover a node |
| GET | `/api/route` | Route a test request |
| GET | `/api/cluster-health` | Retrieve cluster health |
| GET | `/api/system` | Retrieve local system metrics |
| GET | `/api/logs` | Retrieve event logs |

## 3. Application Health

### GET `/api/health`

Checks whether the application is running.

Example response:

```json
{
  "status": "running",
  "project": "ResilienceLab"
}
```

## 4. Service Endpoints

### GET `/api/services`

Returns the current status of the simulated services.

Available service IDs:

- `api-server`
- `database`
- `worker`

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

## 5. Node Endpoints

### GET `/api/nodes`

Returns the state and counters of simulated nodes.

Available node IDs:

- `node-1`
- `node-2`
- `node-3`

### POST `/api/nodes/{node_id}/fail`

Marks the selected node as failed.

Example:

```text
POST /api/nodes/node-2/fail
```

### POST `/api/nodes/{node_id}/recover`

Manually restores the selected node.

Example:

```text
POST /api/nodes/node-2/recover
```

## 6. Request Routing

### GET `/api/route`

Selects the next healthy node using round-robin scheduling and records the routed request.

Example:

```text
GET /api/route
```

Failed nodes are excluded from selection.

If no healthy nodes are available, the endpoint returns:

```text
HTTP 503 Service Unavailable
```

## 7. Cluster Health

### GET `/api/cluster-health`

Returns the current cluster health information.

The response includes healthy and failed node counts and the overall cluster status.

Possible status values:

- `healthy`
- `degraded`
- `unavailable`

## 8. System Metrics

### GET `/api/system`

Returns local machine metrics collected through psutil.

Metrics include:

- CPU utilization.
- Memory utilization.
- Disk utilization.
- System uptime.

## 9. Event Logs

### GET `/api/logs`

Retrieves recorded system events from SQLite.

Events may include:

- Service failure and recovery.
- Node failure and recovery.
- Request routing.

Records include event information and timestamps.

## 10. Testing with Swagger UI

1. Start the application.
2. Open `http://127.0.0.1:8000/docs`.
3. Expand the endpoint to test.
4. Click **Try it out**.
5. Enter any required parameters.
6. Click **Execute**.
7. Inspect the response and HTTP status code.

## 11. Suggested API Test Sequence

1. Call `/api/health`.
2. Retrieve `/api/services`.
3. Retrieve `/api/nodes`.
4. Fail `node-2`.
5. Check `/api/cluster-health`.
6. Call `/api/route` multiple times.
7. Verify that the failed node is excluded.
8. Recover `node-2`.
9. Retrieve `/api/logs`.

## 12. API Limitations

This API currently interacts with a local simulation.

The routing endpoint demonstrates application-level request selection, not production network traffic distribution. Failure and recovery operations change simulated component states rather than controlling independent infrastructure.