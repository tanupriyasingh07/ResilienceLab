
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import psutil
import sqlite3
import asyncio
import time
from datetime import datetime
from fastapi.responses import FileResponse
import docker
import json
import urllib.request
import urllib.error
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
from pathlib import Path
import threading
import os
from app.recovery.state import RecoveryState
from app.recovery.manager import RecoveryManager
from app.recovery.executor import RecoveryExecutor
from fastapi import Query
from pydantic import BaseModel, Field

from app.experiments.repository import ExperimentRepository
from app.experiments.runner import ExperimentRunner
from app.experiments.benchmark import BenchmarkRunner
from app.experiments.comparison import compare_experiments
from app.experiments.reports import (
    build_experiment_report,
    build_benchmark_report,
)


DB = "data/resilience.db"

services = {
    "api-server": {"name": "API Server", "status": "healthy", "restarts": 0, "failed_at": None},
    "database": {"name": "Database", "status": "healthy", "restarts": 0, "failed_at": None},
    "worker": {"name": "Background Worker", "status": "healthy", "restarts": 0, "failed_at": None}
}


nodes = {
    "node-1": {"name": "Server Node 1", "status": "healthy", "requests": 0, "failed_at": None, "restarts": 0},
    "node-2": {"name": "Server Node 2", "status": "healthy", "requests": 0, "failed_at": None, "restarts": 0},
    "node-3": {"name": "Server Node 3", "status": "healthy", "requests": 0, "failed_at": None, "restarts": 0}
}

rr_index = 0
route_lock = asyncio.Lock()
database_lock = asyncio.Lock()
state_write_lock = threading.RLock()
docker_client = docker.from_env()
recovery_manager = None
experiment_runner = None
benchmark_runner = None


class ExperimentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    target_node: str
recovery_executor = RecoveryExecutor()

class BenchmarkCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    target_node: str
    trials: int = Field(default=5, ge=1, le=20)


NODE_CONTAINER_PREFIX = os.getenv(
    "NODE_CONTAINER_PREFIX",
    "resiliencelab-node"
)

NODE_CONTAINER_NAMES = {
    "node-1": f"{NODE_CONTAINER_PREFIX}-1",
    "node-2": f"{NODE_CONTAINER_PREFIX}-2",
    "node-3": f"{NODE_CONTAINER_PREFIX}-3"
}

node_recovery_locks = {
    node_id: asyncio.Lock()
    for node_id in nodes
}


def get_docker_node_status(node_id):
    """Return the real Docker node state using container status and its HTTP health endpoint."""
    container_name = NODE_CONTAINER_NAMES[node_id]

    try:
        container = docker_client.containers.get(container_name)
        container.reload()

        if container.status != "running":
            return "failed"

        request = urllib.request.Request(
            f"http://{container_name}:9000/health",
            headers={"Connection": "close"}
        )

        with urllib.request.urlopen(request, timeout=1.5) as response:
            if response.status != 200:
                return "failed"

            health_data = json.loads(response.read().decode("utf-8"))
            return "healthy" if health_data.get("status") == "healthy" else "failed"

    except (docker.errors.NotFound, urllib.error.URLError, TimeoutError, ValueError):
        return "failed"
    except Exception:
        return "failed"




def init_db():
    Path(DB).parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB, timeout=10) as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT,
                event TEXT,
                timestamp TEXT
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS system_state (
                item_id TEXT PRIMARY KEY,
                item_type TEXT,
                status TEXT,
                restarts INTEGER DEFAULT 0,
                requests INTEGER DEFAULT 0,
                failed_at REAL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS recovery_state (
                item_id TEXT PRIMARY KEY,
                item_type TEXT NOT NULL,
                strategy TEXT NOT NULL DEFAULT 'fixed_retry',
                retry_count INTEGER NOT NULL DEFAULT 0,
                last_attempt_at REAL,
                next_retry_at REAL,
                consecutive_failures INTEGER NOT NULL DEFAULT 0,
                circuit_state TEXT NOT NULL DEFAULT 'closed',
                circuit_opened_at REAL,
                updated_at REAL
            )
        """)

        # Experiment history and benchmark trial records
        conn.execute("""
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                run_group_id TEXT,
                trial_number INTEGER NOT NULL DEFAULT 1,
                name TEXT NOT NULL,
                target_node TEXT NOT NULL,
                strategy TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'running'
                    CHECK(status IN (
                        'running',
                        'completed',
                        'failed',
                        'timed_out'
                    )),
                started_at REAL NOT NULL,
                completed_at REAL,
                duration_seconds REAL,
                outcome TEXT,
                error TEXT,
                config_json TEXT NOT NULL DEFAULT '{}',
                result_json TEXT NOT NULL DEFAULT '{}'
            )
        """)

        # Indexes for experiment history and benchmark lookups
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiments_started_at
            ON experiments(started_at DESC)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_experiments_run_group
            ON experiments(run_group_id)
        """)

        # Existing system_state migration
        columns = [
            row[1] for row in
            conn.execute("PRAGMA table_info(system_state)").fetchall()
        ]

        if "failed_at" not in columns:
            conn.execute("""
                ALTER TABLE system_state
                ADD COLUMN failed_at REAL
            """)



