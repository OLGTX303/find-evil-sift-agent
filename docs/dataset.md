# Dataset Documentation — VANKO Case

## Source

| Field | Value |
|---|---|
| Dataset name | VANKO (Microsoft Surface 3 forensic image) |
| Acquired by | Ovie Carroll, DFIR.training |
| Acquisition date | 2016-11-04 13:47–14:32 UTC |
| Acquisition tool | FTK Imager (EWF/E01 format) |
| Original distribution | SANS FOR508 / DFIR.training challenge |
| Access | Publicly available training dataset |

## Image details

| Field | Value |
|---|---|
| Format | Expert Witness Format (EWF), segments `.E01`–`.E21` |
| Total size | 119 GB (compressed E01 segments) |
| Device | Microsoft Surface 3 (Samsung MDGAGC SSD, serial `e65f5f86`) |
| OS | Windows 10 (build acquired Nov 2016) |
| Partitions | GPT — EFI system + Windows NTFS (mounted as `/mnt/windows/`) |
| MD5 | `4032d556cc866c23f1e797410e95603c` |
| SHA-1 | `e0e72dfcef167dd358813726e82f6c235bc85ce7` |

## Mount procedure

```bash
# On SIFT Workstation VM
sudo ewfmount /cases/VANKO/surface_physical.E01 /mnt/ewf/
sudo kpartx -av /mnt/ewf/ewf1
# → creates /dev/mapper/loop0p2 (EFI) and loop0p3 (Windows NTFS)
sudo ntfs-3g -o ro /dev/mapper/loop0p3 /mnt/windows/
```

The image is mounted **read-only** at every step. `ewfmount` uses FUSE in read-only mode; `ntfs-3g` is invoked with `-o ro`. The original `.E01` segments are never written to.

## Key artifacts present

| Artifact | Path | Significance |
|---|---|---|
| Primary user profile | `/mnt/windows/Users/PC User/` | Subject identity: `anthony.vanko@gmail.com` |
| Starbucks packet capture | `Users/PC User/Documents/starbucks pcap.pcap` | WiFi surveillance evidence |
| Dropper | `Users/PC User/AppData/Local/Temp/set_PxRcHIFy.exe` | MD5: `6f047f29414952777ace6d1cf5b598bc` |
| Typosquat RAT | `Users/PC User/Downloads/NETWIORK LICENSE SERVER 3.4.1.exe` | HTTP/FTP exfil capability |
| SDelete binaries | `Windows/System32/sdelete.exe` + `sdelete64.exe` | Anti-forensics deployment |
| VeraCrypt setup | `Users/PC User/Downloads/VeraCrypt Setup 1.17.exe` | Encrypted volume creation |
| Prefetch directory | `Windows/Prefetch/*.pf` | Execution proof for SDelete, VeraCrypt, NetStumbler |
| Security log on Desktop | `Users/PC User/Desktop/security.evtx` | 26,737 events — self-monitoring |
| NinaResearch collection | `Users/PC User/Documents/NinaResearch/` | Targeted intelligence gathering |
| Weaponization documents | `Users/PC User/Documents/Research to Weaponize the Ion Thruster.docx` | Sensitive research material |

## Reproducibility

The agent can be re-run against the same image and will produce identical findings because:
- The image is read-only and its hash is verified before investigation
- All tool commands are deterministic (no randomized output)
- The LLM temperature is 0 (default for tool-use completions)

Raw tool outputs from the investigation are preserved in [`demo/mcp_session.json`](../demo/mcp_session.json) for auditing without re-running the full pipeline.
