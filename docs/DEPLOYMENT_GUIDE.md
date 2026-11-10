# Deployment Guide

## 1. Overview

This guide explains how to set up and run ResilienceLab in a local development environment.

The current version is designed for local execution. Public cloud deployment is a future development goal and is not part of the current implementation.

## 2. System Requirements

| Requirement | Minimum |
|---|---|
| Operating System | Windows 10/11, Linux, or macOS |
| Python | 3.10 or later |
| Package Manager | pip |
| Browser | Modern browser |
| RAM | 4 GB recommended |
| Internet | Required for initial dependency installation |

## 3. Project Setup

### Step 1: Obtain the Source Code

Clone the GitHub repository:

```bash
git clone <repository-url>
cd ResilienceLab
```

Alternatively, download the project source code and open its folder in VS Code.

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```

A virtual environment keeps project dependencies separate from other Python installations.

### Step 3: Activate the Environment

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

**Windows Command Prompt:**

```cmd
venv\Scripts\activate.bat
```

**Linux or macOS:**

```bash
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

The current project dependencies include:

- FastAPI
- Uvicorn
- psutil

### Step 5: Start the Application

```bash
uvicorn app.main:app --reload
```

The development server will start locally.

## 4. Access the Application

Open the following addresses in a browser:

| Resource | URL |
|---|---|
| Dashboard | http://127.0.0.1:8000/ |
| API Documentation | http://127.0.0.1:8000/docs |
| Application Health | http://127.0.0.1:8000/api/health |

## 5. Verify the Installation

After starting the server:

1. Open the dashboard.
2. Confirm that service and node information is visible.
3. Check that local system metrics are displayed.
4. Open the API documentation.
5. Execute the application health endpoint.
6. Trigger a simulated failure.
7. Verify that the component status changes.
8. Observe automatic recovery.
9. Inspect the event logs.

## 6. Database Storage

The SQLite database is stored at:

```text
data/resilience.db
```

It contains the event logs and relevant persisted simulation state.

The application uses its database initialization logic when starting.

For local development, retain the database if you want to preserve its stored records. Back it up before manually changing or deleting it.

## 7. Stopping the Application

To stop the local development server, press:

```text
Ctrl + C
```

in the terminal running Uvicorn.

Deactivate the virtual environment when finished:

```bash
deactivate
```

## 8. Common Setup Issues

### Python Command Not Found

Check whether Python is installed:

```bash
python --version
```

If necessary, install Python and ensure it is available in the system PATH.

### Dependency Installation Failure

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Then reinstall the project dependencies:

```bash
pip install -r requirements.txt
```

### Port Already in Use

Run the application on another port:

```bash
uvicorn app.main:app --reload --port 8001
```

Open the dashboard at `http://127.0.0.1:8001/`.

### Dashboard Does Not Load

Check that:

- Uvicorn is running.
- The terminal does not show application errors.
- The `static/index.html` file exists.
- The browser is using the correct local URL.

## 9. Deployment Architecture — Future Plan

The current local application is not yet deployed as a public service.

A future deployment may use separate frontend and backend hosting.

Potential architecture:

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
Application Services
     |
     v
Persistent Database
```

Potential deployment technologies:

| Component | Possible Technology |
|---|---|
| Source code | GitHub |
| Frontend hosting | Vercel |
| Backend hosting | Suitable Python hosting platform |
| Containerization | Docker |
| Database | PostgreSQL |
| Monitoring | Prometheus and Grafana |

The final hosting choices will depend on the requirements of the expanded application.

## 10. Production Deployment Considerations

Before making the platform publicly accessible, the following work is required:

- Configure production environment variables.
- Remove development-only settings.
- Add authentication and authorization.
- Apply API input validation and security controls.
- Configure HTTPS.
- Use appropriate persistent database storage.
- Add logging and monitoring.
- Test concurrent requests.
- Validate recovery and failure-handling behaviour.
- Review resource limits and hosting costs.

The current simulation should not be exposed as a production infrastructure management service without these improvements.

## 11. Current Deployment Status

| Deployment Stage | Status |
|---|---|
| Local development setup | Completed |
| Local dashboard | Working |
| Local REST API | Working |
| SQLite persistence | Working |
| Public GitHub repository | Planned |
| Cloud backend deployment | Planned |
| Public frontend deployment | Planned |
| Production security | Planned |

## 12. Conclusion

ResilienceLab v1.0 can be installed and executed locally using Python and its listed dependencies.

Future deployment will require additional architecture, security, persistence, and operational work before the platform is suitable for public use.