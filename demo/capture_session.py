#!/usr/bin/env python3
"""Capture a REAL MCP agent session against the live SIFT VM (image mounted).

Records genuine tool calls + outputs to mcp_session.json so the demo terminal
scene replays authentic forensic activity, not a mockup.
"""
import asyncio
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sift_mcp import tools  # noqa: E402

OUT = Path(__file__).parent / "mcp_session.json"

SUSPECT = "/mnt/windows/Users/PC User/AppData/Local/Temp/set_PxRcHIFy.exe"

# (label shown in terminal, coroutine factory)
STEPS = [
    ("list_users", lambda: tools.list_users()),
    ("find_suspicious_executables", lambda: tools.find_suspicious_executables()),
    ("hash_file", lambda: tools.hash_file(SUSPECT)),
    ("extract_network_artifacts", lambda: tools.extract_network_artifacts()),
    ("get_system_info", lambda: tools.get_system_info()),
]


async def main():
    session = []
    for name, factory in STEPS:
        print(f"-> {name} …", flush=True)
        t0 = time.time()
        try:
            result = await asyncio.wait_for(factory(), timeout=180)
        except Exception as exc:
            result = {"error": str(exc)}
        dt = time.time() - t0
        session.append({"tool": name, "elapsed_s": round(dt, 2), "result": result})
        print(f"   {dt:.1f}s  {json.dumps(result)[:160]}", flush=True)

    OUT.write_text(json.dumps(session, indent=2, default=str), encoding="utf-8")
    print(f"\nWrote {OUT}  ({len(session)} real tool calls)")


if __name__ == "__main__":
    asyncio.run(main())
