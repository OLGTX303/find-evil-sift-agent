"""SSH connection manager for SIFT Workstation VM."""
import asyncio
import asyncssh
import os
from typing import Optional

SIFT_HOST = os.getenv("SIFT_HOST", "192.168.220.129")
SIFT_PORT = int(os.getenv("SIFT_PORT", "22"))
SIFT_USER = os.getenv("SIFT_USER", "sansforensics")
SIFT_PASS = os.getenv("SIFT_PASS", "forensics")
EVIDENCE_DIR = os.getenv("EVIDENCE_DIR", "/mnt/hgfs/vanko")
MOUNT_DIR = os.getenv("MOUNT_DIR", "/mnt/ewf")
WINDOWS_DIR = os.getenv("WINDOWS_DIR", "/mnt/windows")


async def run_cmd(cmd: str, timeout: int = 300) -> tuple[str, str, int]:
    """Run a command on the SIFT VM and return (stdout, stderr, returncode)."""
    async with asyncssh.connect(
        SIFT_HOST,
        port=SIFT_PORT,
        username=SIFT_USER,
        password=SIFT_PASS,
        known_hosts=None,
    ) as conn:
        result = await asyncio.wait_for(
            conn.run(cmd, check=False),
            timeout=timeout,
        )
        return result.stdout or "", result.stderr or "", result.returncode or 0


async def run_sudo(cmd: str, timeout: int = 300) -> tuple[str, str, int]:
    """Run a command with sudo on the SIFT VM."""
    return await run_cmd(f"echo {SIFT_PASS} | sudo -S {cmd}", timeout=timeout)
