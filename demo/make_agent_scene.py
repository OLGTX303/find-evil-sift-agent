#!/usr/bin/env python3
"""Render an animated 'live MCP agent session' terminal scene from REAL data
captured against the mounted VANKO image, and mux it with its narration WAV.

Output:  prebuilt/05b_agent_demo.mp4  (1920x1080, h264 + aac, timed to narration)

Usage:
  python make_agent_scene.py --preview      # render only the final frame to check
  python make_agent_scene.py                # render all frames + build the clip
"""
import argparse
import subprocess
from pathlib import Path

import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

DEMO = Path(__file__).parent
FRAMES = DEMO / "agent_frames"
PREBUILT = DEMO / "prebuilt"
WAV = DEMO / "audio" / "05b_agent_demo.wav"
OUT = PREBUILT / "05b_agent_demo.mp4"

W, H = 1920, 1080
BG     = (13, 17, 23)
TERM   = (8, 11, 16)
PANEL  = (22, 27, 34)
TEXT   = (220, 227, 233)
MUTED  = (139, 148, 158)
GREEN  = (63, 185, 80)
RED    = (248, 81, 73)
AMBER  = (210, 153, 34)
BLUE   = (88, 166, 255)
CYAN   = (86, 211, 200)
PURPLE = (188, 140, 255)
LINE   = (48, 54, 61)

Fp = "C:/Windows/Fonts/"
def font(n, s):
    return ImageFont.truetype(Fp + n, s)

MONO   = font("consola.ttf", 25)
MONOB  = font("consolab.ttf", 25)
HDR    = font("arialbd.ttf", 34)
SMALL  = font("arial.ttf", 26)
TINY   = font("arial.ttf", 24)

# ── real session, as colored segments per line ────────────────────────────────
# each line is a list of (text, color); [] = blank line
B = TEXT
def seg(*parts):
    return list(parts)

LINES = [
    seg(("$ ", GREEN), ("python orchestrator.py --case VANKO --mcp sift-forensic", TEXT)),
    [],
    seg(("[mcp]   ", BLUE), ("connected to sift-mcp  ·  18 forensic tools registered", MUTED)),
    seg(("[agent] ", CYAN), ("model gpt-5.4-mini   ·   goal: find evil on the VANKO image", MUTED)),
    [],
    seg(("› ", AMBER), ("list_users()", TEXT)),
    seg(("    → ", GREEN), ("users: ['PC User', 'Default', 'defaultprinter']", TEXT)),
    seg(("[agent] ", CYAN), ("'PC User' is the primary profile — pivoting there", MUTED)),
    [],
    seg(("› ", AMBER), ("find_suspicious_executables()", TEXT)),
    seg(("    → ", GREEN), ("41 executables in Temp / Downloads / Roaming", TEXT)),
    seg(("        • ", MUTED), ("AppData/Local/Temp/set_PxRcHIFy.exe   ", TEXT), ("← random-named dropper", RED)),
    seg(("        • ", MUTED), ("Downloads/NETWIORK LICENSE SERVER 3.4.1.exe   ", TEXT), ("← typosquat", RED)),
    seg(("        • ", MUTED), ("Downloads/netstumblerinstaller_0_4_0.exe", TEXT)),
    seg(("        • ", MUTED), ("Downloads/VeraCrypt Setup 1.17.exe", TEXT)),
    [],
    seg(("› ", AMBER), ("hash_file('…/Temp/set_PxRcHIFy.exe')", TEXT)),
    seg(("    → ", GREEN), ("md5    ", MUTED), ("6f047f29414952777ace6d1cf5b598bc", TEXT)),
    seg(("    → ", GREEN), ("sha256 ", MUTED), ("90cff67f8f08f54d803a2983b0924ef0…", TEXT)),
    [],
    seg(("› ", AMBER), ("extract_file('…/NETWIORK LICENSE SERVER 3.4.1.exe')", TEXT)),
    seg(("    → ", GREEN), ("imports: HttpOpenRequestW, HttpSendRequestW, FtpFindFirstFileA", TEXT)),
    seg(("    → ", GREEN), ("manifest: ", MUTED), ("requireAdministrator", RED)),
    seg(("[agent] ", CYAN), ("not a license server — HTTP/FTP exfiltration behind admin rights", AMBER)),
    [],
    seg(("› ", AMBER), ("extract_network_artifacts()   ", TEXT), ("# prefetch = proof of execution", MUTED)),
    seg(("    → ", GREEN), ("SDELETE.EXE-FBA93810.pf           ", TEXT), ("(anti-forensics)", RED)),
    seg(("    → ", GREEN), ("VERACRYPT FORMAT.EXE-6EA86AF5.pf  ", TEXT), ("(encrypted volume)", RED)),
    seg(("    → ", GREEN), ("NETSTUMBLER.EXE-C14B26F4.pf       ", TEXT), ("(wifi recon)", RED)),
    [],
    seg(("[agent] ", CYAN), ("converged — 8 findings written to findings_report.json", GREEN)),
    seg(("[done]  ", BLUE), ("evidence read-only · never modified · full JSONL audit trail", MUTED)),
]

