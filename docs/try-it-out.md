# Try It Out — Judges Guide

## Prerequisites

- Windows 10/11 host with VMware Workstation Pro 17+
- Python 3.10+
- Anthropic API key
- ~150GB free disk space (evidence + VM)
- 8GB+ RAM recommended for SIFT VM

## Step 1 — Clone and install

```bash
git clone https://github.com/<your-repo>/sift-agent
cd sift-agent
pip install -e .
pip install anthropic asyncssh
```

## Step 2 — Import SIFT VM

```powershell
# Import OVA into VMware (takes ~20 min for 10GB OVA)
$ovftool = "C:\Program Files (x86)\VMware\VMware Workstation\OVFTool\ovftool.exe"
& $ovftool --acceptAllEulas --name="SIFT-2026" sift-2026-04-22.ova F:\SIFT-VM\
```

## Step 3 — Place evidence

Copy the VANKO evidence files to your machine:
```
find\VANKO\surface_physical.E01 through E21
find\VANKO\vanko-c-drive.CYLR.7z
```

## Step 4 — Configure and start SIFT VM

```bash
python setup_sift_vm.py
# This starts the VM, enables SSH, and copies evidence files
# Note the VM IP address printed at the end
```

## Step 5 — Set environment variables

```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
$env:SIFT_HOST = "192.168.x.x"   # from setup_sift_vm.py output
$env:SIFT_PORT = "22"
$env:SIFT_USER = "sansforensics"
$env:SIFT_PASS = "forensics"
$env:EVIDENCE_DIR = "/cases/VANKO"
```

## Step 6 — Run the autonomous investigation

```bash
python orchestrator.py --output-dir ./findings
```

Watch the agent reason and execute tools in real-time on stderr.
Investigation takes approximately 15–30 minutes.

## Step 7 — Review findings

```bash
# Structured JSON report
cat findings/findings_report.json

# Full audit trail
cat findings/agent_execution_log.jsonl | python -m json.tool --no-ensure-ascii | less
```

## Optional — Run as Claude Code MCP server

```bash
# Register with Claude Code
claude mcp add sift-forensic \
  -e SIFT_HOST=$SIFT_HOST \
  -e SIFT_PORT=22 \
  -e SIFT_USER=sansforensics \
  -e SIFT_PASS=forensics \
  -- sift-mcp

# Then in Claude Code chat:
# "Mount the VANKO image and investigate for signs of compromise"
```

## Troubleshooting

| Problem | Solution |
|---|---|
| SSH connection refused | Check VM is started: `vmrun list` |
| ewfmount: image not found | Verify evidence copied: `setup_sift_vm.py` |
| log2timeline slow | Normal — takes 30–60 min for 119GB image. Agent continues other analysis while waiting. |
| YARA rules not found | SIFT includes rules at `/opt/remnux-rules`; set `rules_dir` accordingly |
