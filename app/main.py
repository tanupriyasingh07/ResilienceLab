
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
docker_client = docker.from_env()


NODE_CONTAINER_NAMES = {
    "node-1": "resiliencelab-node-1",
    "node-2": "resiliencelab-node-2",
    "node-3": "resiliencelab-node-3"
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
    with sqlite3.connect(DB) as conn:

        # Create event logs table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT,
                event TEXT,
                timestamp TEXT
            )
        """)

        # Create system state table
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

        # Update existing database if failed_at is missing
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


def save_states():
    with sqlite3.connect(DB) as conn:

        # Save services
        for item_id, item in services.items():
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
        for item_id, item in nodes.items():
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



def load_states():
    with sqlite3.connect(DB) as conn:
        rows = conn.execute("""
            SELECT item_id, item_type, status, restarts, requests, failed_at
            FROM system_state
        """).fetchall()

    for item_id, item_type, status, restarts, requests, failed_at in rows:
        collection = services if item_type == "service" else nodes

        if item_id in collection:
            collection[item_id]["status"] = status
            collection[item_id]["restarts"] = restarts
            collection[item_id]["failed_at"] = failed_at

            if item_type == "node":
                collection[item_id]["requests"] = requests






async def auto_recovery():
    recovery_delay = 60

    while True:
        # Recover simulated services
        for service_id, service in services.items():
            if (
                service["status"] == "failed"
                and service["failed_at"] is not None
                and time.time() - service["failed_at"] >= recovery_delay
            ):
                service["status"] = "healthy"
                service["restarts"] += 1
                service["failed_at"] = None

                log_event(service_id, "Automatic recovery successful")
                save_states()

        # Monitor Docker nodes
        for node_id, node in nodes.items():
            actual_status = await asyncio.to_thread(
                get_docker_node_status, node_id
            )

            if actual_status == "healthy":
                if node["status"] == "failed":
                    node["status"] = "healthy"
                    node["restarts"] += 1
                    node["failed_at"] = None

                    log_event(
                        node_id,
                        "Docker node automatic recovery successful"
                    )
                    save_states()

                elif node["failed_at"] is not None:
                    node["failed_at"] = None
                    save_states()

                continue

            # Detect failure
            if node["status"] != "failed":
                node["status"] = "failed"
                node["failed_at"] = time.time()

                log_event(node_id, "Docker node failure detected")
                save_states()
                continue

            if node["failed_at"] is None:
                node["failed_at"] = time.time()
                save_states()
                continue

            # Restart after recovery delay
            if time.time() - node["failed_at"] >= recovery_delay:
                try:
                    container = await asyncio.to_thread(
                        docker_client.containers.get,
                        NODE_CONTAINER_NAMES[node_id]
                    )

                    await asyncio.to_thread(container.reload)

                    if container.status != "running":
                        await asyncio.to_thread(container.start)

                except docker.errors.DockerException as error:
                    log_event(
                        node_id,
                        f"Automatic recovery failed: {error}"
                    )

        await asyncio.sleep(2)




@asynccontextmanager
async def lifespan(app: FastAPI):
    print("STARTUP: Initializing database...", flush=True)
    init_db()
    print("STARTUP: Database initialized.", flush=True)

    print("STARTUP: Loading saved states...", flush=True)
    load_states()
    print("STARTUP: States loaded.", flush=True)

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

        save_states()
        print("SHUTDOWN: Application stopped cleanly.", flush=True)


app = FastAPI(title="ResilienceLab", version="1.0", lifespan=lifespan)
@app.get("/")
def dashboard():
    return FileResponse("static/index.html")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/api/health")
def health():
    return {"status": "running", "project": "ResilienceLab"}

@app.get("/api/services")
def get_services():
    return services

@app.post("/api/services/{service_id}/fail")
def fail_service(service_id: str):
    if service_id not in services:
        raise HTTPException(404, "Service not found")

    service = services[service_id]

    if service["status"] == "failed":
        return {"message": "Service already failed"}

    service["status"] = "failed"
    service["failed_at"] = time.time()
    log_event(service_id, "Service failure detected")
    save_states()

    return {"message": f"{service['name']} failure detected"}

@app.post("/api/services/{service_id}/recover")
def recover_service(service_id: str):
    if service_id not in services:
        raise HTTPException(404, "Service not found")

    service = services[service_id]
    service["status"] = "healthy"
    service["failed_at"] = None
    service["restarts"] += 1

    log_event(service_id, "Manual recovery successful")
    save_states()

    return {"message": f"{service['name']} recovered"}


@app.get("/api/cluster-health")
def cluster_health():
    statuses = {
        node_id: get_docker_node_status(node_id)
        for node_id in nodes
    }

    total = len(statuses)
    healthy = sum(1 for status in statuses.values() if status == "healthy")
    failed = total - healthy

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




@app.post("/api/nodes/{node_id}/fail")
def fail_node(node_id: str):
    if node_id not in nodes:
        raise HTTPException(404, "Node not found")

    node = nodes[node_id]
    container_name = NODE_CONTAINER_NAMES[node_id]

    try:
        container = docker_client.containers.get(container_name)
        container.reload()

        if container.status == "running":
            container.stop(timeout=2)

        node["status"] = "failed"
        if node["failed_at"] is None:
            node["failed_at"] = time.time()

        log_event(node_id, "Docker container failure triggered")
        save_states()

        return {
            "message": f"{node_id} Docker container stopped successfully",
            "status": "failed"
        }

    except docker.errors.NotFound:
        node["status"] = "failed"
        if node["failed_at"] is None:
            node["failed_at"] = time.time()
        save_states()
        raise HTTPException(404, "Docker node container not found")

    except docker.errors.DockerException as error:
        raise HTTPException(500, f"Docker operation failed: {error}")



@app.post("/api/nodes/{node_id}/recover")
async def recover_node(node_id: str):
    if node_id not in nodes:
        raise HTTPException(404, "Node not found")

    node = nodes[node_id]

    try:
        container = await asyncio.to_thread(
            docker_client.containers.get,
            NODE_CONTAINER_NAMES[node_id]
        )

        await asyncio.to_thread(container.reload)

        if container.status != "running":
            await asyncio.to_thread(container.start)

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

                log_event(node_id, "Manual Docker recovery successful")
                save_states()

                return {
                    "message": f"{node_id} recovered successfully",
                    "status": "healthy"
                }

            await asyncio.sleep(0.5)

        raise HTTPException(
            503,
            f"{node_id} health check failed after restart"
        )

    except docker.errors.NotFound:
        raise HTTPException(404, "Docker node container not found")

    except docker.errors.DockerException as error:
        raise HTTPException(500, f"Docker operation failed: {error}")



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

            actual_status = await asyncio.to_thread(
                get_docker_node_status, selected
            )

            if actual_status != "healthy":
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

                log_event(selected, "Request processed successfully")
                save_states()

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

                log_event(selected, f"Request failed: {error}")
                save_states()

        raise HTTPException(
            503,
            "No healthy servers available to process the request"
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
