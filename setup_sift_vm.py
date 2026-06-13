#!/usr/bin/env python3
"""
SIFT VM Setup Script
- Starts the SIFT VM in VMware
- Configures NAT/port forwarding (SSH 2222 → 22)
- Copies forensic evidence to the VM
- Installs Python forensic libraries in SIFT
Run this once after the OVA import completes.
"""
import os
import subprocess
import sys
import time
import asyncio
from pathlib import Path

VMRUN = r"D:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe"
VMX = r"F:\5Gcase\hackton\SIFT-VM\SIFT-2026\SIFT-2026.vmx"
EVIDENCE_DIR = Path(r"F:\5Gcase\hackton\find\VANKO")
SIFT_USER = "sansforensics"
SIFT_PASS = "forensics"


def vmrun(*args):
    cmd = [VMRUN] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"vmrun {' '.join(args)}: rc={result.returncode}")
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    return result


def wait_for_ssh(host="127.0.0.1", port=2222, timeout=120):
    import socket
    print(f"Waiting for SSH on {host}:{port}...", end="", flush=True)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                print(" Connected!")
                return True
        except OSError:
            print(".", end="", flush=True)
            time.sleep(3)
    print(" TIMEOUT")
    return False


def copy_evidence_via_vmrun():
    """Copy E01 evidence files to SIFT VM using vmrun copyFileToGuest."""
    print("\nCopying evidence files to SIFT VM...")

    # Create evidence directory on guest
    vmrun("runProgramInGuest", VMX, "-interactive",
          "/bin/bash", "-c", f"mkdir -p /cases/VANKO && echo done")

    # Copy E01 segments (all 21 segments)
    for seg_file in sorted(EVIDENCE_DIR.glob("surface_physical.E*")):
        if seg_file.suffix == ".txt":
            continue
        dest = f"/cases/VANKO/{seg_file.name}"
        print(f"  Copying {seg_file.name}...")
        vmrun("copyFileToGuest", VMX, str(seg_file), dest)

    # Copy CYLR archive
    cylr = EVIDENCE_DIR / "vanko-c-drive.CYLR.7z"
    if cylr.exists():
        vmrun("copyFileToGuest", VMX, str(cylr), "/cases/VANKO/vanko-c-drive.CYLR.7z")

    print("Evidence copy complete.")


def install_python_libs():
    """Install python-registry, python-evtx in SIFT VM."""
    script = (
        "pip3 install python-registry python-evtx --quiet 2>&1 | tail -5"
    )
    vmrun("runProgramInGuest", VMX, "-interactive",
          "/bin/bash", "-c", f"sudo pip3 install python-registry python-evtx 2>&1")


def add_vmnet_portforward():
    """Add NAT port forward: host 2222 → guest 22."""
    vmrun("runProgramInGuest", VMX, "-interactive",
          "/bin/bash", "-c", "ip addr show | grep 'inet '")


def main():
    print("=== SIFT VM Setup ===")
    print(f"VMX: {VMX}")

    # Start VM
    print("\n1. Starting SIFT VM...")
    vmrun("start", VMX, "nogui")
    time.sleep(15)

    # Check VMware Tools / get IP
    print("\n2. Getting VM IP address...")
    result = vmrun("getGuestIPAddress", VMX, "-wait")
    if result.returncode == 0:
        ip = result.stdout.strip()
        print(f"   VM IP: {ip}")
        os.environ["SIFT_HOST"] = ip
        os.environ["SIFT_PORT"] = "22"
    else:
        print("   Could not get IP, will use NAT port forward 2222")

    # Enable shared folders for easy evidence access
    print("\n3. Enabling shared folders...")
    vmrun("enableSharedFolders", VMX)
    vmrun("addSharedFolder", VMX, "evidence", str(EVIDENCE_DIR))

    # Wait for SSH
    host = os.environ.get("SIFT_HOST", "127.0.0.1")
    port = int(os.environ.get("SIFT_PORT", "2222"))
    if not wait_for_ssh(host, port):
        print("ERROR: Cannot reach SIFT VM via SSH. Check network config.")
        sys.exit(1)

    # Install deps
    print("\n4. Installing Python forensic libraries...")
    install_python_libs()

    print("\n5. Copying evidence files...")
    copy_evidence_via_vmrun()

    print("\n✓ SIFT VM setup complete!")
    print(f"   SSH: ssh {SIFT_USER}@{host} -p {port}")
    print(f"   Password: {SIFT_PASS}")
    print(f"\nNext: set SIFT_HOST={host} SIFT_PORT={port} and run:")
    print("   python orchestrator.py --output-dir ./findings")


if __name__ == "__main__":
    main()
