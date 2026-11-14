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

ResilienceLab is a local distributed systems and reliability engineering experimentation platform.

The system manages three independent Docker-based worker nodes through a central FastAPI application. Application-level services remain simulated within the backend, while Docker nodes run as separate containers.

The platform supports:

- Docker node health monitoring and controlled failure injection.
- Automatic recovery using centralized recovery management.
- Fixed retry and exponential backoff strategies.
- Circuit breaker states and recovery coordination.
- Persistent recovery state and experiment history.
- Prometheus metrics and Grafana monitoring.
- Sequential reliability benchmarks, experiment comparisons, and reports.

The platform is designed for local experimentation and learning. It is not a production-grade orchestration system, and production-scale performance and security have not been established.

## 8. Future Direction

Future development aims to extend ResilienceLab into a more configurable and extensible reliability engineering platform through:

- Weighted and least-connections load-balancing algorithms.
- Configurable health-check intervals and failure scenarios.
- Exportable experiment reports and reusable experiment configurations.
- Interactive architecture visualizations.
- Authentication, authorization, and multi-user access.
- Secure public deployment and production-grade storage.
- Improved installation workflows and external developer contributions.

These capabilities remain planned and will be marked complete only after implementation and validation.

## 9. Repository

GitHub: https://github.com/tanupriyasingh07/ResilienceLab

## 10. Project Author

Designed and developed by Tanupriya Singh.

## 11. License

This project is distributed under the MIT License. See the repository's LICENSE file for details.