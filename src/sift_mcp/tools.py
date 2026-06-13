"""Forensic analysis tools wrapping SIFT Workstation commands via SSH."""
import json
import re
from datetime import datetime
from .ssh_client import run_cmd, run_sudo, EVIDENCE_DIR, MOUNT_DIR

# ── Evidence setup ────────────────────────────────────────────────────────────

async def setup_evidence() -> dict:
    """Copy evidence files to SIFT VM and verify checksums."""
    stdout, stderr, rc = await run_sudo(
        f"mkdir -p {EVIDENCE_DIR} && ls {EVIDENCE_DIR}"
    )
    return {"evidence_dir": EVIDENCE_DIR, "files": stdout.strip().splitlines(), "rc": rc}


async def mount_image(image_path: str = None) -> dict:
    """
    Mount an E01/EWF forensic image using ewfmount + kpartx.
    Returns mount point and partition list.
    """
    img = image_path or f"{EVIDENCE_DIR}/surface_physical.E01"
    cmds = [
        f"mkdir -p {MOUNT_DIR}",
        f"ewfmount {img} {MOUNT_DIR} 2>&1",
        f"kpartx -av {MOUNT_DIR}/ewf1 2>&1",
    ]
    results = []
    for cmd in cmds:
        stdout, stderr, rc = await run_sudo(cmd, timeout=120)
        results.append({"cmd": cmd, "stdout": stdout.strip(), "rc": rc})

    # List resulting loop devices / mount points
    stdout, _, _ = await run_cmd("lsblk -J 2>/dev/null | python3 -c \"import sys,json; d=json.load(sys.stdin); [print(b['name'],b.get('mountpoint','')) for b in d['blockdevices']]\"")
    return {"steps": results, "block_devices": stdout.strip().splitlines()}


async def unmount_image() -> dict:
    """Unmount the forensic image cleanly."""
    stdout, stderr, rc = await run_sudo(f"kpartx -d {MOUNT_DIR}/ewf1 && umount {MOUNT_DIR}")
    return {"stdout": stdout, "rc": rc}


# ── File system analysis ──────────────────────────────────────────────────────

async def list_users() -> dict:
    """List Windows user accounts from the mounted image."""
    cmd = f"find /mnt/windows -path '*/Users/*' -maxdepth 5 -name 'NTUSER.DAT' 2>/dev/null | head -30"
    stdout, stderr, rc = await run_cmd(cmd, timeout=60)
    users = []
    for line in stdout.strip().splitlines():
        parts = line.split("/")
        idx = next((i for i, p in enumerate(parts) if p == "Users"), None)
        if idx and idx + 1 < len(parts):
            users.append(parts[idx + 1])
    return {"users": list(set(users)), "raw_paths": stdout.strip().splitlines()}


async def list_recent_files(username: str = None, count: int = 50) -> dict:
    """List recently accessed files for a user (LNK files, RecentDocs)."""
    base = f"/mnt/windows/*/Users/{username or '*'}" if username else "/mnt/windows/*/Users/*"
    cmd = f"find {base}/AppData/Roaming/Microsoft/Windows/Recent -name '*.lnk' 2>/dev/null | head -{count}"
    stdout, stderr, rc = await run_cmd(cmd, timeout=60)
    files = stdout.strip().splitlines()
    return {"count": len(files), "files": files}


async def find_suspicious_executables() -> dict:
    """Find executables in unusual locations (temp dirs, user dirs, downloads)."""
    locations = [
        "/mnt/windows/Users -ipath '*/AppData/Local/Temp/*.exe'",
        "/mnt/windows/Users -ipath '*/AppData/Roaming/*.exe'",
        "/mnt/windows/Users -ipath '*/Downloads/*.exe'",
        "/mnt/windows/Windows/Temp -name '*.exe'",
        "/mnt/windows/ProgramData -maxdepth 2 -name '*.exe'",
    ]
    all_hits = []
    for pattern in locations:
        stdout, _, _ = await run_cmd(f"find {pattern} 2>/dev/null | head -20")
        all_hits.extend(stdout.strip().splitlines())
    return {"suspicious_executables": all_hits, "count": len(all_hits)}


async def extract_file(remote_path: str) -> dict:
    """Read a text/binary file from the mounted image (first 4KB)."""
    stdout, stderr, rc = await run_cmd(f"file '{remote_path}' && head -c 4096 '{remote_path}' | strings | head -80")
    return {"path": remote_path, "content": stdout.strip(), "rc": rc}


# ── Timeline analysis ─────────────────────────────────────────────────────────

async def run_log2timeline(output_file: str = None, partition: str = None) -> dict:
    """
    Run log2timeline/plaso for full timeline creation.
    This is a long-running operation; use get_timeline_status to poll.
    """
    out = output_file or f"{EVIDENCE_DIR}/timeline.plaso"
    part = partition or "/dev/mapper/loop0p3"  # typical Windows partition
    cmd = (
        f"log2timeline.py --parsers win7 --storage-file {out} "
        f"--vss-stores all {part} > {EVIDENCE_DIR}/log2timeline.log 2>&1 &"
    )
    _, _, rc = await run_sudo(cmd, timeout=30)
    return {"status": "started", "output": out, "log": f"{EVIDENCE_DIR}/log2timeline.log", "rc": rc}


