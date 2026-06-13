# Built With

## Core agent framework
- **Claude Code** (primary agentic IDE / MCP host)
- **Custom MCP Server** (architectural pattern) — `sift-forensic-mcp` exposes 18 typed forensic tools via stdio transport

## AI / LLM
- **gpt-5.4-mini** via OpenAI-compatible API (`https://api.456478.xyz/`)
- **OpenAI Python SDK** (`openai>=1.0.0`) — tool-use loop, `finish_reason=="tool_calls"` dispatch

## Forensic platform
- **SIFT Workstation 2026** (Ubuntu 22.04) — 200+ IR tools pre-installed
- **ewfmount** — EWF/E01 forensic image mounting (read-only FUSE)
- **kpartx** — partition mapping from EWF image
- **ntfs-3g** — NTFS read-only mount
- **log2timeline / plaso** — supertimeline creation
- **YARA** — malware signature scanning
- **Regripper** — Windows registry hive parsing
- **python-evtx** — Windows Event Log (EVTX) parsing
- **python-registry** — registry traversal
- **Volatility** (available, not used in submission run)

## Infrastructure
- **VMware Workstation Pro 17** — SIFT VM host
- **asyncssh** — SSH transport from MCP server to SIFT VM
- **Python 3.10+** — orchestrator and MCP server runtime

## Demo pipeline
- **VoxCPM2** (`openbmb/VoxCPM2`, 2B diffusion TTS) — AI narration voice
- **PyTorch 2.12 + CUDA 12.6** — VoxCPM inference on RTX 4060 Laptop GPU
- **Pillow** — slide rendering (1920×1080 PNG)
- **ffmpeg** — video assembly and encoding (H.264 + AAC)
- **Headless Chromium** — HTML cover → PNG rendering

## Tags (Devpost Built-With)
`Claude Code` · `Custom MCP Server` · `SIFT Workstation` · `gpt-5.4-mini` · `OpenAI API` · `Model Context Protocol` · `asyncssh` · `ewfmount` · `YARA` · `log2timeline` · `Regripper` · `python-evtx` · `VMware Workstation` · `VoxCPM2` · `PyTorch` · `CUDA` · `ffmpeg` · `Python`
