# Development Roadmap

## 1. Vision

The long-term goal of ResilienceLab is to evolve from a local reliability simulation into a practical platform for experimenting with service failures, monitoring system health, and understanding recovery behaviour.

Development will progress in stages, with each stage building on a tested and documented foundation.

## 2. Current Status — Version 1.0

**Status: MVP completed**

The current version provides:

- FastAPI backend.
- Browser-based monitoring dashboard.
- Three simulated services.
- Three simulated nodes.
- Manual failure and recovery controls.
- Timed automatic recovery.
- Round-robin request routing.
- Failed-node exclusion.
- Cluster health calculation.
- Local CPU, memory, disk, and uptime metrics.
- SQLite event and state persistence.
- REST API documentation.

## 3. Phase 1 — Code Quality and Documentation

**Goal:** Prepare the current implementation for public development.

Planned tasks:

- Review project structure and code quality.
- Add automated tests.
- Improve input validation and error handling.
- Document API responses and configuration.
- Add dashboard screenshots and a demonstration video.
- Publish the source code on GitHub.
- Add an appropriate open-source license.

**Completion criteria:** A reproducible setup, documented codebase, and verified test suite.

## 4. Phase 2 — Container-Based Simulation

**Goal:** Move beyond simulated nodes running inside one process.

Planned technologies:
- Docker
- Docker Compose
- Python
- FastAPI

Planned tasks:

- Run services in independent containers.
- Introduce container health checks.
- Detect actual container failures.
- Restart failed containers through controlled policies.
- Display container status in the dashboard.
- Introduce configurable failure scenarios.

**Completion criteria:** Multiple independent services can be started, monitored, and tested locally.

## 5. Phase 3 — Advanced Reliability Mechanisms

**Goal:** Explore more realistic failure handling and traffic management.

Planned tasks:

- Add weighted round-robin routing.
- Explore least-connections routing.
- Introduce configurable health-check intervals.
- Implement retry and timeout policies.
- Explore circuit-breaker behaviour.
- Add configurable recovery delays.
- Measure recovery time and request failures.

**Potential technologies:**
- Python
- FastAPI
- Docker
- Redis, if shared state becomes necessary

**Completion criteria:** Additional routing and recovery strategies can be configured and tested against defined scenarios.

## 6. Phase 4 — Observability and Analytics

**Goal:** Improve visibility into system behaviour over time.

Planned technologies:
- Prometheus
- Grafana
- PostgreSQL

Planned tasks:

- Collect historical performance metrics.
- Track service availability.
- Record failure and recovery durations.
- Visualize request distribution.
- Add configurable metric thresholds.
- Introduce alerting integrations.
- Generate failure experiment reports.

**Completion criteria:** Users can inspect historical system behaviour and compare experiment results.

## 7. Phase 5 — Web Deployment and Multi-User Access

**Goal:** Make the platform accessible beyond the local development machine.

Planned tasks:

- Separate frontend and backend deployment.
- Configure production environment variables.
- Introduce authentication and authorization.
- Add secure API access.
- Configure persistent production storage.
- Add deployment monitoring.
- Test concurrent user access.

**Potential technologies:**
- Vercel or another suitable frontend host.
- A suitable backend hosting platform.
- PostgreSQL.
- Docker.

Hosting choices will depend on resource requirements, free-tier availability, and deployment constraints.

**Completion criteria:** Users can access a deployed version with appropriate security and operational controls.

## 8. Phase 6 — Public Developer Product

**Goal:** Develop ResilienceLab into a useful tool for developers and learners.

Potential features:

- Scenario-based failure experiments.
- Custom service configurations.
- Configurable recovery policies.
- Interactive architecture visualizations.
- Exportable experiment reports.
- Reusable testing scenarios.
- Public documentation and contribution guidelines.
- Installation and setup improvements.

**Completion criteria:** External users can install, understand, and use the platform independently.

## 9. Technology Evolution

| Area | Current | Potential Future |
|---|---|---|
| Backend | FastAPI | FastAPI |
| Frontend | HTML, CSS, JavaScript | Enhanced dashboard |
| Storage | SQLite | PostgreSQL |
| State coordination | In-process state | Redis or shared storage |
| Service environment | Local simulation | Docker containers |
| Monitoring | psutil | Prometheus |
| Visualization | Custom dashboard | Grafana integration |
| Deployment | Local machine | Cloud hosting |

These are proposed technology choices, not commitments to use every tool.

## 10. Development Principles

The project will follow these principles:

1. Build incrementally instead of introducing unnecessary complexity.
2. Test every major feature before moving forward.
3. Keep documentation aligned with actual implementation.
4. Prefer free and open-source technologies where practical.
5. Consider performance and security before public deployment.
6. Keep the architecture understandable and maintainable.
7. Avoid claiming production readiness without appropriate testing.

## 11. Success Criteria

Long-term progress will be evaluated through:

- Reliable failure detection.
- Measurable recovery behaviour.
- Correct routing under failure conditions.
- Reproducible test scenarios.
- Useful historical metrics.
- Secure deployment.
- Clear documentation.
- Successful use by developers outside the original development environment.

## 12. Roadmap Status

### Version 1.0 — MVP
**Status: Completed**

The original monitoring platform provides Docker node management, health checks, failure injection, automatic recovery, request routing, SQLite persistence, and monitoring dashboards.

### Version 2.0 — Reliability Hardening and Experimentation
**Status: Implemented and locally validated**

Completed capabilities:

- Centralized recovery management and recovery execution.
- Fixed retry and exponential backoff strategies.
- Circuit breaker with CLOSED, OPEN, and HALF_OPEN states.
- Controlled failure injection and automatic node recovery.
- Recovery state persistence and concurrency protection.
- Prometheus recovery metrics and Grafana reliability dashboard.
- Persistent experiment history.
- Sequential benchmark execution and aggregate results.
- Experiment comparison and individual/group reports.
- Automated test suite: 141 tests passed in the recorded full test run.
- Isolated V2 Docker deployment, validated separately from V1.

V2 has been validated through automated tests and local Docker integration experiments. This does not establish production readiness or production-scale performance.

### Future Development — Version 3.0 and Beyond

The following remain planned rather than implemented:

- Weighted and least-connections routing.
- Configurable health-check intervals and failure scenarios.
- Exportable experiment reports.
- Custom service configurations and reusable scenarios.
- Interactive architecture visualizations.
- Authentication, authorization, and multi-user access.
- Secure public deployment and production storage.
- External developer contributions and installation improvements.

Future phases will be marked complete only after implementation and validation.