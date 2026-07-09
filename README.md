<p align="center">
  <img src="https://img.shields.io/badge/ivnvxd-MCP_Admin-22c55e?style=for-the-badge" alt="ivnvxd MCP Admin"/>
</p>

<h1 align="center">ivnvxd MCP Admin</h1>

<p align="center">
  <strong>Production-Ready Admin Bundle for ivnvxd/mcp-server-odoo</strong><br/>
  Web GUI + Built-in MCP Reverse Proxy + Process Manager, all in one container.
</p>

<p align="center">
  <a href="#features">Features</a> &bull;
  <a href="#architecture">Architecture</a> &bull;
  <a href="#screenshots">Screenshots</a> &bull;
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#deployment">Deployment</a> &bull;
  <a href="#configuration">Configuration</a> &bull;
  <a href="#api-reference">API Reference</a> &bull;
  <a href="README_zh-TW.md">中文文件</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Odoo-18.0-purple?logo=odoo" alt="Odoo 18"/>
  <img src="https://img.shields.io/badge/Python-3.12-blue?logo=python" alt="Python 3.12"/>
  <img src="https://img.shields.io/badge/React-19-61dafb?logo=react" alt="React 19"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/MCP-streamable--http-green" alt="MCP Protocol"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License"/>
  <img src="https://img.shields.io/badge/Docker-Multi--stage-2496ED?logo=docker" alt="Docker"/>
</p>

---

## Overview

