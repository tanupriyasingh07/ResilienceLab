# ResilienceLab — Technical Documentation

## 1. Technical Overview

ResilienceLab is implemented as a Python-based web application using FastAPI. It provides a browser dashboard for monitoring and interacting with simulated services and cluster nodes.

The backend handles application logic, request routing, recovery checks, system metrics, and database operations.

## 2. Technology Details

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API framework |
| Uvicorn | ASGI application server |
| HTML | Dashboard structure |
| CSS | Dashboard styling |
| JavaScript | Dashboard interactions and API calls |
| SQLite | Persistent state and event storage |
| psutil | Operating system metrics |

## 3. Application Structure

```text
ResilienceLab/
├── app/
│   ├── __init__.py
│   └── main.py
├── assets/
│   ├── architecture/
│   ├── demo/
│   └── screenshots/
├── data/
│   └── resilience.db
├── docs/
├── static/
│   └── index.html
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

The `venv/` directory contains the local Python virtual environment and should not be committed to Git.

## 4. Backend Implementation

The main backend implementation is located in `app/main.py`.

It contains:
- FastAPI application initialization.
- API route definitions.
- Service state management.
- Node state management.
- Failure and recovery operations.
- Round-robin request routing.
- Cluster health calculation.
- System metrics collection.
- SQLite database operations.
- Background recovery checks.

## 5. Service Management

The application maintains three simulated services:

| Service ID | Display Name |
|---|---|
| api-server | API Server |
| database | Database |
| worker | Background Worker |

Each service maintains its health status and restart information.

Users can trigger a failure or request manual recovery through the dashboard or API.

Failed services are automatically restored after the configured recovery interval.

## 6. Node Management

The simulated cluster contains three nodes:

- node-1
- node-2
- node-3

Node state includes health status, failure timestamp, and request count.

The backend checks failed nodes periodically and restores them after the configured recovery interval.

## 7. Load-Balancing Logic

ResilienceLab implements round-robin routing across healthy nodes.

The selection process:
1. Identify nodes currently marked healthy.
2. Select the next node using the round-robin position.
3. Skip nodes marked as failed.
4. Increment the selected node's request count.
5. Record the routing event.
6. Return the selected node.

If every node is unavailable, the API responds with HTTP 503.

## 8. Automatic Recovery

The recovery mechanism periodically checks the failure timestamps of simulated components.

When a component has remained failed for the configured recovery interval, the backend restores its healthy state and records the recovery event.

This mechanism demonstrates recovery logic; it does not restart real external services.

## 9. Database Design

The application uses SQLite for local persistence.

### logs

Stores system events, including:
- Service failures.
- Service recoveries.
- Node failures.
- Node recoveries.
- Successful request routing.

### system_state

Stores persisted application state for simulated components.

The database file is located at:

`data/resilience.db`

## 10. System Metrics

The application uses psutil to collect:

- CPU usage.
- Memory usage.
- Disk usage.
- System uptime.

These values describe the local machine running the application.

## 11. Dashboard Communication

The frontend uses JavaScript HTTP requests to communicate with the FastAPI backend.

Dashboard data is refreshed periodically to display updated metrics, component status, cluster health, and event logs.

## 12. Configuration and Dependencies

Python dependencies are listed in `requirements.txt`.

Install them using:

```powershell
pip install -r requirements.txt
```

Start the application using:

```powershell
uvicorn app.main:app --reload
```

## 13. Technical Limitations

The current release is a single-application simulation. It does not provide independent server orchestration, container management, production-grade distributed consensus, or real infrastructure recovery.

These capabilities are potential areas for future development.