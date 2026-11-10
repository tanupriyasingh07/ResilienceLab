
from fastapi import FastAPI
import os
import time

app = FastAPI(title="ResilienceLab Node")

NODE_ID = os.getenv("NODE_ID", "node-1")
START_TIME = time.time()
REQUEST_COUNT = 0

@app.get("/health")
def health():
    return {
        "node_id": NODE_ID,
        "status": "healthy",
        "uptime": round(time.time() - START_TIME),
        "requests": REQUEST_COUNT
    }

@app.get("/process")
def process_request():
    global REQUEST_COUNT
    REQUEST_COUNT += 1

    return {
        "message": "Request processed successfully",
        "node_id": NODE_ID,
        "total_requests": REQUEST_COUNT
    }
