# API Reference

## 1. Overview

ResilienceLab exposes REST API endpoints through FastAPI. These endpoints allow users to inspect system health, simulate failures, recover components, route requests, and retrieve event logs.

**Base URL (local):**

```text
http://127.0.0.1:8000
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## 2. Endpoint Summary

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Check application health |
| GET | `/api/services` | Retrieve service states |
| POST | `/api/services/{service_id}/fail` | Simulate service failure |
| POST | `/api/services/{service_id}/recover` | Recover a service |
| GET | `/api/nodes` | Retrieve node states |
| POST | `/api/nodes/{node_id}/fail` | Simulate node failure |
| POST | `/api/nodes/{node_id}/recover` | Recover a node |
| GET | `/api/route` | Route a request to a healthy node |
| GET | `/api/cluster-health` | Retrieve cluster health |
| GET | `/api/system` | Retrieve local system metrics |
| GET | `/api/logs` | Retrieve system event logs |

## 3. Application Health

### `GET /api/health`

Checks whether the application is running.

**Example response:**

```json
{
  "status": "running",
  "project": "ResilienceLab"
}
```

## 4. Service Endpoints

### `GET /api/services`

Returns the current state of the simulated services.

Available service identifiers:

- `api-server`
- `database`
- `worker`

### `POST /api/services/{service_id}/fail`

Marks the specified service as failed and records its failure time.

**Example:**

```text
POST /api/services/api-server/fail
```

### `POST /api/services/{service_id}/recover`

Manually restores the specified service to a healthy state.

**Example:**

```text
POST /api/services/api-server/recover
```

## 5. Node Endpoints

### `GET /api/nodes`

Returns the current state and relevant counters for simulated nodes.

Available node identifiers:

- `node-1`
- `node-2`
- `node-3`

### `POST /api/nodes/{node_id}/fail`

Marks the selected node as failed.

**Example:**

```text
POST /api/nodes/node-2/fail
```

The failed node is excluded from subsequent routing decisions.

### `POST /api/nodes/{node_id}/recover`

Manually restores a failed node.

**Example:**

```text
POST /api/nodes/node-2/recover
```

## 6. Request Routing

### `GET /api/route`

Selects the next healthy node using round-robin scheduling and records the routed request.

**Example:**

```text
GET /api/route
```

When all nodes are healthy, requests are distributed sequentially across the nodes.

When a node fails, it is excluded from selection.

**Error condition:**

If no healthy nodes are available, the endpoint returns:

```text
HTTP 503 Service Unavailable
```

## 7. Cluster Health

### `GET /api/cluster-health`

Returns information about the current cluster state.

The response includes the number of healthy and failed nodes and an overall cluster health status.

Possible overall statuses:

- `healthy`
- `degraded`
- `unavailable`

## 8. System Metrics

### `GET /api/system`

Returns resource information for the machine running ResilienceLab.

The metrics include:

- CPU utilization.
- Memory utilization.
- Disk utilization.
- System uptime.

The values represent local host metrics, not independent node metrics.

## 9. Event Logs

### `GET /api/logs`

Retrieves recorded system events from SQLite.

Events can include:

- Service failure.
- Service recovery.
- Node failure.
- Node recovery.
- Request routing.

The returned records include event information and timestamps.

## 10. Testing Endpoints

You can test the API through the Swagger interface:

1. Start the application.
2. Open `http://127.0.0.1:8000/docs`.
3. Expand an endpoint.
4. Select **Try it out**.
5. Execute the request.
6. Inspect the response and HTTP status.

### Suggested Test Sequence

1. Call `/api/health`.
2. Call `/api/nodes`.
3. Fail `node-2`.
4. Call `/api/cluster-health`.
5. Call `/api/route` multiple times.
6. Verify that `node-2` is excluded.
7. Recover `node-2`.
8. Call `/api/logs` to inspect recorded events.

## 11. API Notes

- Failure and recovery operations use POST requests because they modify application state.
- GET requests retrieve information or trigger the current routing operation.
- The routing endpoint changes request counters and routing position as part of its simulation.
- Exact response fields can be inspected in the running Swagger documentation.
- This API currently operates against the local simulation and is not designed as a public production API.