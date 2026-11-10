# ResilienceLab — Project Overview

## 1. Introduction

ResilienceLab is a self-healing distributed systems monitoring and simulation project. It provides a local environment to explore how services and server nodes behave during failures, how recovery is handled, and how incoming requests can be routed to healthy nodes.

The application combines a FastAPI backend, a browser-based dashboard, and SQLite-based event persistence.

## 2. Problem Statement

Modern applications depend on multiple services and infrastructure components. A failure in one component can affect availability and interrupt request processing.

Understanding failure detection, recovery, service health, and traffic distribution is important when designing reliable systems.

ResilienceLab demonstrates these concepts through controlled failure simulations and a monitoring dashboard.

## 3. Project Objectives

- Monitor the health of application services and simulated nodes.
- Trigger and observe service and node failures.
- Demonstrate automatic recovery after a configured interval.
- Route requests across healthy nodes using round-robin logic.
- Exclude failed nodes from request distribution.
- Display CPU, memory, disk usage, and system uptime.
- Persist system events and state using SQLite.
- Provide REST API endpoints for interacting with the simulation.

## 4. Current Features

### Service Monitoring
Displays the health of three simulated services:
- API Server
- Database
- Background Worker

### Failure Simulation
Allows users to manually trigger failures for services and nodes.

### Automatic Recovery
A background recovery mechanism checks failed components and restores them after the configured recovery interval.

### Cluster Health
Displays total, healthy, and failed node counts along with the overall cluster status.

### Round-Robin Load Balancing
Distributes incoming test requests among available healthy nodes in sequence.

### System Monitoring
Displays CPU usage, memory usage, disk usage, and system uptime using psutil.

### Event Logging
Stores and displays system events, including failures, recoveries, and request-routing activity.

## 5. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, FastAPI |
| API Server | Uvicorn |
| Frontend | HTML, CSS, JavaScript |
| Database | SQLite |
| System Metrics | psutil |
| API Testing | Swagger UI |

## 6. Intended Users

ResilienceLab is intended for:
- Students learning distributed systems concepts.
- Developers exploring failure handling and recovery.
- Software engineering learners studying load balancing.
- Contributors interested in reliability engineering and monitoring tools.

## 7. Current System Scope

The current release is a local simulation environment.

Services and nodes are represented within a single FastAPI application. The load balancer demonstrates request-routing logic rather than distributing real network traffic across independent servers.

Automatic recovery applies to simulated components and does not restart external services or machines.

System metrics represent the machine running the application.

## 8. Future Direction

The project is planned to evolve toward a more realistic infrastructure reliability platform through:

- Independent service and node processes.
- Docker-based service deployment and failure simulation.
- Configurable health checks and recovery policies.
- Additional load-balancing algorithms.
- Historical metrics and performance analysis.
- Monitoring and alerting integrations.
- Cloud deployment and multi-user access.

These are planned enhancements and are not part of the current release.

## 9. Repository

GitHub: https://github.com/tanupriyasingh07/ResilienceLab

## 10. Project Author

Designed and developed by Tanupriya Singh.

## 11. License

This project is distributed under the MIT License. See the repository's LICENSE file for details.