def log_event(service, event):
    with sqlite3.connect(DB) as conn:
        conn.execute(
            "INSERT INTO logs (service, event, timestamp) VALUES (?, ?, ?)",
            (service, event, datetime.now().isoformat(timespec="seconds"))
        )




def _write_state_snapshot(service_snapshot, node_snapshot):
    with sqlite3.connect(DB, timeout=10) as conn:

        # Save services
        for item_id, item in service_snapshot.items():
            conn.execute("""
                INSERT OR REPLACE INTO system_state
                (item_id, item_type, status, restarts, requests, failed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                "service",
                item["status"],
                item["restarts"],
                0,
                item["failed_at"]
            ))

        # Save server nodes
        for item_id, item in node_snapshot.items():
            conn.execute("""
                INSERT OR REPLACE INTO system_state
                (item_id, item_type, status, restarts, requests, failed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                "node",
                item["status"],
                item["restarts"],
                item["requests"],
                item["failed_at"]
            ))


def _get_state_snapshot():
    service_snapshot = {
        item_id: {
            "status": item["status"],
            "restarts": item["restarts"],
            "failed_at": item["failed_at"]
        }
        for item_id, item in services.items()
    }

    node_snapshot = {
        item_id: {
            "status": item["status"],
            "restarts": item["restarts"],
            "requests": item["requests"],
            "failed_at": item["failed_at"]
        }
        for item_id, item in nodes.items()
    }

    return service_snapshot, node_snapshot



def save_states():
    with state_write_lock:
        service_snapshot, node_snapshot = _get_state_snapshot()

        _write_state_snapshot(
            service_snapshot,
            node_snapshot
        )



# Asynchronous database wrappers
async def async_log_event(service, event):
    await asyncio.to_thread(log_event, service, event)




async def async_save_states():
    async with database_lock:
        await asyncio.to_thread(save_states)








def load_states():
    with sqlite3.connect(DB, timeout=10) as conn:
        rows = conn.execute("""
            SELECT item_id, item_type, status, restarts, requests, failed_at
            FROM system_state
        """).fetchall()

    for item_id, item_type, status, restarts, requests, failed_at in rows:

        if item_type == "service":
            collection = services

        elif item_type == "node":
            collection = nodes

        else:
            continue

        if item_id not in collection:
            continue

        collection[item_id]["status"] = status
        collection[item_id]["restarts"] = restarts
        collection[item_id]["failed_at"] = failed_at

        if item_type == "node":
            collection[item_id]["requests"] = requests

def save_recovery_state(item_id, item_type, state):
    with sqlite3.connect(DB, timeout=10) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO recovery_state (
                item_id,
                item_type,
                strategy,
                retry_count,
                last_attempt_at,
                next_retry_at,
                consecutive_failures,
                circuit_state,
                circuit_opened_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_id,
            item_type,
            state["strategy"],
            state["retry_count"],
            state["last_attempt_at"],
            state["next_retry_at"],
            state["consecutive_failures"],
            state["circuit_state"],
            state["circuit_opened_at"],
            time.time()
        ))

def persist_recovery_manager(manager):
    for state in manager.get_all_states():
        save_recovery_state(
            state.item_id,
            state.item_type,
            state.to_record()
        )

def load_recovery_manager():
    manager = RecoveryManager()

    with sqlite3.connect(DB, timeout=10) as conn:
        conn.row_factory = sqlite3.Row

        rows = conn.execute("""
            SELECT *
            FROM recovery_state
        """).fetchall()

    for row in rows:
        state = RecoveryState.from_record(dict(row))
        manager.register(state)

    return manager


