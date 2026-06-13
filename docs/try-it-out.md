# Try It Out — Judges Guide

## Prerequisites

- Windows 10/11 host with VMware Workstation Pro 17+
- Python 3.10+
- OpenAI-compatible API key
- ~150 GB free disk space (evidence + VM)
- 8 GB+ RAM (16 GB recommended for SIFT VM)

## Step 1 — Clone and install

```bash
git clone https://github.com/OLGTX303/find-evil-sift-agent
cd find-evil-sift-agent
pip install -e .
```

## Step 2 — Import SIFT VM

```powershell
$ovftool = "C:\Program Files (x86)\VMware\VMware Workstation\OVFTool\ovftool.exe"
& $ovftool --acceptAllEulas --name="SIFT-2026" sift-2026-04-22.ova F:\SIFT-VM\
```

## Step 3 — Place evidence

Copy the VANKO evidence files to your machine:
```
find\VANKO\surface_physical.E01 through .E21
find\VANKO\vanko-c-drive.CYLR.7z
```

## Step 4 — Configure and start the SIFT VM

```bash
python setup_sift_vm.py
# Starts the VM, enables SSH, copies evidence files
# Prints the VM IP at the end
```

## Step 5 — Set environment variables

```powershell
$env:OPENAI_API_KEY  = "sk-..."
$env:OPENAI_BASE_URL = "https://api.openai.com/v1"
$env:SIFT_HOST       = "192.168.x.x"   # printed by setup_sift_vm.py
$env:SIFT_PORT       = "22"
$env:SIFT_USER       = "sansforensics"
$env:SIFT_PASS       = "forensics"
$env:EVIDENCE_DIR    = "/cases/VANKO"
```

## Step 6 — Run the autonomous investigation

```bash
python orchestrator.py --output-dir ./findings
```

Watch the agent reason and call tools in real time on stderr.
Investigation takes approximately **15–30 minutes**.

## Step 7 — Review findings

```bash
# Structured JSON report
cat findings/findings_report.json

# Full audit trail
cat findings/agent_execution_log.jsonl
```

## Optional — Run as a Claude Code MCP server

```bash
claude mcp add sift-forensic \
  -e SIFT_HOST=$env:SIFT_HOST \
  -e SIFT_PORT=22 \
  -e SIFT_USER=sansforensics \
  -e SIFT_PASS=forensics \
  -- sift-mcp

# Then in Claude Code:
# "Mount the VANKO image and investigate for signs of compromise"
```

## Troubleshooting

| Problem | Solution |
|---|---|
| SSH connection refused | Check VM is running: `vmrun list` |
| ewfmount: image not found | Verify evidence path: check `setup_sift_vm.py` output |
| log2timeline is slow | Normal — 30–60 min for 119 GB. Agent continues other analysis while waiting. |
| YARA rules not found | SIFT includes rules at `/opt/remnux-rules`; pass `rules_dir` param to `yara_scan` |
| `find_suspicious_executables` returns 0 | Image may not be mounted. Call `mount_image` tool first. |

## Demo video

https://youtu.be/ySjuSR9AP3Q
