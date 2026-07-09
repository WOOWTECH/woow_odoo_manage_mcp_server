"""Connection configuration router for ivnvxd/mcp-server-odoo.

Manages Odoo connection settings. Key differences from tuanle96:
- Uses ODOO_USER (not ODOO_USERNAME)
- Supports ODOO_API_KEY for Phase 2 standard mode
- Supports ODOO_YOLO for Phase 1 read-only mode

Endpoints:
    GET  /api/config            - Current connection config
    PUT  /api/config/connection  - Update connection credentials
    POST /api/config/test        - Test XML-RPC connectivity
"""

from __future__ import annotations

import logging
import xmlrpc.client
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from mcp_admin_core.config import get_config_store
from mcp_admin_core.process import get_process_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/config", tags=["config"])


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ConnectionConfig(BaseModel):
    odoo_url: str = ""
    odoo_db: str = ""
    odoo_user: str = ""
    odoo_api_key_masked: str = "********"
    odoo_yolo: str = "off"


class ConnectionUpdateRequest(BaseModel):
    odoo_url: str = Field(..., description="Odoo instance URL")
    odoo_db: str = Field(..., description="Database name")
    odoo_user: str = Field(..., description="Odoo username (required for XML-RPC uid)")
    odoo_api_key: str = Field(default="", description="API key (Phase 2 standard mode)")
    odoo_password: str = Field(default="", description="Password (Phase 1 YOLO mode)")
    odoo_yolo: str = Field(default="off", description="YOLO mode: off, read, or true")
    restart: bool = Field(default=True, description="Restart MCP server after update")


class ConnectionUpdateResponse(BaseModel):
    success: bool
    message: str
    restarted: bool = False


class ConnectionTestRequest(BaseModel):
    odoo_url: str
    odoo_db: str
    odoo_user: str
    odoo_api_key: str = ""
    odoo_password: str = ""


class ConnectionTestResponse(BaseModel):
    success: bool
    message: str
    uid: int | None = None
    server_version: str | None = None
    details: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mask(s: str) -> str:
    if not s or len(s) <= 2:
        return "****" if s else "(not set)"
    return f"{s[:8]}{'*' * max(0, len(s) - 12)}{s[-4:]}" if len(s) > 12 else f"{s[:4]}****"


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ConnectionConfig)
async def get_config() -> ConnectionConfig:
    """Return current connection config (sensitive fields masked)."""
    store = get_config_store()
    conn = await store.get("connection", {})
    api_key = conn.get("odoo_api_key", "")
    return ConnectionConfig(
        odoo_url=conn.get("odoo_url", ""),
        odoo_db=conn.get("odoo_db", ""),
        odoo_user=conn.get("odoo_user", ""),
        odoo_api_key_masked=_mask(api_key),
        odoo_yolo=conn.get("odoo_yolo", "off"),
    )


@router.put("/connection", response_model=ConnectionUpdateResponse)
async def update_connection(req: ConnectionUpdateRequest) -> ConnectionUpdateResponse:
    """Update connection credentials and optionally restart MCP server."""
    store = get_config_store()
    update_data: dict[str, Any] = {
        "odoo_url": req.odoo_url,
        "odoo_db": req.odoo_db,
        "odoo_user": req.odoo_user,
        "odoo_yolo": req.odoo_yolo,
    }
    if req.odoo_api_key:
        update_data["odoo_api_key"] = req.odoo_api_key
    if req.odoo_password:
        update_data["odoo_password"] = req.odoo_password

    await store.patch("connection", update_data)
    logger.info("Updated ivnvxd connection config")

    restarted = False
    if req.restart:
        pm = get_process_manager()
        if pm.is_running:
            await pm.restart()
            restarted = True

    return ConnectionUpdateResponse(
        success=True,
        message="Connection credentials updated",
        restarted=restarted,
    )


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(req: ConnectionTestRequest) -> ConnectionTestResponse:
    """Test XML-RPC connectivity to Odoo."""
    url = req.odoo_url.rstrip("/")
    password = req.odoo_api_key or req.odoo_password

    if not password:
        return ConnectionTestResponse(success=False, message="No API key or password provided")

    try:
        common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
        version_info = common.version()
    except Exception as exc:
        return ConnectionTestResponse(success=False, message=f"Cannot reach Odoo: {exc}")

    server_version = version_info.get("server_version", "unknown") if isinstance(version_info, dict) else str(version_info)

    try:
        try:
            result = common.authenticate(
                req.odoo_db,
                {"login": req.odoo_user, "password": password, "type": "password"},
                {},
            )
            uid = result.get("uid") if isinstance(result, dict) else result
        except (xmlrpc.client.Fault, TypeError):
            result = common.authenticate(req.odoo_db, req.odoo_user, password, {})
            uid = result.get("uid") if isinstance(result, dict) else result
    except xmlrpc.client.Fault as fault:
        return ConnectionTestResponse(success=False, message=f"XML-RPC fault: {fault.faultString}", server_version=server_version)
    except Exception as exc:
        return ConnectionTestResponse(success=False, message=f"Auth failed: {exc}", server_version=server_version)

    if not uid:
        return ConnectionTestResponse(success=False, message="Invalid credentials (uid=False)", server_version=server_version)

    return ConnectionTestResponse(
        success=True,
        message=f"Authenticated as UID {uid}",
        uid=uid,
        server_version=server_version,
        details={"database": req.odoo_db, "user": req.odoo_user},
    )
