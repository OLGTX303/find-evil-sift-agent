# Architecture — FIND EVIL! SIFT Forensic AI Agent

## Overview

```
┌────────────────────────────────────────────────────────────────┐
│  SECURITY BOUNDARY: Windows Host (analyst workstation)          │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  orchestrator.py                                          │  │
│  │  - Claude claude-sonnet-4-6 (Anthropic API)                      │  │
│  │  - 40-iteration autonomous investigation loop             │  │
│  │  - AuditLogger → findings/agent_execution_log.jsonl       │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                        │  Python in-process MCP call            │
│  ┌─────────────────────▼───────────────────────────────────┐   │
│  │  sift-forensic-mcp  (MCP server, stdio transport)         │   │
│  │  18 tools: mount_image, list_users, run_log2timeline,     │   │
│  │  yara_scan, parse_evtx, get_run_keys, hash_file, …       │   │
│  └────────────────────┬────────────────────────────────────┘   │
│                        │  asyncssh (TCP 22/2222)                │
└────────────────────────┼───────────────────────────────────────┘
                SECURITY BOUNDARY: VMware NAT network
┌───────────────────────▼────────────────────────────────────────┐
│  SIFT Workstation 2026 VM  (Ubuntu 22.04, VMware NAT)           │
│  Read-only evidence mount (ewfmount FUSE, no write perm)        │
│                                                                 │
│  /cases/VANKO/surface_physical.E01  ←── forensic image          │
│       │                                                         │
│  ewfmount ──→ /mnt/ewf/ewf1                                     │
│  kpartx   ──→ /dev/mapper/loop0p3  (NTFS Windows partition)     │
│  ntfs-3g  ──→ /mnt/windows/        (read-only mount)            │
│                                                                 │
│  SIFT Tools used:                                               │
│    ewfmount     – E01/EWF image mounting                        │
│    log2timeline – Supertimeline creation (plaso)               │
│    psort        – Timeline query/export                         │
│    yara         – Malware signature scanning                    │
│    regripper    – Registry hive parsing                         │
│    python-evtx  – EVTX event log parsing                        │
│    python-registry – Registry traversal                         │
│    strings/file – Binary analysis                               │
└────────────────────────────────────────────────────────────────┘
```

## Data flow

1. `orchestrator.py` sends initial prompt to Claude claude-sonnet-4-6
2. Claude reasons about investigation steps, calls MCP tools
3. MCP server translates tool calls → SSH commands on SIFT VM
4. SIFT VM executes commands against read-only mounted image
5. Results return to Claude for reasoning and next steps
6. Each step appended to `agent_execution_log.jsonl`
7. At end_turn, Claude emits structured JSON findings report

## Security boundaries

| Boundary | Enforcement |
|---|---|
| Evidence read-only | ewfmount uses FUSE read-only (`-o ro`) |
| SIFT VM network isolation | VMware NAT; only SSH port exposed to host |
| API keys | Environment variables only; never in code |
| Agent cannot self-modify | No file-write tools exposed via MCP |
| Audit trail immutability | JSONL append-only log |

## Autonomous reasoning capabilities

- **Failure recovery**: if tool returns error, agent tries alternative (e.g., regripper fallback)
- **Path discovery**: uses `find` commands when expected paths not found
- **Self-correction**: if YARA finds nothing, agent revisits with broader scope
- **Async awareness**: starts log2timeline, continues other analysis, polls status
- **Confidence scoring**: each finding rated 0.0–1.0; low-confidence items flagged

## Tool inventory

| Category | Tools | Count |
|---|---|---|
| Evidence setup | setup_evidence, mount_image, unmount_image | 3 |
| File system | list_users, list_recent_files, find_suspicious_executables, extract_file | 4 |
| Timeline | run_log2timeline, get_timeline_status, run_psort | 3 |
| Registry | parse_registry, get_run_keys | 2 |
| Malware detection | yara_scan, hash_file, check_known_malware_hashes | 3 |
| Event logs | parse_evtx, get_logon_events | 2 |
| Network artifacts | extract_network_artifacts | 1 |
| **Total** | | **18** |
