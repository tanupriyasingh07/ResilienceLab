# ResilienceLab

**A Self-Healing Distributed Systems Monitor**

ResilienceLab is a local simulation environment for exploring service failures, node health, automatic recovery, and traffic distribution. It provides a dashboard and REST API to observe how a small simulated cluster behaves when components fail and recover.

## Overview

Modern applications often depend on multiple services and servers. When one component becomes unavailable, the system should detect the failure, maintain visibility into its health, and direct traffic toward available components.

ResilienceLab demonstrates these concepts through a controlled, locally runnable environment.

## Features

- **Service health monitoring:** View the status of simulated API, database, and worker services.
- **Failure simulation:** Trigger service and node failures manually.
- **Automatic recovery:** Simulated failed components recover automatically after a configured interval.
- **Cluster health:** Monitor healthy and failed nodes and view the overall cluster status.
- **Round-robin load balancing:** Distribute requests across healthy nodes.
- **Failure-aware routing:** Exclude failed nodes from request distribution.
- **System monitoring:** Display CPU, memory, disk usage, and uptime.
- **Event logging:** Store and view system events using SQLite.
- **Live dashboard:** Refresh system information and component status automatically.

## Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |
| System metrics | psutil |
| API server | Uvicorn |

## System Architecture

The following diagram represents the current implementation of ResilienceLab. Services and nodes are simulated within a single FastAPI application process.

![ResilienceLab System Architecture](assets/architecture/system-architecture.png)

## Project Demo

Watch the ResilienceLab demonstration:

[![ResilienceLab Project Demo](https://img.youtube.com/vi/Pv6WM5nrrmQ/hqdefault.jpg)](https://youtu.be/Pv6WM5nrrmQ)

▶ **[Watch the Full Demo on YouTube](https://youtu.be/Pv6WM5nrrmQ)**

The demonstration covers:

- Live system monitoring
- Service failure simulation
- Automatic recovery
- Node health monitoring
- Round-robin load balancing
- Event logging

*Video visibility: Unlisted.*

## Dashboard Preview

### System Overview
![Dashboard Overview](assets/screenshots/dashboard-overview.png)

### Service Health
![Service Health](assets/screenshots/service-health.png)

### Cluster Health
![Cluster Health](assets/screenshots/cluster-health.png)

### Load Balancer and Nodes
![Load Balancer](assets/screenshots/load-balancer.png)

### Event Logs
![Event Logs](assets/screenshots/event-logs.png)

## Project Structure

```text
ResilienceLab/
├── app/
│   ├── __init__.py
│   └── main.py
├── data/
│   └── resilience.db
├── docs/
│   ├── PROJECT_OVERVIEW.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── TECHNICAL_DOCUMENTATION.md
│   ├── API_REFERENCE.md
│   ├── TESTING.md
│   ├── MARKET_RESEARCH.md
│   ├── REAL_WORLD_USE_CASES.md
│   ├── DEVELOPMENT_ROADMAP.md
│   └── DEPLOYMENT_GUIDE.md
├── static/
│   └── index.html
├── .gitignore
├── README.md
└── requirements.txt
```

## Getting Started

### Prerequisites

- Python 3.10 or later
- pip

### Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd ResilienceLab
```

2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate it on Windows:

```bash
venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Start the application:

```bash
uvicorn app.main:app --reload
```

### Access the Application

- Dashboard: http://127.0.0.1:8000/
- API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/api/health

## API Overview

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/health` | GET | Check application status |
| `/api/services` | GET | View service status |
| `/api/services/{service_id}/fail` | POST | Simulate service failure |
| `/api/services/{service_id}/recover` | POST | Recover a service |
| `/api/nodes` | GET | View node status |
| `/api/nodes/{node_id}/fail` | POST | Simulate node failure |
| `/api/nodes/{node_id}/recover` | POST | Recover a node |
| `/api/route` | GET | Route a request to a healthy node |
| `/api/cluster-health` | GET | View cluster health |
| `/api/system` | GET | View local system metrics |
| `/api/logs` | GET | Retrieve event logs |

See [API Reference](docs/API_REFERENCE.md) for details.

## Current Scope and Limitations

The current version is a local simulation, not a production distributed infrastructure platform.

- Services and nodes are simulated within one application process.
- The load balancer demonstrates round-robin routing logic; it does not distribute network traffic between independent servers.
- System metrics describe the machine running the application.
- Recovery is simulated and does not restart real external services or machines.

These boundaries are intentional for the current development stage.

## Documentation

Detailed project documentation is available in the [`docs/`](docs/) directory:

- Project overview
- System architecture
- Technical documentation
- API reference
- Testing
- Market research
- Real-world use cases
- Development roadmap
- Deployment guide

## Future Development

Planned areas of development include:

- Real service and node integration
- Container-based failure simulation
- More advanced load-balancing strategies
- Configurable health checks and recovery policies
- Historical metrics and performance analysis
- Monitoring and alerting integrations
- Cloud deployment and multi-user access

These are planned enhancements, not features of the current version.

## Author

**Designed and developed by Tanupriya Singh**