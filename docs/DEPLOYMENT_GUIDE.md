# ResilienceLab — Deployment Guide

## 1. Overview

This guide explains how to configure and run ResilienceLab in a local development environment.

The current version uses Docker containers for the FastAPI application, Prometheus monitoring, Grafana visualization, and three independent server nodes.

Public cloud deployment is not part of the current implementation.

## 2. System Requirements

| Requirement | Minimum |
|---|---|
| Operating System | Windows 10/11, Linux, or macOS |
| Docker | Docker Desktop or Docker Engine |
| Docker Compose | Compose V2 |
| Python | 3.12 recommended for local development |
| RAM | 8 GB recommended |
| Browser | Modern browser |
| Git | Recommended |
| Internet | Required for initial image and dependency downloads |

## 3. Project Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/tanupriyasingh07/ResilienceLab.git
cd ResilienceLab
```

Alternatively, download the project source code and open its folder in VS Code.

### Step 2: Verify Docker

Check Docker Engine:

```powershell
docker --version
docker compose version
```

Ensure Docker Desktop is running before proceeding.

### Step 3: Start the Application and Monitoring Stack

From the project root directory, run:

```powershell
docker compose up -d --build
```

This builds and starts:

- ResilienceLab FastAPI application.
- Prometheus metrics collector.
- Grafana monitoring dashboard.

### Step 4: Build the Server Node Image

Open a terminal in the project directory:

```powershell
docker build -f Dockerfile.node -t resiliencelab-node:v1 .
```

### Step 5: Create Three Docker Server Nodes

Create the three independent server containers on the application's Docker Compose network:

```powershell
docker run -d --name resiliencelab-node-1 --network resiliencelab_default -e NODE_ID=node-1 resiliencelab-node:v1

docker run -d --name resiliencelab-node-2 --network resiliencelab_default -e NODE_ID=node-2 resiliencelab-node:v1

docker run -d --name resiliencelab-node-3 --network resiliencelab_default -e NODE_ID=node-3 resiliencelab-node:v1
```

These nodes run independently from the Docker Compose services.

### Step 6: Verify Running Containers

```powershell
docker ps
```

You should see:

- `resiliencelab-app`
- `resiliencelab-prometheus`
- `resiliencelab-grafana`
- `resiliencelab-node-1`
- `resiliencelab-node-2`
- `resiliencelab-node-3`

## 4. Access the Application

Open the following URLs in your browser:

| Resource | URL |
|---|---|
| Application Dashboard | http://localhost:8000/ |
| API Documentation | http://localhost:8000/docs |
| Application Health | http://localhost:8000/api/health |
| Node Status | http://localhost:8000/api/nodes |
| Cluster Health | http://localhost:8000/api/cluster-health |
| Prometheus Metrics | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Prometheus Targets | http://localhost:9090/targets |
| Grafana | http://localhost:3000 |

## 5. Grafana Configuration

Grafana uses Prometheus as its metrics data source.

### Step 1: Log In

Open:

```text
http://localhost:3000
```

Local development credentials:

- Username: `admin`
- Password: `resiliencelab123`

### Step 2: Configure Prometheus Data Source

1. Open Connections → Data Sources.
2. Add a Prometheus data source.
3. Set the server URL to:

```text
http://prometheus:9090
```

4. Click Save & Test.
5. Confirm that the connection succeeds.

### Step 3: Open the Monitoring Dashboard

Open the saved dashboard:

**ResilienceLab Cluster & Request Analytics**

The dashboard contains seven monitoring panels:

1. HTTP Request Rate
2. Failed Nodes
3. Healthy Nodes
4. Total Nodes
5. Request Duration (Latency)
6. Total HTTP Requests
7. Active Nodes

## 6. Verify the Installation

After starting the complete stack:

1. Confirm that all six containers are running.
2. Open the application dashboard.
3. Execute the application health endpoint.
4. Check the cluster health endpoint.
5. Confirm that all three nodes report healthy.
6. Open the Prometheus Targets page and verify that the ResilienceLab target is UP.
7. Open the `/metrics` endpoint and confirm that application metrics are exposed.
8. Open Grafana and verify that the monitoring panels display data.
9. Test node failure injection.
10. Verify failure-aware routing and automatic recovery.

## 7. Database Storage

The SQLite database is stored at:

```text
data/resilience.db
```

It contains event logs and relevant persisted application state.

The database directory is mounted into the application container:

```yaml
volumes:
  - ./data:/app/data