# anchors = indices of non-blank lines (reveal points)
ANCHORS = [i for i, ln in enumerate(LINES) if ln]

PANEL_X0, PANEL_Y0, PANEL_X1, PANEL_Y1 = 70, 96, W - 70, H - 86
TXT_X = PANEL_X0 + 34
TXT_Y = PANEL_Y0 + 84
LH = 29


def base():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # header
    d.text((60, 24), "FIND EVIL!", font=HDR, fill=RED)
    d.text((300, 30), "Live MCP Agent Session", font=SMALL, fill=MUTED)
    d.text((W - 470, 30), "Case #20161104 — VANKO", font=font("consola.ttf", 26), fill=GREEN)
    # terminal panel
    d.rounded_rectangle([PANEL_X0, PANEL_Y0, PANEL_X1, PANEL_Y1], radius=14, fill=TERM, outline=LINE, width=2)
    # title bar
    d.rounded_rectangle([PANEL_X0, PANEL_Y0, PANEL_X1, PANEL_Y0 + 50], radius=14, fill=PANEL)
    for i, c in enumerate([RED, AMBER, GREEN]):
        d.ellipse([PANEL_X0 + 24 + i*30, PANEL_Y0 + 18, PANEL_X0 + 38 + i*30, PANEL_Y0 + 32], fill=c)
    d.text((PANEL_X0 + 150, PANEL_Y0 + 13), "sansforensics@sift: orchestrator.py — sift-mcp", font=font("consola.ttf", 23), fill=MUTED)
    # footer
    d.text((60, H - 54), "gpt-5.4-mini  +  SIFT Workstation  +  MCP", font=TINY, fill=MUTED)
    d.text((W - 560, H - 54), "github.com/OLGTX303/find-evil-sift-agent", font=TINY, fill=MUTED)
    return img, d


def render_state(n_anchors: int) -> Image.Image:
    """Render frame showing lines up to the n_anchors-th non-blank line."""
    img, d = base()
    last_idx = ANCHORS[n_anchors - 1] if n_anchors > 0 else -1
    y = TXT_Y
    cursor_xy = (TXT_X, TXT_Y)
    for i, line in enumerate(LINES[: last_idx + 1]):
        if line:
            x = TXT_X
            for text, color in line:
                d.text((x, y), text, font=MONO, fill=color)
                x += d.textlength(text, font=MONO)
            if i == last_idx:
                cursor_xy = (x + 4, y)
        y += LH
    # blinking cursor block at end of last line
    cx, cy = cursor_xy
    d.rectangle([cx, cy + 3, cx + 13, cy + 24], fill=GREEN)
    return img


def build_clip():
    FRAMES.mkdir(exist_ok=True)
    PREBUILT.mkdir(exist_ok=True)
    R = len(ANCHORS)
    dur = sf.info(str(WAV)).frames / sf.info(str(WAV)).samplerate
    tail = 0.7
    per = dur / R

    # frame 0 = just the prompt already typed (state 1); reveal the rest across narration
    paths = []
    for k in range(1, R + 1):
        p = FRAMES / f"f{k:02d}.png"
        render_state(k).save(p)
        paths.append((p, per))

    concat = DEMO / "_agent_frames.txt"
    lines = []
    for p, sec in paths:
        lines.append(f"file '{p.as_posix()}'")
        lines.append(f"duration {sec:.3f}")
    # last frame must be repeated (concat demuxer quirk) and held through the tail
    lines.append(f"file '{paths[-1][0].as_posix()}'")
    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-i", str(WAV),
        "-filter_complex", f"[1:a]apad=pad_dur={tail},aresample=48000[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-r", "25", "-fps_mode", "cfr", "-t", f"{dur + tail:.3f}",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        str(OUT),
    ], check=True)
    print(f"DONE -> {OUT}  ({dur + tail:.1f}s, {R} reveal steps)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true")
    args = ap.parse_args()
    if args.preview:
        FRAMES.mkdir(exist_ok=True)
        render_state(len(ANCHORS)).save(FRAMES / "_preview.png")
        print("wrote", FRAMES / "_preview.png")
    else:
        build_clip()
