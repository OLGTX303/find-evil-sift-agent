# FIND EVIL! — SIFT Forensic AI Agent

> Autonomous incident response agent that mounts a 119 GB forensic disk image, hunts malware and anti-forensics through 18 MCP tools on a SIFT Workstation VM, and writes a courtroom-ready report — with no human in the loop.

**Demo video:** https://youtu.be/ySjuSR9AP3Q  
**License:** MIT  
**Architecture pattern:** Custom MCP Server

---

## What it does

The agent receives a single prompt ("investigate the VANKO disk image") and autonomously:

1. Mounts the EWF forensic image read-only via `ewfmount` + `ntfs-3g`
2. Enumerates users, recent files, and installed software
3. Scans for suspicious executables in `%TEMP%`, `%AppData%`, and `Downloads`
4. Parses the Windows registry for persistence mechanisms
5. Extracts and correlates Windows Event Log logon events
6. Runs YARA malware signatures across the image
7. Identifies Prefetch artifacts proving anti-forensic tool execution
8. Produces `findings/findings_report.json` with confidence-scored IOCs

On the VANKO case it found **8 confirmed findings** including WiFi packet capture, evidence destruction (SDelete), an encrypted volume (VeraCrypt FORMAT confirmed), a typosquatted RAT, and identified the subject as `anthony.vanko@gmail.com`.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│  Windows Host (analyst workstation)                       │
│                                                           │
│  orchestrator.py  ←→  gpt-5.4-mini (OpenAI-compat API)   │
│        │                                                  │
│  sift-forensic-mcp  (18 MCP tools, stdio transport)       │
│        │  asyncssh (TCP 22)                               │
└────────┼─────────────────────────────────────────────────┘
         │
┌────────▼─────────────────────────────────────────────────┐
│  SIFT Workstation 2026 VM  (Ubuntu 22.04, VMware NAT)     │
│                                                           │
│  /cases/VANKO/surface_physical.E01                        │
│       ewfmount → /mnt/ewf/ewf1                            │
│       kpartx   → /dev/mapper/loop0p3                      │
│       ntfs-3g  → /mnt/windows/  (READ-ONLY)               │
│                                                           │
│  SIFT tools: ewfmount, log2timeline, yara,                │
│              regripper, python-evtx, strings, file        │
└──────────────────────────────────────────────────────────┘
```

See [`docs/architecture.md`](docs/architecture.md) for the full tool inventory and security boundary breakdown.

---

## Prerequisites

- Windows 10/11 host with **VMware Workstation Pro 17+**
- **Python 3.10+**
- OpenAI-compatible API key (or set `OPENAI_BASE_URL` to a local endpoint)
- ~150 GB free disk space (119 GB evidence + SIFT VM)
- 8 GB+ RAM (16 GB recommended)

---

## Quick start

### 1. Clone and install

```bash
git clone https://github.com/OLGTX303/find-evil-sift-agent
cd find-evil-sift-agent
pip install -e .
```

### 2. Import the SIFT Workstation VM

```powershell
$ovftool = "C:\Program Files (x86)\VMware\VMware Workstation\OVFTool\ovftool.exe"
& $ovftool --acceptAllEulas --name="SIFT-2026" sift-2026-04-22.ova F:\SIFT-VM\
```

### 3. Place evidence files

```
find\VANKO\surface_physical.E01  (through .E21)
find\VANKO\vanko-c-drive.CYLR.7z
```

### 4. Start and configure the SIFT VM

```bash
python setup_sift_vm.py
# Starts the VM, enables SSH, copies evidence — prints the VM IP at the end
```

### 5. Set environment variables

```powershell
$env:OPENAI_API_KEY    = "sk-..."
$env:OPENAI_BASE_URL   = "https://api.openai.com/v1"   # or your endpoint
$env:SIFT_HOST         = "192.168.x.x"   # from setup_sift_vm.py
$env:SIFT_PORT         = "22"
$env:SIFT_USER         = "sansforensics"
$env:SIFT_PASS         = "forensics"
$env:EVIDENCE_DIR      = "/cases/VANKO"
```

### 6. Run the investigation

```bash
python orchestrator.py --output-dir ./findings
```

The agent prints reasoning and tool calls to stderr in real time.  
Investigation takes **15–30 minutes** (log2timeline on 119 GB runs in background).

### 7. Review results

```bash
# Structured findings report
cat findings/findings_report.json

# Full timestamped audit trail
cat findings/agent_execution_log.jsonl
```

---

## MCP server (standalone — use with Claude Code)

```bash
# Register the MCP server in Claude Code
claude mcp add sift-forensic \
  -e SIFT_HOST=192.168.x.x \
  -e SIFT_PORT=22 \
  -e SIFT_USER=sansforensics \
  -e SIFT_PASS=forensics \
  -- sift-mcp

# Then in Claude Code:
# "Mount the VANKO image and find evil"
```

---

## Repository layout

```
sift-agent/
├── orchestrator.py          ← Autonomous IR agent (gpt-5.4-mini)
├── setup_sift_vm.py         ← One-time VM setup
├── pyproject.toml
├── LICENSE                  ← MIT
├── src/sift_mcp/
│   ├── server.py            ← MCP server (stdio transport)
│   ├── tools.py             ← 18 forensic tool implementations
│   └── ssh_client.py        ← asyncssh helper with sudo support
├── findings/
│   ├── findings_report.json         ← Structured IOC report
│   └── agent_execution_log.jsonl    ← Full timestamped audit trail
├── demo/
│   ├── demo_find_evil.mp4           ← Narrated demo video (local copy)
│   ├── mcp_session.json             ← Real captured tool output
│   └── cover_3x2.png                ← Devpost thumbnail (1200×800)
└── docs/
    ├── architecture.md      ← Component diagram + security boundaries
    ├── accuracy_report.md   ← Finding accuracy + false positive analysis
    ├── dataset.md           ← Evidence dataset documentation
    └── try-it-out.md        ← Judges guide
```

---

## Docs

| Document | Contents |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Component diagram, tool inventory, security boundaries, guardrails |
| [`docs/accuracy_report.md`](docs/accuracy_report.md) | 8 findings vs ground truth, false positives, evidence integrity |
| [`docs/dataset.md`](docs/dataset.md) | VANKO case dataset, provenance, integrity hashes |
| [`docs/try-it-out.md`](docs/try-it-out.md) | Step-by-step judges guide with troubleshooting |

---

## License

MIT — see [LICENSE](LICENSE).
