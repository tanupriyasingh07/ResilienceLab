
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import psutil
import sqlite3
import asyncio
import time
from datetime import datetime
from fastapi.responses import FileResponse

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
    while True:
        for service_id, service in services.items():
            if service["status"] == "failed":
                if time.time() - service["failed_at"] >= 10:
                    service["status"] = "healthy"
                    service["restarts"] += 1
                    service["failed_at"] = None
                    log_event(service_id, "Automatic recovery successful")
                    save_states()

        for node_id, node in nodes.items():
            if node["status"] == "failed":
                if node["failed_at"] is not None and time.time() - node["failed_at"] >= 10:
                    node["status"] = "healthy"
                    node["restarts"] += 1
                    node["failed_at"] = None
                    log_event(node_id, "Automatic node recovery successful")
                    save_states()

        await asyncio.sleep(2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    load_states()
    task = asyncio.create_task(auto_recovery())
    yield
    save_states()
    task.cancel()

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
    total = len(nodes)
    healthy = sum(
        1 for node in nodes.values()
        if node["status"] == "healthy"
    )
    failed = total - healthy

    return {
        "total_nodes": total,
        "healthy_nodes": healthy,
        "failed_nodes": failed,
        "cluster_status": "healthy" if healthy == total else
                          "degraded" if healthy > 0 else "down"
    }

@app.get("/api/nodes")
def get_nodes():
    return nodes


@app.post("/api/nodes/{node_id}/fail")
def fail_node(node_id: str):
    if node_id not in nodes:
        raise HTTPException(404, "Node not found")

    node = nodes[node_id]

    if node["status"] == "failed":
        return {"message": "Node already failed"}

    node["status"] = "failed"
    node["failed_at"] = time.time()
    log_event(node_id, "Node failure detected")
    save_states()

    return {"message": f"{node_id} marked as failed"}


@app.post("/api/nodes/{node_id}/recover")
def recover_node(node_id: str):
    if node_id not in nodes:
        raise HTTPException(404, "Node not found")

    node = nodes[node_id]
    node["status"] = "healthy"
    node["failed_at"] = None
    node["restarts"] += 1

    log_event(node_id, "Manual recovery successful")
    save_states()

    return {"message": f"{node_id} recovered successfully"}


@app.post("/api/route")
def route_request():
    global rr_index

    healthy_nodes = [
        node_id for node_id, node in nodes.items()
        if node["status"] == "healthy"
    ]

    if not healthy_nodes:
        raise HTTPException(503, "No healthy servers available")

    selected = healthy_nodes[rr_index % len(healthy_nodes)]
    rr_index += 1

    nodes[selected]["requests"] += 1

    log_event(selected, "Request routed successfully")

    return {
        "message": "Request routed successfully",
        "selected_node": selected,
        "total_requests": nodes[selected]["requests"]
    }

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
