"""Provider-neutral tool schemas and dispatcher."""

from __future__ import annotations

from typing import Any

from web_automator.providers.base import ToolSchema

# ---------------------------------------------------------------------------
# Tool schemas (provider-neutral JSON Schema definitions)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[ToolSchema] = [
    ToolSchema(
        name="navigate",
        description="Navigate the browser to a URL.",
        parameters={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The URL to navigate to."},
            },
            "required": ["url"],
        },
    ),
    ToolSchema(
        name="click",
        description="Click on an element identified by a CSS selector or visible text.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector or visible text of the element to click.",
                },
            },
            "required": ["selector"],
        },
    ),
    ToolSchema(
        name="type",
        description="Type text into an input field identified by a CSS selector.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector of the input element.",
                },
                "text": {"type": "string", "description": "Text to type."},
            },
            "required": ["selector", "text"],
        },
    ),
    ToolSchema(
        name="scroll",
        description="Scroll the page up or down.",
        parameters={
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["up", "down"],
                    "description": "Scroll direction.",
                },
                "amount": {
                    "type": "integer",
                    "description": "Number of pixels to scroll (default 500).",
                    "default": 500,
                },
            },
            "required": ["direction"],
        },
    ),
    ToolSchema(
        name="wait_for",
        description="Wait for an element matching a CSS selector to appear on the page.",
        parameters={
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "CSS selector to wait for.",
                },
                "timeout": {
                    "type": "integer",
                    "description": "Maximum wait time in milliseconds (default 10000).",
                    "default": 10000,
                },
            },
            "required": ["selector"],
        },
    ),
    ToolSchema(
        name="screenshot",
        description=(
            "Capture a screenshot of the current page. "
            "Returns a base64-encoded PNG image so you can see the page state."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    ToolSchema(
        name="get_page_content",
        description="Return the simplified text content of the current page (title + visible text).",
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    ToolSchema(
        name="extract",
        description="Extract specific information from the current page based on a description.",
        parameters={
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": "Description of what to extract (e.g. 'all product names and prices').",
                },
            },
            "required": ["description"],
        },
    ),
    ToolSchema(
        name="done",
        description=(
            "Signal that the task is complete. "
            "Call this when you have finished all required actions and have a final answer."
        ),
        parameters={
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "The final result or answer to return to the user.",
                },
            },
            "required": ["result"],
        },
    ),
    ToolSchema(
        name="get_html",
        description=(
            "Return the raw HTML of the current page or a scoped element. "
            "Use this before writing Playwright tests so you can inspect real "
            "attributes (id, data-testid, aria-label, name) to build reliable locators."
        ),
        parameters={
            "type": "object",
            "properties": {
                "selector": {
                    "type": "string",
                    "description": "Optional CSS selector to scope the HTML to one element.",
                }
            },
            "required": [],
        },
    ),
    ToolSchema(
        name="write_test",
        description=(
            "Write a Playwright test file to the generated_tests/ directory. "
            "Use after generating test code from the page HTML."
        ),
        parameters={
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "File name, e.g. 'test_login.py'.",
                },
                "content": {
                    "type": "string",
                    "description": "Full Python pytest-playwright test file content.",
                },
            },
            "required": ["filename", "content"],
        },
    ),
    ToolSchema(
        name="list_skills",
        description=(
            "List the names of all available skill playbooks. "
            "Call this to discover which skills exist before loading one."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    ToolSchema(
        name="read_skill",
        description=(
            "Read the contents of a named skill playbook. "
            "Use the names returned by list_skills. "
            "The playbook contains step-by-step guidance for completing common tasks."
        ),
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The skill name (without .md extension), e.g. 'google_search'.",
                },
            },
            "required": ["name"],
        },
    ),
]

TOOL_SCHEMA_MAP: dict[str, ToolSchema] = {t.name: t for t in TOOL_SCHEMAS}


# ---------------------------------------------------------------------------
# Dispatcher — maps tool name → browser method call
# (actual execution lives in browser.py; this just validates the dispatch)
# ---------------------------------------------------------------------------

DISPATCHABLE_TOOLS = {t.name for t in TOOL_SCHEMAS}


def get_tool_schemas() -> list[ToolSchema]:
    return TOOL_SCHEMAS


def validate_tool_call(name: str, arguments: dict[str, Any]) -> str | None:
    """Return an error string if the tool call is invalid, else None."""
    if name not in TOOL_SCHEMA_MAP:
        return f"Unknown tool: {name!r}"
    schema = TOOL_SCHEMA_MAP[name]
    required = schema.parameters.get("required", [])
    for field in required:
        if field not in arguments:
            return f"Missing required argument {field!r} for tool {name!r}"
    return None