def load_recovery_state(item_id):
    with sqlite3.connect(DB, timeout=10) as conn:
        conn.row_factory = sqlite3.Row

        row = conn.execute("""
            SELECT *
            FROM recovery_state
            WHERE item_id = ?
        """, (item_id,)).fetchone()

    return dict(row) if row else None

def get_recovery_state(item_id):
    record = load_recovery_state(item_id)

    if record is None:
        return None

    return RecoveryState.from_record(record)

def reset_recovery_state(item_id):
    with sqlite3.connect(DB, timeout=10) as conn:
        conn.execute("""
            DELETE FROM recovery_state
            WHERE item_id = ?
        """, (item_id,))



async def auto_recovery():
    while True:
        # Recover simulated services (existing V1 behaviour)
        recovery_delay = 60

        for service_id, service in services.items():
            if (
                service["status"] == "failed"
                and service["failed_at"] is not None
                and time.time() - service["failed_at"] >= recovery_delay
            ):
                service["status"] = "healthy"
                service["restarts"] += 1
                service["failed_at"] = None

                await async_log_event(
                    service_id,
                    "Automatic recovery successful"
                )
                await async_save_states()

        # RecoveryManager must be initialized during application startup.
        if recovery_manager is None:
            await asyncio.sleep(2)
            continue

        # Strategy-driven Docker node recovery
        for node_id, node in nodes.items():

            async with node_recovery_locks[node_id]:

                actual_status = await asyncio.to_thread(
                    get_docker_node_status,
                    node_id
                )

                recovery_state = recovery_manager.get_state(node_id)

                # Node is healthy: confirm recovery and reset retry state.
                if actual_status == "healthy":

                    if (
                        node["status"] == "failed"
                        or recovery_state.next_retry_at is not None
                        or recovery_state.consecutive_failures > 0
                        or recovery_state.circuit_state != "closed"
                    ):
                        recovery_manager.record_success(node_id)

                        node["status"] = "healthy"
                        node["restarts"] += 1
                        node["failed_at"] = None

                        await async_log_event(
                            node_id,
                            "Docker node recovery verified successfully"
                        )
                        await async_save_states()

                        await asyncio.to_thread(
                            save_recovery_state,
                            node_id,
                            "node",
                            recovery_state.to_record()
                        )

                    continue

                # Detect a new failure.
                if node["status"] != "failed":
                    node["status"] = "failed"
                    node["failed_at"] = time.time()

                    await async_log_event(
                        node_id,
                        "Docker node failure detected"
                    )
                    await async_save_states()

                elif node["failed_at"] is None:
                    node["failed_at"] = time.time()
                    await async_save_states()

                # Schedule the first retry if no retry is pending.
                if recovery_state.next_retry_at is None:
                    next_retry = recovery_manager.schedule_retry(node_id)

                    await asyncio.to_thread(
                        save_recovery_state,
                        node_id,
                        "node",
                        recovery_state.to_record()
                    )

                    if next_retry is None:
                        continue

                # Check retry timing and circuit-breaker permission.
                if not recovery_manager.can_attempt_recovery(node_id):

                    await asyncio.to_thread(
                        save_recovery_state,
                        node_id,
                        "node",
                        recovery_state.to_record()
                    )
                    continue


                recovery_action = None
                recovery_error = None

                async def perform_docker_recovery():
                    nonlocal recovery_action

                    container = await asyncio.to_thread(
                        docker_client.containers.get,
                        NODE_CONTAINER_NAMES[node_id]
                    )

                    await asyncio.to_thread(container.reload)

                    if container.status != "running":
                        await asyncio.to_thread(container.start)
                        recovery_action = "started"
                    else:
                        await asyncio.to_thread(container.restart)
                        recovery_action = "restarted"

                    # Verify actual application health.
                    for attempt in range(10):
                        verified_status = await asyncio.to_thread(
                            get_docker_node_status,
                            node_id
                        )

                        if verified_status == "healthy":
                            return True

                        if attempt < 9:
                            await asyncio.sleep(1)

                    return False

                # Count only attempts authorized by RecoveryManager.
                RECOVERY_ATTEMPTS.labels(node_id).inc()

                # Measure exactly one executor invocation.
                recovery_started_at = time.perf_counter()
                try:
                    recovered = await recovery_executor.execute(
                        perform_docker_recovery
                    )
                except Exception as error:
                    recovered = False
                    recovery_error = error
                finally:
                    RECOVERY_DURATION.labels(node_id).observe(
                        time.perf_counter() - recovery_started_at
                    )

                if recovered:
                    RECOVERY_RESULTS.labels(node_id, "success").inc()
                    recovery_manager.record_success(node_id)

                    node["status"] = "healthy"
                    node["restarts"] += 1
                    node["failed_at"] = None

                else:
                    RECOVERY_RESULTS.labels(node_id, "failure").inc()
                    recovery_manager.record_failure(node_id)
                    recovery_manager.schedule_retry(node_id)

                if recovery_action is not None:
                    await async_log_event(
                        node_id,
                        f"Automatic recovery {recovery_action} attempted"
                    )

                if recovered:
                    await async_log_event(
                        node_id,
                        "Docker node recovery health verification passed"
                    )
                else:
                    failure_detail = (
                        str(recovery_error)
                        if recovery_error is not None
                        else "node health verification unsuccessful"
                    )

                    await async_log_event(
                        node_id,
                        f"Automatic recovery failed: {failure_detail}"
                    )

                # Persist recovery state after every attempt.
                await asyncio.to_thread(
                    save_recovery_state,
                    node_id,
                    "node",
                    recovery_state.to_record()
                )

                await async_save_states()

        await asyncio.sleep(2)



