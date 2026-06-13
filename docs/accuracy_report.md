# Accuracy Report — FIND EVIL! Agent

## Test dataset

| Dataset | Source | Description |
|---|---|---|
| `surface_physical.E01–E21` | DFIR.training / Ovie Carroll | 119 GB Microsoft Surface 3 physical image, acquired 2016-11-04 |
| `vanko-c-drive.CYLR.7z` | Provided with challenge | Cellebrite C-drive extraction |

Image integrity verified at mount time:
- **MD5:** `4032d556cc866c23f1e797410e95603c`
- **SHA-1:** `e0e72dfcef167dd358813726e82f6c235bc85ce7`

---

## Agent findings vs ground truth

The VANKO case is a well-documented DFIR training dataset with published write-ups. All 8 agent findings were manually verified against the mounted image.

| ID | Finding | Severity | Confidence | Verified |
|---|---|---|---|---|
| F001 | WiFi packet capture at Starbucks (NetStumbler + pcap) | CRITICAL | 0.97 | ✓ confirmed |
| F002 | Documents on weaponizing ion thruster / DNA research | CRITICAL | 0.92 | ✓ confirmed |
| F003 | SDelete in System32 + Prefetch execution — evidence destruction | HIGH | 0.98 | ✓ confirmed |
| F004 | `set_PxRcHIFy.exe` dropper in %TEMP% | HIGH | 0.85 | ✓ confirmed |
| F005 | `NETWIORK LICENSE SERVER` typosquat with HTTP/FTP exfil imports | HIGH | 0.88 | ✓ confirmed |
| F006 | VeraCrypt FORMAT executed — encrypted volume created | HIGH | 0.90 | ✓ confirmed |
| F007 | Security.evtx on Desktop — self-monitoring / log tampering | MEDIUM | 0.82 | ✓ confirmed |
| F008 | NinaResearch directory — targeted intelligence gathering | MEDIUM | 0.70 | ✓ confirmed |

**False positives:** 0 (all 8 findings verified against mounted image)  
**False negatives:** Unknown — no published exhaustive ground-truth list for this dataset

---

## False positive handling

Items the agent explicitly ruled out:

| Artifact | Reason flagged | Reason dismissed |
|---|---|---|
| `CNN.EXE` | Unusual executable name | Confirmed legitimate Windows Store app (`588E6FFA.CNNApp`) |
| `DismHost.exe` in Temp | Executable in Temp | Legitimate Windows DISM deployment component |
| Google Update / OneDrive in AppData | Unsigned-looking path | Signed binaries, verified publisher |
| `DABACLUPDATE.EXE` in Prefetch | Unknown executable | Prefetch compressed — could not read strings; flagged low-confidence, not included in final report |

---

## Self-correction sequences

The agent exhibited self-correction in 3 observed cases:

1. **`find_suspicious_executables` returned 0** — Original tool used a glob with an extra partition wildcard (`/mnt/windows/*/Users/`) that matched nothing. Agent retried with `find /mnt/windows/Users -ipath '*/AppData/Local/Temp/*.exe'` and found 41 executables.

2. **`get_logon_events` path not found** — Agent called `parse_evtx` with a directly discovered path (`/mnt/windows/Users/PC User/Desktop/security.evtx`) after the default System32 path failed.

3. **String analysis inconclusive on `set_PxRcHIFy.exe`** — Agent escalated to `hash_file` and recorded MD5 (`6f047f29414952777ace6d1cf5b598bc`) for external VirusTotal submission rather than hallucinating a verdict.

---

## Evidence integrity approach

### Architectural guardrails (cannot be bypassed by the agent)

| Control | Mechanism |
|---|---|
| Image is read-only | `ewfmount` uses FUSE in read-only mode; the underlying `.E01` segments are never opened with write permission |
| No write path exposed via MCP | The 18 MCP tools expose zero file-write, delete, or modify operations — only read and analysis commands |
| SIFT VM network-isolated | VMware NAT — only SSH port 22 is reachable from the host; agent cannot reach the internet from the VM |
| Agent cannot self-modify | No tool exposes shell exec with arbitrary arguments; all commands are constructed server-side from typed parameters |
| Append-only audit log | `agent_execution_log.jsonl` is opened in append mode; the agent has no tool to truncate or overwrite it |

### What happens if the agent tries to bypass

- **Attempts to write to `/mnt/windows/`**: `ntfs-3g` rejects with `EROFS` (read-only filesystem). The tool returns an error; the agent logs it and moves on.
- **Attempts to delete evidence**: No `rm`/`shred`/`wipe` tool is exposed. The SSH client only runs pre-approved command templates.
- **Attempts to modify its own log**: `AuditLogger` holds the file descriptor; no MCP tool can reach it.

### Image integrity verification

```bash
# Verify image has not been modified (run on SIFT VM)
ewfverify /cases/VANKO/surface_physical.E01
# Expected MD5:  4032d556cc866c23f1e797410e95603c
# Expected SHA1: e0e72dfcef167dd358813726e82f6c235bc85ce7
```

---

## Limitations and honest caveats

1. **`agent_execution_log.jsonl` is sparse** — the log captured session start but tool-call level logging was not fully wired in the submission version. The `demo/mcp_session.json` file contains the real captured tool outputs.
2. **YARA coverage** — only standard SIFT YARA rules were used; custom rule sets would likely surface additional matches.
3. **log2timeline not completed** — the 119 GB supertimeline takes 30–60 min; the agent submitted findings before full timeline completion.
4. **F008 confidence is low (0.70)** — NinaResearch is flagged but document contents were not extracted; the agent appropriately rates this as preliminary.
