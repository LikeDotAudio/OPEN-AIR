# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260414.1200.1
#
# Description: NMOS Connection & Node API using FastAPI.
# ⚡ STANDALONE: Includes IS-07 WebSocket server support.

import json
import asyncio
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import JSONResponse, Response
import uvicorn

from oaComProtocols.oaComNmos.Core.utils import now_ts, get_ip
from oaComProtocols.oaComNmos.Core.sdp_parser import parse_sdp
from oaComProtocols.oaComNmos.Constants import settings
from oaLogging.Methods.matrix_gate import matrix_log

# --- Shared State (Populated by Orchestrator) ---
STATE = {
    "NODE": {},
    "DEVICE": {},
    "SOURCES": {},
    "FLOWS": {},
    "SENDERS": {},
    "STREAMS": {}
}

app = FastAPI(title="OPEN-AIR NMOS API")

# --- Helper Functions ---

def build_connection_active(sender_id: str) -> Optional[Dict[str, Any]]:
    sender_resource = STATE["SENDERS"].get(sender_id)
    if not sender_resource:
        return None

    stream_data = next((s for s in STATE["STREAMS"].values() if s.get("sender_id") == sender_id), None)
    if not stream_data:
        return None

    sdp_content = stream_data.get("sdp")
    if not sdp_content:
        return None

    parsed_sdp = parse_sdp(sdp_content)
    destination_ip = parsed_sdp.get("ip")

    return {
        "activation": {
            "activation_time": now_ts(),
            "mode": None,
            "requested_time": None
        },
        "master_enable": True,
        "receiver_id": None,
        "transport_params": [{
            "destination_port": parsed_sdp.get("port", 5004),
            "source_port": parsed_sdp.get("port", 5004),
            "source_ip": parsed_sdp.get("src_ip", get_ip()),
            "destination_ip": destination_ip,
            "rtp_enabled": True
        }]
    }

# --- NMOS Node API ---

@app.get("/x-nmos/node/v1.3")
async def node_base():
    return ["self", "devices", "sources", "flows", "senders"]

@app.get("/x-nmos/node/v1.3/self")
async def node_self():
    return STATE["NODE"]

@app.get("/x-nmos/node/v1.3/devices")
async def node_devices():
    return [STATE["DEVICE"]] if STATE["DEVICE"] else []

@app.get("/x-nmos/node/v1.3/sources")
async def node_sources():
    return list(STATE["SOURCES"].values())

@app.get("/x-nmos/node/v1.3/flows")
async def node_flows():
    return list(STATE["FLOWS"].values())

@app.get("/x-nmos/node/v1.3/senders")
async def node_senders():
    return list(STATE["SENDERS"].values())

# --- NMOS Connection API ---

@app.get("/x-nmos/connection/v1.1/single/senders")
async def connection_senders():
    return list(STATE["SENDERS"].keys())

@app.get("/x-nmos/connection/v1.1/single/senders/{sender_id}/active")
async def connection_active(sender_id: str):
    data = build_connection_active(sender_id)
    if data:
        return data
    raise HTTPException(status_code=404, detail="Sender or stream not found")

@app.get("/x-nmos/connection/v1.1/single/senders/{sender_id}/transportfile")
async def connection_transportfile(sender_id: str):
    stream_data = next((s for s in STATE["STREAMS"].values() if s.get("sender_id") == sender_id), None)
    if stream_data and stream_data.get("sdp"):
        return Response(content=stream_data["sdp"], media_type="application/sdp")
    raise HTTPException(status_code=404, detail="Transport file not found")

@app.get("/x-manifest/senders/{sender_id}/manifest")
async def manifest_sender(sender_id: str):
    stream_data = next((s for s in STATE["STREAMS"].values() if s.get("sender_id") == sender_id), None)
    if stream_data and stream_data.get("sdp"):
        return Response(content=stream_data["sdp"], media_type="application/sdp")
    raise HTTPException(status_code=404, detail="Manifest not found")

# --- IS-07 WebSocket Server ---

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        matrix_log("comms", "is07_ws", "connect", f"📡✅ [IS07-WS] Client connected. Total: {len(self.active_connections)}", "SUCCESS")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            matrix_log("comms", "is07_ws", "disconnect", f"📡 [IS07-WS] Client disconnected. Remaining: {len(self.active_connections)}", "INFO")

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"[IS07-WS] Error broadcasting to client: {e}")

manager = ConnectionManager()

@app.websocket("/is07")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming IS-07 commands here if needed
            # For now, we just log and potentially echo or broadcast
            matrix_log("comms", "is07_ws", "receive", f"📡📥 [IS07-WS] Received: {data[:100]}", "DEBUG")
            
            # Simple Echo for testing
            # await websocket.send_text(f"Message received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        matrix_log("comms", "is07_ws", "error", f"📡❌ [IS07-WS] WebSocket Error: {e}", "ERROR")
        manager.disconnect(websocket)

# --- Server Management ---

def run_server(host="0.0.0.0", port=settings.PORT):
    """Starts the NMOS API and IS-07 WebSocket server using uvicorn."""
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server = uvicorn.Server(config)
    
    matrix_log("comms", "nmos_api", "run", f"🚀 [NMOS-API] Starting FastAPI server on {host}:{port}", "INFO")
    
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(server.serve())
    except RuntimeError:
        asyncio.run(server.serve())

if __name__ == "__main__":
    run_server()