@asynccontextmanager
async def lifespan(app: FastAPI):
    global recovery_manager, experiment_runner, benchmark_runner

    print("STARTUP: Initializing database...", flush=True)
    init_db()
    print("STARTUP: Database initialized.", flush=True)

    print("STARTUP: Loading saved states...", flush=True)
    load_states()
    print("STARTUP: States loaded.", flush=True)

    print("STARTUP: Loading recovery manager...", flush=True)
    recovery_manager = load_recovery_manager()

    # Register configured nodes missing from persisted recovery state.
    for node_id in nodes:
        if recovery_manager.get_state(node_id) is None:
            recovery_manager.register(
                RecoveryState(
                    item_id=node_id,
                    item_type="node"
                )
            )

    # Persist restored and newly registered recovery states.
    await asyncio.to_thread(
        persist_recovery_manager,
        recovery_manager
    )

    print("STARTUP: Recovery manager restored.", flush=True)

    # Initialize experiment repository and runner.
    experiment_repository = ExperimentRepository(DB)

    experiment_runner = ExperimentRunner(
        repository=experiment_repository,
        recovery_manager=recovery_manager,
        inject_failure=inject_node_failure,
        get_node_status=get_docker_node_status,
    )

    benchmark_runner = BenchmarkRunner(
        experiment_runner=experiment_runner
    )

    print("STARTUP: Benchmark runner initialized.", flush=True)

    print("STARTUP: Experiment runner initialized.", flush=True)

    print("STARTUP: Starting recovery task...", flush=True)
    task = asyncio.create_task(auto_recovery())

    print("STARTUP: Application ready.", flush=True)

    try:
        yield

    finally:
        task.cancel()

        try:
            await task
        except asyncio.CancelledError:
            pass

        await async_save_states()

        if recovery_manager is not None:
            await asyncio.to_thread(
                persist_recovery_manager,
                recovery_manager
            )

        experiment_runner = None

        print("SHUTDOWN: Application stopped cleanly.", flush=True)


# FastAPI application must be created AFTER lifespan is defined.
app = FastAPI(
    title="ResilienceLab",
    version="1.0",
    lifespan=lifespan
)

# =========================
# Prometheus Metrics
# =========================

HTTP_REQUESTS = Counter(
    "resiliencelab_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION = Histogram(
    "resiliencelab_http_request_duration_seconds",
    "HTTP request duration in seconds"
)

TOTAL_NODES = Gauge(
    "resiliencelab_total_nodes",
    "Total number of configured nodes"
)

ACTIVE_NODES = Gauge(
    "resiliencelab_active_nodes",
    "Number of healthy nodes"
)

RECOVERY_ATTEMPTS = Counter(
    "resiliencelab_recovery_attempts_total",
    "Authorized Docker node recovery attempts",
    ["node_id"]
)

