# FIND EVIL! — SIFT Forensic AI Agent

## Project structure

```
sift-agent/
├── orchestrator.py          ← Main autonomous IR agent (gpt-5.4-mini via OpenAI-compatible API)
├── setup_sift_vm.py         ← One-time VM setup: start, share evidence, install deps
├── src/sift_mcp/
│   ├── server.py            ← MCP server exposing SIFT tools
│   ├── tools.py             ← 18 forensic tool implementations (SSH → SIFT VM)
│   └── ssh_client.py        ← asyncssh helper with sudo support
└── findings/                ← Auto-created: agent_execution_log.jsonl + findings_report.json
```

## Evidence (VANKO case)
- `find/VANKO/surface_physical.E01-E21` — Microsoft Surface 3 disk image (119GB EWF)
- `find/VANKO/vanko-c-drive.CYLR.7z` — Cellebrite C-drive extraction
- `find/sift-2026-04-22.ova` — SIFT Workstation VM

## One-time setup

```bash
# 1. Import OVA (already done via ovftool)
# VMX at: F:\5Gcase\hackton\SIFT-VM\SIFT-2026\SIFT-2026.vmx

# 2. Install sift-agent
pip install -e .

# 3. Start and configure SIFT VM
python setup_sift_vm.py

# 4. Set environment
set OPENAI_API_KEY=your_key
set OPENAI_BASE_URL=https://api.456478.xyz/
set SIFT_HOST=<vm_ip>
set SIFT_PORT=22      # or 2222 if using NAT
set SIFT_USER=sansforensics
set SIFT_PASS=forensics
set EVIDENCE_DIR=/cases/VANKO
```

## Running the investigation

```bash
python orchestrator.py --output-dir ./findings
```

The agent will autonomously:
1. Mount the E01 image via ewfmount
2. Enumerate users and system info
3. Scan for suspicious executables
4. Parse registry Run keys (persistence)
5. Extract logon events from Security.evtx
6. Run YARA malware detection
7. Build a timeline with log2timeline
8. Produce `findings/findings_report.json`

## MCP server (standalone)

```bash
# Register in Claude Code
claude mcp add sift-forensic -e SIFT_HOST=<ip> -e SIFT_PORT=22 -- sift-mcp

# Then ask Claude: "Mount the VANKO image and find evil"
```

## Architecture

```
┌─────────────────────────────────────────────┐
│  Windows Host (Claude Code)                  │
│  orchestrator.py + gpt-5.4-mini (OpenAI-compat API)  │
│  ┌─────────────────────────────────────┐    │
│  │  sift-forensic-mcp (stdio MCP)      │    │
│  │  18 forensic tool definitions        │    │
│  └──────────────┬──────────────────────┘    │
└─────────────────┼───────────────────────────┘
                  │ asyncssh (port 22/2222)
┌─────────────────▼───────────────────────────┐
│  SIFT Workstation VM (VMware NAT)            │
│  Ubuntu 22.04 + 200+ IR tools               │
│  ┌───────────────────────────────────────┐  │
│  │  /cases/VANKO/surface_physical.E01    │  │
│  │  ewfmount → /mnt/ewf/ewf1            │  │
│  │  kpartx   → /dev/mapper/loop0p3      │  │
│  │  /mnt/windows/ (NTFS mounted)         │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Security boundaries
- MCP server runs on host; SIFT VM is isolated in VMware NAT
- Evidence files are read-only (ewfmount uses FUSE read-only by default)
- SSH credentials are environment variables, never hardcoded in submission
- Agent cannot modify evidence (only reads via mounted image)

## Judging notes
- Architecture: Custom MCP Server approach (type-safe tool exposure)
- Self-correction: agent retries on error, tries alternative paths
- Audit trail: structured JSONL log with timestamps at every step
- False positive handling: confidence scores per finding, `false_positive_notes` in report
