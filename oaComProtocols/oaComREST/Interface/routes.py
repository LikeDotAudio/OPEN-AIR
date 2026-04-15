# oaComProtocols.oaComREST/Interface/routes.py
# Author: Anthony Peter Kuzub
# Version: 20260414.1000.1
#
# Description: Dynamic API routes with an interactive HTML Tree Explorer.

import sys
sys.path.insert(0, '/home/anthony/Documents/OPEN-AIR')

try:
    from fastapi import APIRouter, HTTPException, Path, Body, Request
    from fastapi.responses import HTMLResponse, JSONResponse
except ImportError:
    pass

from typing import Any, Dict, List
from ..Constants.rest_constants import LOCAL_DEBUG
from loguru import logger
from oaComBroker.Core.protocol_router.router import ProtocolRouter # Import ProtocolRouter

def create_router(state_cache_manager, protocol_router):
    """
    Creates dynamic routes that mirror the system's MQTT topic tree.
    Includes a Visual Tree Explorer for human interaction.
    """
    router = APIRouter()

    def get_children(prefix: str) -> List[str]:
        """Helper to find immediate sub-topics/children for a given prefix."""
        if prefix and not prefix.endswith('/'): prefix += '/'
        
        children = set()
        for topic in state_cache_manager.rust_cache.keys():
            if topic.startswith(prefix):
                relative = topic[len(prefix):]
                parts = relative.split('/')
                if parts[0]:
                    children.add(parts[0])
        return sorted(list(children))

    @router.get("/", response_class=HTMLResponse)
    async def root_explorer(request: Request):
        """Interactive HTML Tree Explorer for the OPEN-AIR System."""
        
        # If client wants JSON (e.g. scripts), give them the raw root data
        if "text/html" not in request.headers.get("Accept", ""):
            roots = set()
            for topic in state_cache_manager.rust_cache.keys():
                roots.add(topic.split('/')[0])
            return JSONResponse({
                "system": "OPEN-AIR",
                "root_namespaces": sorted(list(roots)),
                "links": {"docs": "/docs", "explorer": "/"}
            })

        # Generate HTML Explorer
        roots = sorted(list(set(topic.split('/')[0] for topic in state_cache_manager.rust_cache.keys())))
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>OPEN-AIR | API Explorer</title>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #1a1a1a; color: #dcdcdc; margin: 0; padding: 20px; }}
                .container {{ max-width: 900px; margin: auto; background: #2b2b2b; padding: 30px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
                h1 {{ color: #f4902c; border-bottom: 1px solid #444; padding-bottom: 10px; display: flex; align-items: center; }}
                .nav-bar {{ margin-bottom: 20px; display: flex; gap: 10px; }}
                .btn {{ background: #444; color: #fff; padding: 8px 15px; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: bold; border: 1px solid #555; }}
                .btn:hover {{ background: #555; border-color: #f4902c; }}
                .btn-primary {{ background: #f4902c; color: #1a1a1a; }}
                .tree-node {{ margin-left: 20px; border-left: 1px solid #444; padding-left: 15px; margin-top: 5px; }}
                .folder {{ font-weight: bold; color: #33A1FD; cursor: pointer; }}
                .leaf {{ color: #6a9955; }}
                .topic-link {{ text-decoration: none; color: inherit; }}
                .topic-Shover {{ text-decoration: underline; }}
                .meta {{ font-size: 11px; color: #888; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌐 OPEN-AIR SYSTEM EXPLORER</h1>
                <div class="nav-bar">
                    <a href="/" class="btn btn-primary">🏠 ROOT INDEX</a>
                    <a href="/docs" class="btn">📚 API DOCS (SWAGGER)</a>
                    <a href="/api/v1/system/status" class="btn">🚦 SYSTEM STATUS</a>
                </div>
                <p>Browsing the live MQTT Topic Tree. Click any folder to descend or a leaf to see data.</p>
                
                <div class="tree-root">
                    <strong>/ (Root)</strong>
                    {"".join([f'<div class="tree-node"><span class="folder">📁</span> <a class="topic-link folder" href="/{r}">{r}</a></div>' for r in roots])}
                </div>
                
                <div style="margin-top: 40px; font-size: 10px; color: #555; text-align: center; border-top: 1px solid #333; padding-top: 10px;">
                    OPEN-AIR PARTITIONED ARCHITECTURE | REST-TO-MQTT BRIDGE v1.0
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    @router.get("/api/v1/system/status")
    async def get_system_status():

            # from oaComBroker.Core.protocol_router.manager import ProtocolRouter
            router_inst = ProtocolRouter.get_instance()
            active = router_inst.protocols if router_inst else ["MQTT", "REST"] # Fallback if router not found
            return {
                "status": "operational", 
                "partition": "CORE", 
                "active_protocols": active,
                "instance_id": getattr(router_inst, "GUID", "UNKNOWN")
            }

    @router.get("/api/v1/system/tree")
    async def get_full_tree():
        """Returns the entire system state as a single JSON object."""
        try:
            # ⚡ PERFORMANCE: Directly retrieve the Rust cache items
            return state_cache_manager.rust_cache.to_dict()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to retrieve tree: {e}")

    @router.get("/{topic_path:path}")
    async def dynamic_get(request: Request, topic_path: str = Path(..., description="The MQTT topic path")):
        """
        Dynamic Resolver:
        - If LEAF: Returns data (JSON or HTML view).
        - If FOLDER: Returns children (JSON or HTML Tree).
        """
        is_html = "text/html" in request.headers.get("Accept", "")
        
        # 1. Check for Exact Match (Leaf Node)
        value = state_cache_manager.get_cached_value(topic_path)
        if value is not None:
            if not is_html:
                return {"type": "leaf", "topic": topic_path, "value": value}
            
            # Simple HTML Leaf View
            return HTMLResponse(f"""
                <body style="background:#1a1a1a; color:#dcdcdc; font-family:sans-serif; padding:40px;">
                    <div style="max-width:600px; margin:auto; background:#2b2b2b; padding:20px; border-radius:8px; border-left: 5px solid #6a9955;">
                        <h2 style="color:#6a9955;">🍃 LEAF TOPIC</h2>
                        <code style="display:block; background:#111; padding:15px; color:#f4902c; font-size:1.2em;">{topic_path}</code>
                        <hr style="border:0; border-top:1px solid #444; margin:20px 0;">
                        <pre style="font-size:1.5em; color:#fff;">{value}</pre>
                        <a href="/{topic_path.rsplit('/', 1)[0] if '/' in topic_path else ''}" style="color:#33A1FD; text-decoration:none;">⬅️ Back to folder</a>
                    </div>
                </body>
            """)

        # 2. Check for Prefix (Folder Node)
        if state_cache_manager.check_prefix_exists(topic_path):
            children = get_children(topic_path)
            if not is_html:
                return {
                    "type": "folder",
                    "path": topic_path,
                    "children": children,
                    "child_urls": [f"/{topic_path.rstrip('/')}/{c}" for c in children]
                }

            # HTML Folder View
            child_html = "".join([f'<div style="margin:10px 0; padding-left:20px; border-left:1px solid #444;">📁 <a href="/{topic_path.rstrip("/")}/{c}" style="color:#33A1FD; text-decoration:none; font-weight:bold;">{c}</a></div>' for c in children])
            return HTMLResponse(f"""
                <body style="background:#1a1a1a; color:#dcdcdc; font-family:sans-serif; padding:40px;">
                    <div style="max-width:800px; margin:auto; background:#2b2b2b; padding:20px; border-radius:8px; border-left: 5px solid #33A1FD;">
                        <h2 style="color:#33A1FD;">📂 FOLDER: {topic_path}</h2>
                        <div style="margin:20px 0;">
                            <a href="/{topic_path.rsplit('/', 1)[0] if '/' in topic_path else ''}" style="background:#444; color:#fff; padding:5px 10px; text-decoration:none; border-radius:4px; font-size:12px;">⬆️ LEVEL UP</a>
                            <a href="/" style="background:#444; color:#fff; padding:5px 10px; text-decoration:none; border-radius:4px; font-size:12px; margin-left:10px;">🏠 ROOT</a>
                        </div>
                        <div style="background:#111; padding:15px; border-radius:4px;">
                            {child_html if children else "<i>Empty Namespace</i>"}
                        </div>
                    </div>
                </body>
            """)

        raise HTTPException(status_code=404, detail=f"Path '{topic_path}' not found.")

    @router.post("/{topic_path:path}")
    async def dynamic_post(topic_path: str = Path(...), payload: Any = Body(...)):
        value = payload.get("value", payload) if isinstance(payload, dict) else payload
        protocol_router.ingest(transport_source="REST", topic=topic_path, value=value)
        return {"status": "success", "topic": topic_path, "value": value}

    return router