**ivnvxd MCP Admin** is an all-in-one management platform that wraps [ivnvxd/mcp-server-odoo](https://github.com/ivnvxd/mcp-server-odoo) with a full-featured Web GUI, a built-in MCP reverse proxy (replacing nginx), and an async process manager -- all bundled into a single container.

It allows you to manage your MCP server entirely through a browser, with no `kubectl` or YAML editing required.

<p align="center">
  <img src="docs/screenshots/dashboard.png" alt="Dashboard" width="720"/>
</p>

### Why This Package?

| Challenge | Solution |
|-----------|----------|
| Managing MCP server requires `kubectl` + YAML editing | **Web GUI** with 8 management pages |
| Token rotation requires manual Secret update + pod restart | **One-click token rotation** with confirmation dialog |
| No visibility into MCP server logs without `kubectl logs` | **Real-time SSE log streaming** in browser |
| Needs separate nginx sidecar for auth proxy | **Built-in Python reverse proxy** (zero nginx) |
| No dashboard for health monitoring | **Live dashboard** with MCP/Odoo/Proxy status cards |
| Tool management requires env var changes + restart | **Visual toggle switch** to enable/disable all tools |
| Odoo connection config scattered across Secrets/ConfigMaps | **Single settings form** with test connection button |

---

## Features

### Web GUI (React 19 SPA)
- **8 management pages**: Dashboard, Tools, Connection, Tokens, Logs, Permissions, Settings, Login
- **JWT authentication** with httponly cookie support
- **Dark theme** with responsive design
- **30-second auto-refresh** dashboard

### Built-in MCP Reverse Proxy
- **Replaces nginx entirely** -- no sidecar container needed
- **URL-path token authentication**: `/private_{token}/mcp`
- **SSE streaming support** with `x-accel-buffering: no`
- **86,400-second timeout** for long-running MCP tool calls
- Compatible with **Claude Desktop**, **Cursor**, **Claude Code CLI**, **MCP Inspector**

### Process Manager
- **Async subprocess management** of `mcp-server-odoo`
- **Start/stop/restart** via GUI or API
- **Stdout/stderr capture** into ring buffer for log streaming
- **PID tracking** and restart counter

### MCP Server (ivnvxd/mcp-server-odoo v0.7.1)
- **9 MCP tools**: search_records, get_record, list_models, aggregate_records, list_resource_templates, create_record, update_record, delete_record, post_message
- **Smart field selection** -- automatically picks common fields
- **YOLO mode** (read/full) for quick testing without Odoo module
- **Standard mode** with mcp_server module for production (whitelist + API key + audit)
- **Native `/health` endpoint** for monitoring

---

## Architecture

```
Browser (React 19 SPA)
        |
        v
+------ FastAPI Admin Server (:8080) ------+
|                                           |
|  /api/*          JWT-protected admin API  |
|    /api/health     Dashboard data         |
|    /api/config     Connection config      |
|    /api/tools      Tool enable/disable    |
|    /api/tokens     Token rotation         |
|    /api/logs       SSE log streaming      |
|    /api/settings   MCP server settings    |
|                                           |
|  /private_{token}/*  MCP Reverse Proxy    |
|    -> http://127.0.0.1:8000/mcp           |
|                                           |
|  /*              SPA static files         |
|                                           |
|  ProcessManager (asyncio subprocess)      |
|    -> mcp-server-odoo :8000               |
|                                           |
+-------------------------------------------+
        |
        | XML-RPC (/xmlrpc/2/* or /mcp/xmlrpc/*)
        v
   Odoo 18 (:8069)
```

### System Flow

```mermaid
graph TB
    Client[MCP Client<br/>Claude / Cursor / Inspector]
    Browser[Browser<br/>Admin Web GUI]

    subgraph Container["Single Container :8080"]
        FastAPI[FastAPI Admin Server]
        Proxy[MCP Reverse Proxy<br/>/private_token/mcp]
        PM[Process Manager]
        SPA[React 19 SPA<br/>Static Files]
        MCP[mcp-server-odoo<br/>:8000 internal]
    end

    Odoo[Odoo 18<br/>:8069]
    Config[config.json<br/>Persistent Volume]

    Browser --> FastAPI
    FastAPI --> SPA
    Client --> Proxy
    Proxy --> MCP
    FastAPI --> PM
    PM --> MCP
    MCP --> Odoo
    FastAPI --> Config

    style Container fill:#1a1a2e,stroke:#22c55e,color:#fff
    style MCP fill:#22c55e,stroke:#fff,color:#000
    style Odoo fill:#714B67,stroke:#fff,color:#fff
```

### Component Architecture

```mermaid
graph LR
    subgraph Core["mcp_admin_core (reusable)"]
        App[app.py<br/>FastAPI Factory]
        ProxyM[proxy.py<br/>Reverse Proxy]
        Process[process.py<br/>Subprocess Mgr]
        Auth[auth/<br/>JWT Middleware]
        ConfigS[config/<br/>File Store]
    end

    subgraph Target["ivnvxd_mcp_admin (target-specific)"]
        Main[main.py<br/>Entry Point]
        Tools[tool_registry.py<br/>9 Tools]
        Health[routers/health.py<br/>ivnvxd /health]
        ConnCfg[routers/config.py<br/>ODOO_USER + API_KEY]
    end

    Main --> App
    Main --> Health
    Main --> ConnCfg
    Main --> Tools

    style Core fill:#1e3a5f,stroke:#60a5fa
    style Target fill:#3a1e5f,stroke:#a78bfa
```

---

## Screenshots

### Login

Secure JWT-based authentication with admin password.

<p align="center">
  <img src="docs/screenshots/login.png" alt="Login Page" width="720"/>
</p>

### Dashboard

Real-time health monitoring with 6 status cards: MCP Server, Odoo Instance, MCP Proxy, Version, Database, and Module count. Auto-refreshes every 30 seconds.

<p align="center">
  <img src="docs/screenshots/dashboard.png" alt="Dashboard" width="720"/>
</p>

### Tool Manager

Master toggle switch to enable/disable all 9 MCP tools at once. Tools are categorized into Read & Discover (5) and Write & Operate (4, marked as dangerous).

<p align="center">
  <img src="docs/screenshots/tools.png" alt="Tool Manager" width="720"/>
</p>

### Connection Configuration

Configure Odoo connection with support for three operation modes: Standard (API key + mcp_server module), YOLO Read-Only, and YOLO Full Access. Includes one-click connection test.

<p align="center">
  <img src="docs/screenshots/connection.png" alt="Connection Config" width="720"/>
</p>

### Token Manager

Manage MCP proxy authentication tokens. Show/hide masked tokens, copy to clipboard, and rotate with confirmation dialog. Rotation history tracks the last 10 events.

<p align="center">
  <img src="docs/screenshots/tokens.png" alt="Token Manager" width="720"/>
</p>

### Log Viewer

Real-time MCP server log streaming via Server-Sent Events. Supports pause/resume, auto-scroll, text filtering, and maintains a 5,000-line ring buffer.

<p align="center">
  <img src="docs/screenshots/logs.png" alt="Log Viewer" width="720"/>
</p>

### Settings

Full MCP server process configuration: command, arguments, port, environment variables. Includes restart button with live PID and restart count feedback. Also configures proxy timeout and admin password.

<p align="center">
  <img src="docs/screenshots/settings.png" alt="Settings" width="720"/>
</p>

### Permission Editor

JSON-based permission policy editor with syntax validation, format, and reset capabilities.

<p align="center">
  <img src="docs/screenshots/permissions.png" alt="Permission Editor" width="720"/>
</p>

---

## Quick Start

### Docker

```bash
docker run -d --name ivnvxd-mcp-admin \
  -p 8080:8080 \
  -e ODOO_URL=http://your-odoo:8069 \
  -e ODOO_DB=your_db \
  -e ODOO_USER=admin \
  -e ODOO_API_KEY=your_api_key \
  -v mcp-admin-data:/data \
  ghcr.io/woowtech/ivnvxd-mcp-admin:latest
```

Then open `http://localhost:8080` and login with password `admin`.

### Docker Compose

```bash
git clone https://github.com/WOOWTECH/woow_odoo_manage_mcp_server.git
cd woow_odoo_manage_mcp_server
ODOO_API_KEY=your_key docker compose up -d
```

---

## Deployment

### Kubernetes / K3s

```bash
# 1. Create image pull secret (for private GHCR)
kubectl create secret docker-registry ghcr-creds \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USER \
  --docker-password=YOUR_GITHUB_TOKEN \
  -n your-odoo-ns

# 2. Apply manifests
kubectl apply -f k8s/08-mcp-odoo-ivnvxd-admin.yaml

# 3. Verify
kubectl get pods -n your-odoo-ns -l app.kubernetes.io/component=mcp-odoo-ivnvxd-admin
```

### Cloudflare Tunnel

After deploying, add a tunnel route:

| Field | Value |
|-------|-------|
| Hostname | `your-mcp-admin.example.com` |
| Service | `http://mcp-odoo-ivnvxd-admin-svc:8080` |

MCP proxy URL: `https://your-mcp-admin.example.com/private_{token}/mcp`

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_ADMIN_CONFIG` | `/data/config.json` | Path to persistent config file |
| `JWT_SECRET` | (auto-generated) | JWT signing secret |
| `JWT_EXPIRY_HOURS` | `24` | JWT token expiry |
| `ODOO_URL` | -- | Initial Odoo URL |
| `ODOO_DB` | -- | Initial database name |
| `ODOO_USER` | -- | Initial Odoo username |
| `ODOO_API_KEY` | -- | Initial API key (Standard mode) |
| `ODOO_PASSWORD` | -- | Initial password (YOLO mode) |

### Operation Modes

| Mode | `ODOO_YOLO` | Requires Module | Auth | Access |
|------|-------------|-----------------|------|--------|
| **Standard** | `off` | Yes (`mcp_server` v18.0.1.1.0) | API key | Whitelist only |
| **YOLO Read** | `read` | No | Password | All models, read-only |
| **YOLO Full** | `true` | No | Password | All models, full CRUD |

---

## API Reference

### Admin Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/auth/login` | Get JWT token |
| `GET` | `/api/health` | Dashboard health data |
| `GET` | `/api/config` | Connection config (masked) |
| `PUT` | `/api/config/connection` | Update connection |
| `POST` | `/api/config/test` | Test Odoo connectivity |
| `GET` | `/api/tools` | List 9 tools with status |
| `PUT` | `/api/tools` | Enable/disable tools |
| `GET` | `/api/tokens` | Current token (masked) + history |
| `POST` | `/api/tokens/rotate` | Generate new token |
| `GET` | `/api/logs/stream` | SSE log stream |
| `GET` | `/api/logs/search?q=error` | Search log buffer |
| `PUT` | `/api/settings/{section}` | Update config section |
| `POST` | `/api/settings/mcp/restart` | Restart MCP server |

### MCP Proxy

```bash
# MCP clients connect via token-authenticated proxy
curl -X POST https://your-admin.example.com/private_{TOKEN}/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{...},"id":1}'
```

---

## Project Structure

```
woow_odoo_manage_mcp_server/
  mcp_admin_core/                 # Reusable core framework
    app.py                        # FastAPI factory + lifespan
    proxy.py                      # Built-in MCP reverse proxy
    process.py                    # Async subprocess manager
    config/store.py               # File-backed config store
    auth/middleware.py             # JWT authentication
    routers/settings.py           # Settings CRUD API
    k8s/client.py                 # Optional K8s API wrapper
  ivnvxd_mcp_admin/               # ivnvxd-specific package
    main.py                       # Entry point
    tool_registry.py              # 9 tool definitions
    routers/
      config.py                   # Odoo connection config
      health.py                   # Dashboard + /health check
      tools.py                    # Tool management
      tokens.py                   # Token rotation
      logs.py                     # SSE log streaming
  frontend/                       # React 19 + Tailwind 4 + Vite 6
    src/pages/                    # 8 page components
    src/components/               # Sidebar, StatusCard
  k8s/                            # Kubernetes manifests
  Dockerfile                      # Multi-stage build
  docker-compose.yml              # Local development
  pyproject.toml                  # Python package config
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, Tailwind CSS 4, Vite 6, TanStack React Query 5, lucide-react |
| **Backend** | FastAPI, Uvicorn, httpx, PyJWT |
| **MCP Server** | ivnvxd/mcp-server-odoo v0.7.1 |
| **Build** | Multi-stage Docker (Node 20 + Python 3.12) |
| **Deployment** | K3s, Cloudflare Tunnel, PVC |

---

## Comparison

| Feature | ivnvxd + nginx sidecar | **ivnvxd MCP Admin** |
|---------|----------------------|---------------------|
| Containers | 2 (ivnvxd + nginx) | **1 (all-in-one)** |
| Management | kubectl + YAML | **Web GUI** |
| Token rotation | Manual Secret + restart | **One-click in GUI** |
| Tool management | All-or-nothing | **Master toggle** |
| Logs | `kubectl logs` | **Real-time SSE** |
| Monitoring | curl /health | **Dashboard** |
| Settings | Edit ConfigMap | **Web form** |
| Auth proxy | nginx ConfigMap | **Built-in proxy** |

---

## License

[MIT](LICENSE)

---

<p align="center">
  <sub>Built with &#10084; by <a href="https://github.com/WOOWTECH">WOOWTECH</a> &bull; Powered by <a href="https://github.com/ivnvxd/mcp-server-odoo">ivnvxd/mcp-server-odoo</a></sub>
</p>