RECOVERY_RESULTS = Counter(
    "resiliencelab_recovery_results_total",
    "Docker node recovery outcomes",
    ["node_id", "result"]
)

RECOVERY_DURATION = Histogram(
    "resiliencelab_recovery_duration_seconds",
    "Time spent executing a Docker node recovery attempt",
    ["node_id"]
)

RECOVERY_RETRIES = Gauge(
    "resiliencelab_recovery_retries",
    "Current scheduled retry count",
    ["node_id"]
)

RECOVERY_CONSECUTIVE_FAILURES = Gauge(
    "resiliencelab_recovery_consecutive_failures",
    "Current consecutive recovery failures",
    ["node_id"]
)

CIRCUIT_BREAKER_STATE = Gauge(
    "resiliencelab_circuit_breaker_state",
    "Current circuit breaker state (one-hot: closed, open, half_open)",
    ["node_id", "state"]
)


def update_recovery_metrics():
    if recovery_manager is None:
        return

    circuit_states = ("closed", "open", "half_open")

    for state in recovery_manager.get_all_states():
        RECOVERY_RETRIES.labels(state.item_id).set(
            state.retry_count
        )

        RECOVERY_CONSECUTIVE_FAILURES.labels(
            state.item_id
        ).set(state.consecutive_failures)

        for circuit_state in circuit_states:
            CIRCUIT_BREAKER_STATE.labels(
                state.item_id,
                circuit_state
            ).set(
                1 if state.circuit_state == circuit_state else 0
            )



