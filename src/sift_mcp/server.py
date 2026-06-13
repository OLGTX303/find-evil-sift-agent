"""
SIFT Forensic MCP Server
Exposes SIFT Workstation tools as MCP tools for autonomous incident response.
"""
import asyncio
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

from . import tools

app = Server("sift-forensic-mcp")


def _tool(name: str, description: str, properties: dict, required: list[str] = None):
    return types.Tool(
        name=name,
        description=description,
        inputSchema={
            "type": "object",
            "properties": properties,
            "required": required or [],
        },
    )


@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        _tool("setup_evidence", "Copy evidence to SIFT VM and verify. Call this first.", {}),
        _tool(
            "mount_image",
            "Mount the E01 forensic image using ewfmount + kpartx. Required before any file-system analysis.",
            {"image_path": {"type": "string", "description": "Path to .E01 file on SIFT VM (optional, uses default)"}},
        ),
        _tool("unmount_image", "Unmount the forensic image cleanly after analysis.", {}),
        _tool("get_system_info", "Extract OS version, hostname, timezone from the mounted image.", {}),
        _tool("list_users", "List Windows user accounts discovered in the image.", {}),
        _tool(
            "list_recent_files",
            "List recently accessed files (LNK files) for a user.",
            {
                "username": {"type": "string", "description": "Windows username (omit for all users)"},
                "count": {"type": "integer", "description": "Max results (default 50)"},
            },
        ),
        _tool(
            "find_suspicious_executables",
            "Find executables in anomalous locations: Temp dirs, user AppData, ProgramData.",
            {},
        ),
        _tool(
            "extract_file",
            "Read strings from a file on the mounted image (first 4KB).",
            {"remote_path": {"type": "string", "description": "Absolute path to file on mounted image"}},
            ["remote_path"],
        ),
        _tool(
            "run_log2timeline",
            "Start log2timeline timeline creation (long-running). Poll with get_timeline_status.",
            {
                "output_file": {"type": "string", "description": "Path for .plaso output file"},
                "partition": {"type": "string", "description": "Block device of Windows partition"},
            },
        ),
        _tool("get_timeline_status", "Check if log2timeline is running; return last log lines.", {}),
        _tool(
            "run_psort",
            "Query the plaso timeline. Returns events sorted by time.",
            {
                "filter_query": {"type": "string", "description": "e.g. 'date > 2016-10-01 AND date < 2016-11-05'"},
                "top_n": {"type": "integer", "description": "Max events to return (default 100)"},
            },
        ),
        _tool(
            "parse_registry",
            "Parse a Windows registry hive. Optionally navigate to a specific key.",
            {
                "hive_path": {"type": "string", "description": "Path to hive file (NTUSER.DAT, SYSTEM, etc.)"},
                "key_path": {"type": "string", "description": "Registry key path within hive (optional)"},
            },
            ["hive_path"],
        ),
        _tool("get_run_keys", "Extract Run/RunOnce autostart registry keys from all user hives.", {}),
        _tool(
            "yara_scan",
            "Run YARA malware detection rules against a path in the mounted image.",
            {
                "scan_path": {"type": "string", "description": "Path to scan (default: /mnt)"},
                "rules_dir": {"type": "string", "description": "Directory with .yar rule files"},
            },
        ),
        _tool(
            "parse_evtx",
            "Parse a Windows EVTX event log file.",
            {
                "evtx_path": {"type": "string", "description": "Path to .evtx file"},
                "event_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Filter to specific Event IDs (optional)",
                },
                "top_n": {"type": "integer", "description": "Max events (default 50)"},
            },
            ["evtx_path"],
        ),
        _tool("get_logon_events", "Extract logon/logoff events (4624, 4625, 4634) from Security.evtx.", {
            "top_n": {"type": "integer", "description": "Max events (default 30)"},
        }),
        _tool("extract_network_artifacts", "Extract prefetch files, hosts file, browser history paths.", {}),
        _tool(
            "hash_file",
            "Compute MD5 and SHA256 hash of a file on the mounted image.",
            {"remote_path": {"type": "string", "description": "Path to file"}},
            ["remote_path"],
        ),
        _tool(
            "check_known_malware_hashes",
            "Check hashes against local NSRL/malware hash database.",
            {"hashes": {"type": "array", "items": {"type": "string"}, "description": "List of MD5/SHA256 hashes"}},
            ["hashes"],
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    tool_fn = getattr(tools, name, None)
    if tool_fn is None:
        raise ValueError(f"Unknown tool: {name}")
    try:
        result = await tool_fn(**arguments)
    except Exception as exc:
        result = {"error": str(exc), "tool": name}
    return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]


def main():
    async def _run():
        async with stdio_server() as (read, write):
            await app.run(read, write, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
