#!/usr/bin/env python3
"""Assemble the final demo video: each slide PNG timed to its narration WAV.

Pipeline per scene:  loop slide image  +  narration audio (+ tail padding)
Then concatenate all scene clips into demo_find_evil.mp4.
"""
import json
import subprocess
from pathlib import Path

import soundfile as sf

DEMO = Path(__file__).parent
SLIDES = DEMO / "slides"
AUDIO = DEMO / "audio"
CLIPS = DEMO / "clips"
PREBUILT = DEMO / "prebuilt"
CLIPS.mkdir(exist_ok=True)

TAIL = 0.7          # seconds of silence after each narration line
FPS = 25
OUT = DEMO / "demo_find_evil.mp4"


def dur(wav: Path) -> float:
    info = sf.info(str(wav))
    return info.frames / info.samplerate


def vdur(mp4: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nokey=1:noprint_wrappers=1", str(mp4)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def run(cmd):
    subprocess.run(cmd, check=True)


def main():
    scenes = json.loads((DEMO / "script.json").read_text(encoding="utf-8"))["scenes"]
    concat = DEMO / "_concat.txt"
    lines, total = [], 0.0

    for s in scenes:
        sid = s["id"]

        # Pre-rendered animated scenes (e.g. the live MCP agent terminal) ship as
        # a finished clip with their own audio — drop them straight into the reel.
        prebuilt = PREBUILT / f"{sid}.mp4"
        if prebuilt.exists():
            d = vdur(prebuilt)
            total += d
            lines.append(f"file '{prebuilt.as_posix()}'")
            print(f"  {sid}: {d:.1f}s  (prebuilt clip)")
            continue

        slide = SLIDES / f"{sid}.png"
        wav = AUDIO / f"{sid}.wav"
        clip = CLIPS / f"{sid}.mp4"
        if not slide.exists() or not wav.exists():
            raise SystemExit(f"missing asset for {sid}: slide={slide.exists()} wav={wav.exists()}")
        d = dur(wav) + TAIL
        total += d
        run([
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", str(FPS), "-i", str(slide),
            "-i", str(wav),
            "-filter_complex", f"[1:a]apad=pad_dur={TAIL},aresample=48000[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-tune", "stillimage",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-t", f"{d:.3f}",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            str(clip),
        ])
        lines.append(f"file '{clip.as_posix()}'")
        print(f"  {sid}: {d:.1f}s")

    concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
    run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        str(OUT),
    ])
    print(f"\nDONE -> {OUT}  ·  {total:.0f}s ({total/60:.1f} min)")


if __name__ == "__main__":
    main()
