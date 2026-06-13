#!/usr/bin/env python3
"""
FIND EVIL! Autonomous IR Orchestrator
Drives a logical investigation pipeline against the VANKO forensic image
using Claude claude-sonnet-4-6 and the SIFT forensic MCP server.

Usage:
    python orchestrator.py [--output-dir ./findings]
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import anthropic

MODEL = "claude-sonnet-4-6"
SIFT_MCP_CMD = [sys.executable, "-m", "sift_mcp.server"]

SYSTEM_PROMPT = """You are an expert digital forensic investigator performing autonomous incident response
on the VANKO forensic image (Microsoft Surface 3, acquired 2016-11-04, Case #20161104).

Your mission is to find evil — unauthorized access, malware, data exfiltration, or other malicious activity.

## Investigation protocol
1. ALWAYS start with setup_evidence → mount_image → get_system_info → list_users
2. For each user found: check list_recent_files, get_run_keys
3. Run find_suspicious_executables on the whole image
4. Extract and parse Security.evtx for logon anomalies
5. Run yara_scan on suspicious paths
6. If suspicious files found: hash_file → check_known_malware_hashes
7. Start run_log2timeline for timeline (async — poll with get_timeline_status)
8. Summarize findings with confidence levels and recommended actions

## Self-correction rules
- If a tool returns an error, try an alternative approach before giving up
- If a path is not found, search for it with find_suspicious_executables or extract_file
- If log2timeline is still running, continue other analysis and check back
- If registry parse fails, try regripper fallback (call parse_registry without key_path)

## Output format
At the end, produce a structured JSON report:
{
  "case": "20161104-VANKO",
  "investigator": "SIFT-AI-Agent",
  "timestamp": "<ISO8601>",
  "system": { "hostname": "...", "os": "...", "users": [...] },
  "findings": [
    {
      "id": "F001",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "category": "malware|persistence|lateral_movement|data_exfiltration|suspicious_behavior",
      "title": "...",
      "description": "...",
      "evidence": ["tool_name: result snippet"],
      "confidence": 0.0-1.0,
      "recommendation": "..."
    }
  ],
  "timeline_highlights": [...],
  "false_positive_notes": "...",
  "iocs": { "files": [], "hashes": [], "ips": [], "domains": [] }
}
"""


class AuditLogger:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = output_dir / "agent_execution_log.jsonl"
        self.session_start = datetime.now(timezone.utc)
        self._seq = 0

    def _entry(self, event_type: str, data: dict) -> dict:
        self._seq += 1
        return {
            "seq": self._seq,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_s": (datetime.now(timezone.utc) - self.session_start).total_seconds(),
            "event": event_type,
            **data,
        }

    def log(self, event_type: str, **kwargs):
        entry = self._entry(event_type, kwargs)
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        # Pretty-print to stderr for live visibility
        ts = entry["timestamp"][11:19]
        print(f"[{ts}] [{event_type}] {json.dumps(kwargs)[:120]}", file=sys.stderr)
        return entry


async def run_investigation(output_dir: Path):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    audit = AuditLogger(output_dir)
    audit.log("session_start", model=MODEL, case="20161104-VANKO")

    messages = []
    tool_results_pending = []
    iteration = 0
    max_iterations = 40  # safety limit

    while iteration < max_iterations:
        iteration += 1
        audit.log("agent_turn", iteration=iteration)

        kwargs = dict(
            model=MODEL,
            max_tokens=8096,
            system=SYSTEM_PROMPT,
            tools=await _get_tool_schemas(),
            messages=messages if messages else [
                {"role": "user", "content": "Begin the autonomous investigation of the VANKO forensic image. Follow the investigation protocol systematically."}
            ],
        )

        response = client.messages.create(**kwargs)
        audit.log("llm_response", stop_reason=response.stop_reason, usage=dict(response.usage))

        # Process response blocks
        assistant_content = []
        for block in response.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
                if block.text.strip():
                    audit.log("reasoning", text=block.text[:500])
            elif block.type == "tool_use":
                assistant_content.append({
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                })
                audit.log("tool_call", tool=block.name, input=block.input)

        messages.append({"role": "assistant", "content": assistant_content})

        if response.stop_reason == "end_turn":
            audit.log("investigation_complete", iterations=iteration)
            # Extract final JSON report from last text block
            for block in reversed(response.content):
                if hasattr(block, "text") and "{" in block.text:
                    report_path = output_dir / "findings_report.json"
                    try:
                        start = block.text.index("{")
                        end = block.text.rindex("}") + 1
                        report = json.loads(block.text[start:end])
                        report_path.write_text(json.dumps(report, indent=2))
                        audit.log("report_saved", path=str(report_path))
                        print(f"\n✓ Report saved: {report_path}")
                    except Exception:
                        report_path.write_text(block.text)
                    break
            break

        if response.stop_reason != "tool_use":
            audit.log("unexpected_stop", reason=response.stop_reason)
            break

        # Execute tool calls
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            audit.log("tool_execute", tool=block.name, input=block.input)
            try:
                result = await _call_sift_tool(block.name, block.input)
                audit.log("tool_result", tool=block.name, result_preview=str(result)[:300])
            except Exception as exc:
                result = {"error": str(exc)}
                audit.log("tool_error", tool=block.name, error=str(exc))

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(result, default=str),
            })

        messages.append({"role": "user", "content": tool_results})

    audit.log("session_end", total_iterations=iteration)
    print(f"\n✓ Audit log: {audit.log_path}")


# ── MCP tool integration ──────────────────────────────────────────────────────

_sift_tools_cache: list[dict] | None = None


async def _get_tool_schemas() -> list[dict]:
    """Load tool schemas from the SIFT MCP server."""
    global _sift_tools_cache
    if _sift_tools_cache:
        return _sift_tools_cache

    # Import directly to avoid subprocess overhead in demo mode
    from sift_mcp import tools as sift_tools
    from sift_mcp.server import list_tools
    tool_list = await list_tools()
    _sift_tools_cache = [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.inputSchema,
        }
        for t in tool_list
    ]
    return _sift_tools_cache


async def _call_sift_tool(name: str, arguments: dict) -> dict:
    """Call a SIFT forensic tool."""
    from sift_mcp import tools as sift_tools
    fn = getattr(sift_tools, name, None)
    if fn is None:
        return {"error": f"Unknown tool: {name}"}
    return await fn(**arguments)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="FIND EVIL! Autonomous IR Orchestrator")
    parser.add_argument("--output-dir", default="./findings", help="Directory for reports and logs")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    print(f"FIND EVIL! Autonomous IR — Case 20161104-VANKO")
    print(f"Output directory: {output_dir.resolve()}")
    print("-" * 60)

    asyncio.run(run_investigation(output_dir))


if __name__ == "__main__":
    main()