```

Retain the database if you want to preserve stored records. Back it up before manually changing or deleting it.

Grafana dashboard data is persisted through the `grafana-data` Docker volume.

## 8. Stopping the Application

To stop the Docker Compose services:

```powershell
docker compose down
```

This stops the main application, Prometheus, and Grafana containers.

The three independently created node containers must be stopped separately:

```powershell
docker stop resiliencelab-node-1 resiliencelab-node-2 resiliencelab-node-3
```

To start the Compose services again:

```powershell
docker compose up -d
```

Start the three node containers again:

```powershell
docker start resiliencelab-node-1 resiliencelab-node-2 resiliencelab-node-3
```

## 9. Common Setup Issues

### Docker Command Not Found

Check whether Docker Desktop or Docker Engine is installed and running.

```powershell
docker --version
```

### Container Already Exists

If a node container already exists, do not create another container with the same name.

Check existing containers:

```powershell
docker ps -a
```

Start the existing node if it is stopped:

```powershell
docker start resiliencelab-node-1
```

Repeat for the other nodes if required.

### Port Already in Use

Check whether another application is using ports 8000, 9090, or 3000.

Stop the conflicting application or adjust the port mapping in `compose.yaml`.

### Prometheus Target Is Down

Check:

- The FastAPI application container is running.
- The metrics endpoint is accessible.
- The Prometheus configuration file exists.
- Prometheus and the application share the Docker Compose network.

Inspect Prometheus logs:

```powershell
docker logs resiliencelab-prometheus
```

### Grafana Cannot Connect to Prometheus

Verify that the Grafana data source URL is:

```text
http://prometheus:9090
```

Do not use `localhost:9090` inside Grafana because it runs in a separate container.

### Application Dashboard Does Not Load

Check:

- The application container is running.
- The terminal does not show application errors.
- The `static/index.html` file exists.
- The browser is using the correct local URL.

Inspect application logs:

```powershell
docker logs resiliencelab-app
```

## 10. Deployment Architecture — Future Plan

The current implementation is designed for local development and experimentation.

A future deployment may use a more scalable architecture:

```text
User Browser
     |
     v
Hosted Frontend
     |
     v
FastAPI Backend
     |
     v
Distributed Application Nodes
     |
     v
Persistent Database
     |
     v
Monitoring Infrastructure
```

Potential technologies:

| Component | Possible Technology |
|---|---|
| Source Control | GitHub |
| Frontend Hosting | Vercel |
| Backend Hosting | Python-compatible cloud platform |
| Containerization | Docker |
| Database | PostgreSQL |
| Metrics Collection | Prometheus |
| Monitoring Visualization | Grafana |
| Orchestration | Kubernetes |

These are future deployment possibilities, not part of the current release.

## 11. Production Deployment Considerations

Before making the platform publicly accessible, the following work is required:

- Configure production environment variables.
- Replace development-only credentials.
- Add authentication and authorization.
- Apply API input validation and security controls.
- Configure HTTPS.
- Secure Docker Engine access.
- Use appropriate persistent database storage.
- Configure monitoring retention and backups.
- Test concurrent requests.
- Validate recovery and failure-handling behaviour.
- Review resource limits and hosting costs.

The current Docker socket configuration provides powerful host-level access. It must not be exposed to untrusted networks.

The current simulation should not be exposed as a production infrastructure management service without these improvements.

## 12. Current Deployment Status

| Deployment Stage | Status |
|---|---|
| Local Docker application setup | Completed |
| Three Docker server nodes | Working |
| Local REST API | Working |
| SQLite persistence | Previously validated |
| Prometheus integration | Working |
| Grafana integration | Working |
| Combined monitoring dashboard | Working |
| Public GitHub repository | Existing |
| Cloud backend deployment | Planned |
| Public frontend deployment | Planned |
| Production security | Planned |

## 13. Conclusion

ResilienceLab currently runs as a local Docker-based distributed systems experimentation platform.

Its FastAPI backend, three Docker server nodes, Prometheus metrics collection, Grafana visualization, and SQLite persistence demonstrate the core self-healing and monitoring workflows.

Further security improvements, automated testing, concurrency validation, benchmarking, and cloud deployment work are required before production use.