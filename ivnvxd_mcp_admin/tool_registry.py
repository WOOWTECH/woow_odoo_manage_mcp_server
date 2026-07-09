"""Registry of all 9 ivnvxd/mcp-server-odoo tools organized into 2 categories.

Each tool entry contains:
- name: The MCP tool function name
- description: Human-readable description
- category: Grouping category for UI display
- enabled_by_default: Whether the tool is enabled when first deployed
- dangerous: Whether the tool performs write/modify operations
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


class ToolCategory(str, Enum):
    """Categories for organizing ivnvxd MCP tools."""

    READ_DISCOVER = "Read & Discover"
    WRITE_OPERATE = "Write & Operate"


class ToolDefinition(BaseModel):
    """Schema for a single MCP tool definition."""

    name: str
    description: str
    category: ToolCategory
    enabled_by_default: bool = True
    dangerous: bool = False


class ToolState(BaseModel):
    """Runtime state of a tool (definition + current enabled status)."""

    name: str
    description: str
    category: ToolCategory
    enabled_by_default: bool
    dangerous: bool
    enabled: bool


class ToolUpdateRequest(BaseModel):
    """Request body for updating tool enabled states."""

    tools: Any  # dict[str, bool] or list[dict] from frontend


class ToolUpdateResponse(BaseModel):
    """Response after updating tool states."""

    updated: int
    tools: list[ToolState]


# ---------------------------------------------------------------------------
# Complete registry of all 9 ivnvxd/mcp-server-odoo tools
# ---------------------------------------------------------------------------

TOOL_REGISTRY: list[ToolDefinition] = [
    # ── Read & Discover (5) ───────────────────────────────────────────────
    ToolDefinition(
        name="search_records",
        description="Search for records with domain filters, smart field selection, and pagination",
        category=ToolCategory.READ_DISCOVER,
    ),
    ToolDefinition(
        name="get_record",
        description="Get a specific record by ID with smart field selection",
        category=ToolCategory.READ_DISCOVER,
    ),
    ToolDefinition(
        name="list_models",
        description="List all models enabled for MCP access with allowed operations",
        category=ToolCategory.READ_DISCOVER,
    ),
    ToolDefinition(
        name="aggregate_records",
        description="Server-side aggregation via Odoo's read_group (sum, avg, count, groupby)",
        category=ToolCategory.READ_DISCOVER,
    ),
    ToolDefinition(
        name="list_resource_templates",
        description="List available resource URI templates for model/record/field access",
        category=ToolCategory.READ_DISCOVER,
    ),
    # ── Write & Operate (4) ───────────────────────────────────────────────
    ToolDefinition(
        name="create_record",
        description="Create a new record in an Odoo model",
        category=ToolCategory.WRITE_OPERATE,
        dangerous=True,
    ),
    ToolDefinition(
        name="update_record",
        description="Update an existing record's field values",
        category=ToolCategory.WRITE_OPERATE,
        dangerous=True,
    ),
    ToolDefinition(
        name="delete_record",
        description="Delete a record permanently",
        category=ToolCategory.WRITE_OPERATE,
        dangerous=True,
    ),
    ToolDefinition(
        name="post_message",
        description="Post a message to a record's chatter (mail.thread)",
        category=ToolCategory.WRITE_OPERATE,
        dangerous=True,
    ),
]

# Pre-built lookups
TOOL_BY_NAME: dict[str, ToolDefinition] = {t.name: t for t in TOOL_REGISTRY}

TOOLS_BY_CATEGORY: dict[ToolCategory, list[ToolDefinition]] = {}
for _tool in TOOL_REGISTRY:
    TOOLS_BY_CATEGORY.setdefault(_tool.category, []).append(_tool)


def get_tool_states(enabled_overrides: dict[str, bool] | None = None) -> list[ToolState]:
    """Build the full tool state list, applying any enabled overrides."""
    overrides = enabled_overrides or {}
    return [
        ToolState(
            name=t.name,
            description=t.description,
            category=t.category,
            enabled_by_default=t.enabled_by_default,
            dangerous=t.dangerous,
            enabled=overrides.get(t.name, t.enabled_by_default),
        )
        for t in TOOL_REGISTRY
    ]


def get_category_summary() -> dict[str, dict[str, Any]]:
    """Return a summary of tools per category."""
    return {
        cat.value: {
            "count": len(tools),
            "tools": [t.name for t in tools],
        }
        for cat, tools in TOOLS_BY_CATEGORY.items()
    }
