#!/usr/bin/env python3
"""Synthesize per-scene narration WAVs with VoxCPM2 on CUDA.

Run with the CUDA venv that already has the full voxcpm stack:
  F:\\5Gcase\\hackton\\fraudsentinel\\demotools\\fraudsentinel-demo\\.venv312\\Scripts\\python.exe synth_voxcpm.py

Voice is locked on the first chunk, then cloned (prompt_wav + prompt_text) for
every following chunk so the narrator never changes across all scenes.
"""
import json
import re
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from voxcpm import VoxCPM

DEMO = Path(__file__).parent
AUDIO = DEMO / "audio"
AUDIO.mkdir(exist_ok=True)

CFG = 2.0
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
STEPS = 30 if DEVICE == "cuda" else 16
REF_PATH = AUDIO / "_ref_voice.wav"


def split_text(text: str, max_chars: int = 360) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.replace("\n", " ")) if s.strip()]
    chunks, cur = [], ""
    for s in sentences:
        if not cur:
            cur = s
        elif len(cur) + 1 + len(s) <= max_chars:
            cur = f"{cur} {s}"
        else:
            chunks.append(cur)
            cur = s
    if cur:
        chunks.append(cur)
    return chunks


def main():
    scenes = json.loads((DEMO / "script.json").read_text(encoding="utf-8"))["scenes"]

    print(f"Loading VoxCPM2 on {DEVICE} (steps={STEPS})…")
    t0 = time.time()
    model = VoxCPM.from_pretrained(
        "openbmb/VoxCPM2", load_denoiser=False, optimize=False, device=DEVICE,
    )
    sr = model.tts_model.sample_rate
    print(f"  loaded in {time.time()-t0:.0f}s  ·  sr={sr}")

    ref_text = None  # set once chunk 1 locks the voice
    pause = np.zeros(int(sr * 0.18), dtype=np.float32)  # small gap between chunks within a scene
    total = 0.0

    for s in scenes:
        out = AUDIO / f"{s['id']}.wav"
        if out.exists():
            d = sf.info(str(out)).frames / sr
            print(f"  [skip] {s['id']}  ({d:.1f}s)")
            total += d
            if ref_text is None and REF_PATH.exists():
                # recover ref_text from first scene's first chunk
                ref_text = split_text(scenes[0]["narration"])[0]
            continue

        chunks = split_text(s["narration"])
        print(f"Synthesizing {s['id']}  ({len(chunks)} chunk(s))…")
        t0 = time.time()
        parts = []
        for ch in chunks:
            if ref_text is None:
                wav = model.generate(text=ch, cfg_value=CFG, inference_timesteps=STEPS,
                                     normalize=True, retry_badcase=True)
                sf.write(str(REF_PATH), wav, sr)
                ref_text = ch
            else:
                wav = model.generate(text=ch, prompt_wav_path=str(REF_PATH), prompt_text=ref_text,
                                     cfg_value=CFG, inference_timesteps=STEPS,
                                     normalize=True, retry_badcase=True)
            peak = float(np.max(np.abs(wav))) or 1.0
            if peak > 0.97:
                wav = wav * (0.97 / peak)
            # 5 ms edge fades to kill boundary clicks
            n = max(1, int(sr * 0.005))
            ramp = np.linspace(0, 1, n, dtype=np.float32)
            wav[:n] *= ramp
            wav[-n:] *= ramp[::-1]
            parts.append(wav)
            parts.append(pause)

        scene_wav = np.concatenate(parts)
        sf.write(str(out), scene_wav, sr)
        d = len(scene_wav) / sr
        total += d
        print(f"  {s['id']}  {d:.1f}s  (gen {time.time()-t0:.0f}s)")

    print(f"\nDONE. narration ≈ {total:.0f}s ({total/60:.1f} min) across {len(scenes)} scenes")


if __name__ == "__main__":
    main()
