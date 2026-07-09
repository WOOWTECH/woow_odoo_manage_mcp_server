"""Health dashboard router for ivnvxd/mcp-server-odoo.

Key difference from tuanle96 version: ivnvxd has a native /health
endpoint at port 8000 that returns JSON health status, so we can
check it directly instead of relying solely on process manager status.

Endpoints:
    GET /api/health - Dashboard health data
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter

from mcp_admin_core.config import get_config_store
from mcp_admin_core.process import get_process_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health", tags=["health"])


async def _check_odoo(odoo_url: str) -> dict[str, Any]:
    """Check Odoo health via /web/health."""
    if not odoo_url:
        return {"healthy": False, "url": "", "error": "Not configured"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{odoo_url.rstrip('/')}/web/health")
            return {"healthy": resp.status_code == 200, "url": odoo_url, "status_code": resp.status_code}
    except httpx.ConnectError:
        return {"healthy": False, "url": odoo_url, "error": "Connection refused"}
    except httpx.TimeoutException:
        return {"healthy": False, "url": odoo_url, "error": "Timed out"}
    except Exception as exc:
        return {"healthy": False, "url": odoo_url, "error": str(exc)}


async def _check_mcp_health(mcp_port: int) -> dict[str, Any]:
    """Check ivnvxd's native /health endpoint.

    ivnvxd uses lazy-connect: /health returns {"status":"unhealthy"}
    until the first MCP request triggers Odoo authentication.
    We treat "responding at all" as healthy (server is ready to accept
    MCP connections). The "connected" field tracks Odoo auth state separately.
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"http://127.0.0.1:{mcp_port}/health")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "healthy": True,  # Server is responding = healthy
                    "version": data.get("version", "unknown"),
                    "connected": data.get("connection", {}).get("connected", False),
                }
            return {"healthy": False, "version": "unknown", "connected": False}
    except Exception:
        return {"healthy": False, "version": "unknown", "connected": False}


async def _get_odoo_info(odoo_url: str, db: str, user: str, api_key: str) -> dict[str, Any]:
    """Get Odoo version and module count via XML-RPC."""
    info: dict[str, Any] = {"version": None, "db_name": db, "item_count": None}
    if not odoo_url or not user:
        return info
    password = api_key
    if not password:
        return info
    try:
        import xmlrpc.client

        common = xmlrpc.client.ServerProxy(f"{odoo_url.rstrip('/')}/xmlrpc/2/common", allow_none=True)
        ver = common.version()
        info["version"] = ver.get("server_version", "unknown") if isinstance(ver, dict) else str(ver)

        try:
            result = common.authenticate(db, {"login": user, "password": password, "type": "password"}, {})
        except (xmlrpc.client.Fault, TypeError):
            result = common.authenticate(db, user, password, {})
        uid = result.get("uid") if isinstance(result, dict) else result
        if uid:
            models = xmlrpc.client.ServerProxy(f"{odoo_url.rstrip('/')}/xmlrpc/2/object", allow_none=True)
            count = models.execute_kw(db, uid, password, "ir.module.module", "search_count", [[["state", "=", "installed"]]])
            info["item_count"] = count
    except Exception as exc:
        logger.debug("Failed to get Odoo info: %s", exc)
    return info


@router.get("")
async def get_health() -> dict[str, Any]:
    """Return health data for the Dashboard frontend."""
    store = get_config_store()
    pm = get_process_manager()

    conn = await store.get("connection", {})
    odoo_url = conn.get("odoo_url", "")
    mcp_cfg = await store.get("mcp_server", {})
    mcp_port = mcp_cfg.get("port", 8000)

    pm_status = await pm.status()

    # ivnvxd-specific: check native /health endpoint
    mcp_health = await _check_mcp_health(mcp_port)
    mcp_running = pm_status.get("running", False)
    mcp_server = {
        "healthy": mcp_running and mcp_health.get("healthy", False),
        "pod_name": f"pid={pm_status.get('pid')}" if mcp_running else "stopped",
        "restart_count": pm_status.get("restart_count", 0),
        "ivnvxd_version": mcp_health.get("version", "unknown"),
        "odoo_connected": mcp_health.get("connected", False),
    }

    target_app = await _check_odoo(odoo_url)
    proxy = {"healthy": True, "pod_name": "built-in reverse proxy"}

    odoo_info = await _get_odoo_info(
        odoo_url,
        conn.get("odoo_db", ""),
        conn.get("odoo_user", ""),
        conn.get("odoo_api_key", "") or conn.get("odoo_password", ""),
    )

    all_healthy = mcp_server["healthy"] and target_app.get("healthy", False)

    return {
        "app_type": "odoo-ivnvxd",
        "overall_status": "ok" if all_healthy else "degraded" if mcp_running or target_app.get("healthy") else "error",
        "mcp_server": mcp_server,
        "target_app": target_app,
        "proxy": proxy,
        "version": odoo_info.get("version"),
        "db_name": odoo_info.get("db_name"),
        "item_count": odoo_info.get("item_count"),
        "namespace": "k3s",
    }