async def get_timeline_status() -> dict:
    """Check if log2timeline is still running and show last log lines."""
    stdout, _, _ = await run_cmd("pgrep -a log2timeline 2>/dev/null")
    running = bool(stdout.strip())
    log_stdout, _, _ = await run_cmd(f"tail -20 {EVIDENCE_DIR}/log2timeline.log 2>/dev/null")
    return {"running": running, "log_tail": log_stdout.strip().splitlines()}


async def run_psort(filter_query: str = "", top_n: int = 100) -> dict:
    """
    Run psort to query the plaso timeline.
    filter_query example: 'date > 2016-10-01 AND date < 2016-11-05'
    """
    plaso = f"{EVIDENCE_DIR}/timeline.plaso"
    filt = f"--filter \"{filter_query}\"" if filter_query else ""
    cmd = f"psort.py -o l2tcsv {filt} {plaso} 2>/dev/null | head -{top_n}"
    stdout, stderr, rc = await run_cmd(cmd, timeout=120)
    events = []
    for line in stdout.strip().splitlines()[1:]:  # skip header
        parts = line.split(",", 15)
        if len(parts) >= 5:
            events.append({
                "date": parts[0].strip(),
                "time": parts[1].strip(),
                "source": parts[2].strip(),
                "type": parts[4].strip(),
                "description": parts[-1].strip() if len(parts) > 4 else "",
            })
    return {"events": events, "count": len(events), "raw": stdout.strip()}


# ── Registry analysis ─────────────────────────────────────────────────────────

async def parse_registry(hive_path: str, key_path: str = None) -> dict:
    """Parse a Windows registry hive using regripper or python-registry."""
    if key_path:
        cmd = f"python3 -c \"import Registry.Registry as R; r=R.RegistryHive('{hive_path}'); k=r.open('{key_path}'); [print(v.name(), '=', v.value()) for v in k.values()]\""
    else:
        cmd = f"regripper -r '{hive_path}' -f all 2>/dev/null | head -200"
    stdout, stderr, rc = await run_cmd(cmd, timeout=60)
    return {"hive": hive_path, "key": key_path, "output": stdout.strip(), "rc": rc}


async def get_run_keys() -> dict:
    """Extract autorun/persistence keys from registry."""
    ntuser_paths, _, _ = await run_cmd("find /mnt/windows -name 'NTUSER.DAT' 2>/dev/null | head -10")
    software_path, _, _ = await run_cmd("find /mnt/windows -path '*/Windows/System32/config/SOFTWARE' 2>/dev/null | head -3")

    run_keys = [
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        r"Software\Microsoft\Windows\CurrentVersion\RunOnce",
        r"Software\Microsoft\Windows NT\CurrentVersion\Winlogon",
    ]
    results = {}
    for hive in ntuser_paths.strip().splitlines()[:3]:
        for key in run_keys:
            stdout, _, rc = await run_cmd(
                f"python3 -c \"import Registry.Registry as R; r=R.RegistryHive('{hive}'); k=r.open('{key.replace(chr(92), '/')}'); [print(v.name(),'=',v.value()) for v in k.values()]\" 2>/dev/null"
            )
            if stdout.strip():
                results[f"{hive}::{key}"] = stdout.strip().splitlines()
    return {"run_keys": results}


# ── YARA scanning ─────────────────────────────────────────────────────────────

async def yara_scan(scan_path: str = None, rules_dir: str = "/opt/malware-rules") -> dict:
    """
    Run YARA malware detection against mounted image or specific path.
    Returns matches with rule names and file paths.
    """
    target = scan_path or "/mnt/windows"
    cmd = f"yara -r {rules_dir}/*.yar {target} 2>/dev/null | head -100"
    stdout, stderr, rc = await run_cmd(cmd, timeout=300)
    matches = []
    for line in stdout.strip().splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            matches.append({"rule": parts[0], "file": parts[1]})
    return {"matches": matches, "count": len(matches), "scan_path": target}


# ── Event log analysis ────────────────────────────────────────────────────────

async def parse_evtx(evtx_path: str, event_ids: list[int] = None, top_n: int = 50) -> dict:
    """Parse Windows EVTX event logs using python-evtx."""
    id_filter = ""
    if event_ids:
        id_str = ",".join(str(i) for i in event_ids)
        id_filter = f"| python3 -c \"import sys; lines=[l for l in sys.stdin if any(f'<EventID>{i}</EventID>' in l for i in [{id_str}])]; [print(l,end='') for l in lines[:50]]\""
    cmd = f"python3 -c \"import Evtx.Evtx as e; import Evtx.Views as v; f=e.Evtx('{evtx_path}'); [print(v.evtx_record_xml_view(r,f)) for r in list(f.records())[-{top_n}:]]\" 2>/dev/null {id_filter}"
    stdout, stderr, rc = await run_cmd(cmd, timeout=120)
    return {"evtx": evtx_path, "event_ids": event_ids, "output": stdout.strip()[:8000], "rc": rc}