@app.get("/metrics")
async def prometheus_metrics():
    await asyncio.to_thread(get_cluster_health_data)
    update_recovery_metrics()

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.get("/")
def dashboard():
    return FileResponse("static/index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)
@app.middleware("http")
async def track_requests(request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    duration = time.perf_counter() - start_time

    if request.url.path != "/metrics":
        route = request.scope.get("route")
        endpoint = route.path if route else request.url.path

        HTTP_REQUESTS.labels(
            method=request.method,
            endpoint=endpoint,
            status=str(response.status_code)
        ).inc()

        HTTP_REQUEST_DURATION.observe(duration)

    return response

@app.get("/api/health")
def health():
    return {"status": "running", "project": "ResilienceLab"}

@app.get("/api/services")
def get_services():
    return services


@app.post("/api/services/{service_id}/fail")
async def fail_service(service_id: str):
    if service_id not in services:
        raise HTTPException(404, "Service not found")

    service = services[service_id]

    if service["status"] == "failed":
        return {"message": "Service already failed"}

    service["status"] = "failed"
    service["failed_at"] = time.time()

    await async_log_event(
        service_id,
        "Service failure detected"
    )
    await async_save_states()

    return {"message": f"{service['name']} failure detected"}


@app.post("/api/services/{service_id}/recover")
async def recover_service(service_id: str):
    if service_id not in services:
        raise HTTPException(404, "Service not found")

    service = services[service_id]
    service["status"] = "healthy"
    service["failed_at"] = None
    service["restarts"] += 1

    await async_log_event(
        service_id,
        "Manual recovery successful"
    )
    await async_save_states()

    return {"message": f"{service['name']} recovered"}



def get_cluster_health_data():
    statuses = {
        node_id: get_docker_node_status(node_id)
        for node_id in nodes
    }

    total = len(statuses)
    healthy = sum(
        1 for status in statuses.values()
        if status == "healthy"
    )
    failed = total - healthy

    TOTAL_NODES.set(total)
    ACTIVE_NODES.set(healthy)

    return {
        "total_nodes": total,
        "healthy_nodes": healthy,
        "failed_nodes": failed,
        "cluster_status": (
            "healthy" if healthy == total
            else "degraded" if healthy > 0
            else "down"
        )
    }


@app.get("/api/cluster-health")
def cluster_health():
    return get_cluster_health_data()

@app.get("/api/nodes")
def get_nodes():
    result = {}

    for node_id, node in nodes.items():
        actual_status = get_docker_node_status(node_id)

        result[node_id] = {
            "name": node["name"],
            "status": actual_status,
            "requests": node["requests"],
            "failed_at": node["failed_at"],
            "restarts": node["restarts"]
        }

    return result






async def inject_node_failure(node_id: str):
    """Stop a Docker node container and persist its failed state."""

    if node_id not in nodes:
        raise HTTPException(404, "Node not found")

    async with node_recovery_locks[node_id]:

        node = nodes[node_id]
        container_name = NODE_CONTAINER_NAMES[node_id]

        try:
            container = await asyncio.to_thread(
                docker_client.containers.get,
                container_name
            )

            await asyncio.to_thread(container.reload)

            if container.status == "running":
                await asyncio.to_thread(
                    container.stop,
                    timeout=2
                )

            node["status"] = "failed"

            if node["failed_at"] is None:
                node["failed_at"] = time.time()

            await async_log_event(
                node_id,
                "Docker container failure triggered"
            )

            await async_save_states()

            return {
                "message": f"{node_id} Docker container stopped successfully",
                "status": "failed"
            }

        except docker.errors.NotFound:
            node["status"] = "failed"

            if node["failed_at"] is None:
                node["failed_at"] = time.time()

            await async_save_states()

            raise HTTPException(
                404,
                "Docker node container not found"
            )

        except docker.errors.DockerException as error:
            raise HTTPException(
                500,
                f"Docker operation failed: {error}"
            )


@app.post("/api/nodes/{node_id}/fail")
async def fail_node(node_id: str):
    return await inject_node_failure(node_id)




@app.post("/api/nodes/{node_id}/recover")
async def recover_node(node_id: str):

    if node_id not in nodes:
        raise HTTPException(404, "Node not found")

    async with node_recovery_locks[node_id]:

        node = nodes[node_id]

        try:
            container = await asyncio.to_thread(
                docker_client.containers.get,
                NODE_CONTAINER_NAMES[node_id]
            )

            await asyncio.to_thread(container.reload)

            if container.status != "running":
                await asyncio.to_thread(container.start)
            else:
                # Restart a running but unhealthy container
                actual_status = await asyncio.to_thread(
                    get_docker_node_status, node_id
                )

                if actual_status != "healthy":
                    await asyncio.to_thread(container.restart)

            deadline = time.time() + 10

            while time.time() < deadline:

                actual_status = await asyncio.to_thread(
                    get_docker_node_status, node_id
                )

                if actual_status == "healthy":

                    if node["status"] == "failed":
                        node["restarts"] += 1

                    node["status"] = "healthy"
                    node["failed_at"] = None

                    if recovery_manager is not None:
                        recovery_manager.record_success(node_id)

                        recovery_state = recovery_manager.get_state(node_id)

                        await asyncio.to_thread(
                            save_recovery_state,
                            node_id,
                            "node",
                            recovery_state.to_record()
                        )

                    await async_log_event(
                        node_id,
                        "Manual Docker recovery successful"
                    )
                    await async_save_states()

                    return {
                        "message": f"{node_id} recovered successfully",
                        "status": "healthy"
                    }

                await asyncio.sleep(0.5)

            raise HTTPException(
                503,
                "Node recovery timed out"
            )

        except docker.errors.NotFound:
            raise HTTPException(
                404,
                "Docker node container not found"
            )

        except docker.errors.DockerException as error:
            raise HTTPException(
                500,
                f"Docker recovery failed: {error}"
            )





@app.post("/api/route")
async def route_request():
    global rr_index

    async with route_lock:
        node_ids = list(nodes.keys())
        total_nodes = len(node_ids)

        if total_nodes == 0:
            raise HTTPException(503, "No nodes configured")

        for offset in range(total_nodes):
            index = (rr_index + offset) % total_nodes
            selected = node_ids[index]

            async with node_recovery_locks[selected]:

                actual_status = await asyncio.to_thread(
                    get_docker_node_status, selected
                )

                if actual_status != "healthy":
                    node = nodes[selected]

                    if node["status"] != "failed":
                        node["status"] = "failed"
                        node["failed_at"] = time.time()

                        await async_log_event(
                            selected,
                            "Node marked failed during routing health check"
                        )
                        await async_save_states()

                    elif node["failed_at"] is None:
                        node["failed_at"] = time.time()
                        await async_save_states()

                    continue

                node_url = (
                    f"http://{NODE_CONTAINER_NAMES[selected]}:9000/process"
                )

                def send_request():
                    with urllib.request.urlopen(
                        node_url, timeout=3
                    ) as response:
                        return json.loads(
                            response.read().decode("utf-8")
                        )

                try:
                    result = await asyncio.to_thread(send_request)

                    nodes[selected]["requests"] += 1
                    nodes[selected]["status"] = "healthy"
                    nodes[selected]["failed_at"] = None

                    rr_index = (index + 1) % total_nodes

                    await async_log_event(
                        selected,
                        "Request processed successfully"
                    )
                    await async_save_states()

                    return {
                        "message": "Request processed successfully",
                        "selected_node": selected,
                        "node_response": result,
                        "total_requests": nodes[selected]["requests"]
                    }

                except Exception as error:
                    actual_status = await asyncio.to_thread(
                        get_docker_node_status, selected
                    )

                    if actual_status == "healthy":
                        nodes[selected]["status"] = "healthy"
                        nodes[selected]["failed_at"] = None
                    else:
                        nodes[selected]["status"] = "failed"
                        nodes[selected]["failed_at"] = time.time()

                    await async_log_event(
                        selected,
                        f"Request failed: {error}"
                    )
                    await async_save_states()

        raise HTTPException(
            503,
            "No healthy servers available"
        )





@app.get("/api/system")
def system_metrics():
    return {
        "cpu": psutil.cpu_percent(interval=0.3),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "uptime": round(time.time() - psutil.boot_time())
    }

@app.get("/api/logs")
def get_logs():
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM logs ORDER BY id DESC LIMIT 100"
        ).fetchall()
        return [dict(row) for row in rows]


# =========================
# Experiment API
# =========================

@app.post("/api/experiments")
async def create_experiment(request: ExperimentCreateRequest):
    if experiment_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Experiment runner is not initialized"
        )

    try:
        experiment = await experiment_runner.run(
            name=request.name,
            target_node=request.target_node
        )
        return experiment

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )


