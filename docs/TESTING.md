# Testing and Validation

## 1. Testing Overview

ResilienceLab was tested locally to verify its API endpoints, service and node state transitions, automatic recovery, routing behaviour, cluster health calculations, system metrics, and event logging.

Testing was performed using the FastAPI Swagger interface and the browser dashboard.

## 2. Testing Environment

| Component | Environment |
|---|---|
| Operating System | Windows 11 |
| Backend | Python, FastAPI |
| API Server | Uvicorn |
| Database | SQLite |
| System Metrics | psutil |
| API Testing | FastAPI Swagger UI |
| Dashboard | Local browser |

## 3. Functional Test Cases

| Test ID | Test Scenario | Expected Result | Observed Result |
|---|---|---|---|
| TC-01 | Check application health | Application reports running status | Passed |
| TC-02 | Retrieve service list | All three simulated services are returned | Passed |
| TC-03 | Fail a service | Selected service changes to failed | Passed |
| TC-04 | Automatic service recovery | Failed service recovers after configured interval | Passed |
| TC-05 | Retrieve node list | All three simulated nodes are returned | Passed |
| TC-06 | Fail a node | Selected node changes to failed | Passed |
| TC-07 | Recover a node | Selected node returns to healthy state | Passed |
| TC-08 | Verify recovery persistence | Failure timestamp is saved and restored | Passed |
| TC-09 | Check cluster health | Health reflects current node states | Passed |
| TC-10 | Verify round-robin routing | Requests follow node sequence | Passed |
| TC-11 | Exclude failed node | Failed node receives no new routed requests | Passed |
| TC-12 | Check local system metrics | CPU, memory, disk, and uptime are returned | Passed |
| TC-13 | Retrieve event logs | Recorded events are returned from SQLite | Passed |

## 4. Detailed Test Observations

### 4.1 Application Health

The health endpoint was tested and returned:

```json
{
  "status": "running",
  "project": "ResilienceLab"
}
```

**Result:** Passed.

### 4.2 Service Failure and Recovery

The `api-server` service was manually marked as failed.

Its status changed to failed and a failure timestamp was recorded. After the configured recovery interval, the service returned to a healthy state.

**Result:** Passed.

### 4.3 Node Failure and Recovery

A simulated node was marked as failed and then manually recovered.

The application correctly updated the node state. Automatic recovery was also verified.

**Result:** Passed.

### 4.4 Persistence of Failure State

The node failure timestamp was checked after saving and reloading application state.

The timestamp was retained, allowing the recovery checker to evaluate the elapsed failure duration.

**Result:** Passed.

### 4.5 Round-Robin Routing

Six consecutive routing requests were tested with all three nodes healthy.

Observed sequence:

```text
node-1
node-2
node-3
node-1
node-2
node-3
```

Each node received two requests.

**Result:** Passed.

### 4.6 Failed Node Exclusion

`node-2` was marked as failed. Subsequent routing requests selected the remaining healthy nodes.

The failed node did not receive new routed requests during this test.

**Result:** Passed.

### 4.7 Cluster Health

The cluster health endpoint was checked after a node failure.

With two healthy nodes and one failed node, the overall status was reported as degraded.

**Result:** Passed.

### 4.8 System Metrics

The system monitoring endpoint returned CPU, memory, disk, and uptime information using psutil.

**Result:** Passed.

### 4.9 Event Logging

The logs endpoint returned chronological events with timestamps and incremental identifiers.

Failure, recovery, and routing events were visible.

**Result:** Passed.

## 5. Dashboard Validation

The browser dashboard was checked for:

- System metric display.
- Service health status.
- Cluster health status.
- Node failure and recovery controls.
- Traffic distribution.
- Event log display.
- Periodic data refresh.

**Result:** Dashboard functionality and visual presentation verified locally.

## 6. Known Testing Limitations

The tests validate the current local simulation. They do not establish production readiness.

The following areas have not yet been validated:

- Communication between independent machines.
- Real container or process failure recovery.
- Concurrent multi-user workloads.
- High-volume performance and stress testing.
- Distributed state consistency.
- Production security and authentication.
- Cloud deployment reliability.

## 7. Conclusion

The current functional tests confirm that the implemented local simulation supports service and node failure operations, recovery, health-state tracking, failure-aware round-robin routing, system metrics, and persistent event logging.

Further integration, performance, security, and deployment testing will be required as the project evolves.