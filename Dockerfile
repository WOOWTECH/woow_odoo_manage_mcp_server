# ── Stage 1: Build React frontend ──
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/ frontend/
RUN cd frontend && npm ci && npm run build

# ── Stage 2: Python runtime with ivnvxd MCP server + admin bundle ──
FROM python:3.12-slim
WORKDIR /app

# Install ivnvxd/mcp-server-odoo from PyPI
RUN pip install --no-cache-dir mcp-server-odoo

# Install admin bundle
COPY pyproject.toml /tmp/pkg/
COPY mcp_admin_core/ /tmp/pkg/mcp_admin_core/
COPY ivnvxd_mcp_admin/ /tmp/pkg/ivnvxd_mcp_admin/
RUN pip install --no-cache-dir /tmp/pkg/ && rm -rf /tmp/pkg/

# Copy frontend build output
COPY --from=frontend-builder /build/frontend/dist /app/static

# Config volume
RUN mkdir -p /data
VOLUME /data

EXPOSE 8080

ENV MCP_ADMIN_CONFIG=/data/config.json \
    PYTHONUNBUFFERED=1

CMD ["uvicorn", "ivnvxd_mcp_admin.main:app", "--host", "0.0.0.0", "--port", "8080"]