@app.get("/api/experiments")
async def get_experiments(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    if experiment_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Experiment runner is not initialized"
        )

    return await asyncio.to_thread(
        experiment_runner.repository.list_all,
        limit,
        offset
    )

@app.get("/api/experiments/compare")
async def compare_experiment_results(
    ids: str = Query(...)
):
    if experiment_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Experiment runner is not initialized"
        )

    experiment_ids = [
        item.strip()
        for item in ids.split(",")
        if item.strip()
    ]

    if len(experiment_ids) != len(set(experiment_ids)):
        raise HTTPException(
            status_code=400,
            detail="Duplicate experiment IDs are not allowed"
        )

    if not 2 <= len(experiment_ids) <= 10:
        raise HTTPException(
            status_code=400,
            detail="Provide between 2 and 10 experiment IDs"
        )

    experiments = []

    for experiment_id in experiment_ids:
        experiment = await asyncio.to_thread(
            experiment_runner.repository.get,
            experiment_id
        )

        if experiment is None:
            raise HTTPException(
                status_code=404,
                detail=f"Experiment not found: {experiment_id}"
            )

        experiments.append(experiment)

    return compare_experiments(experiments)


@app.get("/api/experiments/{experiment_id}")
async def get_experiment(experiment_id: str):
    if experiment_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Experiment runner is not initialized"
        )

    experiment = await asyncio.to_thread(
        experiment_runner.repository.get,
        experiment_id
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found"
        )

    return experiment

@app.get("/api/experiments/{experiment_id}/report")
async def get_experiment_report(experiment_id: str):
    if experiment_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Experiment runner is not initialized"
        )

    experiment = await asyncio.to_thread(
        experiment_runner.repository.get,
        experiment_id
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found"
        )

    return build_experiment_report(experiment)

@app.get("/api/experiments/groups/{run_group_id}/report")
async def get_benchmark_report(run_group_id: str):
    if experiment_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Experiment runner is not initialized"
        )

    experiments = await asyncio.to_thread(
        experiment_runner.repository.list_by_group,
        run_group_id
    )

    if not experiments:
        raise HTTPException(
            status_code=404,
            detail="Benchmark group not found"
        )

    return build_benchmark_report(
        run_group_id,
        experiments
    )

# =========================
# Benchmark API
# =========================

@app.post("/api/experiments/benchmark")
async def create_benchmark(request: BenchmarkCreateRequest):
    if benchmark_runner is None:
        raise HTTPException(
            status_code=503,
            detail="Benchmark runner is not initialized"
        )

    try:
        return await benchmark_runner.run(
            name=request.name,
            target_node=request.target_node,
            trials=request.trials
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=409,
            detail=str(error)
        )