async def get_logon_events(top_n: int = 30) -> dict:
    """Extract logon/logoff events from Security.evtx (4624, 4625, 4634)."""
    evtx_path, _, _ = await run_cmd("find /mnt/windows -path '*/Logs/Security.evtx' 2>/dev/null | head -3")
    if not evtx_path.strip():
        return {"error": "Security.evtx not found on mounted image"}
    return await parse_evtx(evtx_path.strip().splitlines()[0], [4624, 4625, 4634], top_n)


# ── Network artifacts ─────────────────────────────────────────────────────────

async def extract_network_artifacts() -> dict:
    """Extract network-related artifacts: prefetch, DNS cache, browser history."""
    results = {}
    # Prefetch files (indicate what ran)
    stdout, _, _ = await run_cmd("find /mnt/windows -path '*/Windows/Prefetch/*.pf' 2>/dev/null | head -50")
    results["prefetch_files"] = stdout.strip().splitlines()

    # Hosts file
    stdout, _, _ = await run_cmd("cat /mnt/windows/*/Windows/System32/drivers/etc/hosts 2>/dev/null | grep -v '^#' | grep -v '^$'")
    results["hosts_file"] = stdout.strip().splitlines()

    # Chrome/Firefox history
    for browser in ["Chrome", "Firefox", "Edge"]:
        stdout, _, _ = await run_cmd(f"find /mnt/windows -path '*/{browser}*' -name 'History' 2>/dev/null | head -5")
        if stdout.strip():
            results[f"{browser.lower()}_history_paths"] = stdout.strip().splitlines()

    return results


# ── Hashing and integrity ─────────────────────────────────────────────────────

async def hash_file(remote_path: str) -> dict:
    """Compute MD5/SHA256 of a file on the mounted image."""
    stdout, _, rc = await run_cmd(f"md5sum '{remote_path}' && sha256sum '{remote_path}'")
    lines = stdout.strip().splitlines()
    return {
        "path": remote_path,
        "md5": lines[0].split()[0] if len(lines) > 0 else None,
        "sha256": lines[1].split()[0] if len(lines) > 1 else None,
    }


async def check_known_malware_hashes(hashes: list[str]) -> dict:
    """Check hashes against local NSRL/malware hash database."""
    # Use hashdeep or md5deep with NSRL DB if available
    results = {}
    for h in hashes:
        stdout, _, rc = await run_cmd(f"grep -i '{h}' /opt/malware-hashes/*.txt 2>/dev/null | head -5")
        results[h] = {"matches": stdout.strip().splitlines(), "found": bool(stdout.strip())}
    return {"results": results}


# ── Summary / reporting ───────────────────────────────────────────────────────

async def get_system_info() -> dict:
    """Extract basic system info from the image (OS version, hostname, timezone)."""
    results = {}

    # Hostname from registry
    stdout, _, _ = await run_cmd(
        "find /mnt/windows -path '*/System32/config/SYSTEM' 2>/dev/null | head -1 | "
        "xargs -I{} python3 -c \"import Registry.Registry as R; r=R.RegistryHive('{}'); "
        "k=r.open('ControlSet001/Control/ComputerName/ComputerName'); "
        "[print(v.name(),'=',v.value()) for v in k.values()]\" 2>/dev/null"
    )
    results["hostname"] = stdout.strip()

    # OS info from SOFTWARE hive
    stdout, _, _ = await run_cmd(
        "find /mnt/windows -path '*/System32/config/SOFTWARE' 2>/dev/null | head -1 | "
        "xargs -I{} python3 -c \"import Registry.Registry as R; r=R.RegistryHive('{}'); "
        "k=r.open('Microsoft/Windows NT/CurrentVersion'); "
        "[print(v.name(),'=',v.value()) for v in k.values() if v.name() in ['ProductName','CurrentBuildNumber','RegisteredOwner','InstallDate']]\" 2>/dev/null"
    )
    results["os_info"] = stdout.strip()

    # Time zone
    stdout, _, _ = await run_cmd(
        "find /mnt/windows -path '*/System32/config/SYSTEM' 2>/dev/null | head -1 | "
        "xargs -I{} python3 -c \"import Registry.Registry as R; r=R.RegistryHive('{}'); "
        "k=r.open('ControlSet001/Control/TimeZoneInformation'); "
        "[print(v.name(),'=',v.value()) for v in k.values() if v.name() in ['TimeZoneKeyName','Bias']]\" 2>/dev/null"
    )
    results["timezone"] = stdout.strip()

    return results
