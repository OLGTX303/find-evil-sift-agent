# FIND EVIL! — Demo video pipeline

Builds `demo_find_evil.mp4`: a ~3.5 min narrated walkthrough of the autonomous
forensic IR agent, including a **live MCP agent terminal scene** driven by real
tool output captured from the mounted VANKO image.

## Pipeline

| Step | Script | Output |
|------|--------|--------|
| 1. Narration script | `script.json` | 13 scenes (title → case → architecture → **live agent run** → 8 findings → results) |
| 2. Slides | `make_slides.py` | `slides/*.png` (1920×1080) |
| 3. Voice | `synth_voxcpm.py` | `audio/*.wav` — VoxCPM2 on CUDA; one voice locked on chunk 1 and cloned for every scene |
| 4. Real MCP session | `capture_session.py` | `mcp_session.json` — genuine tool calls/outputs over SSH to the live SIFT VM |
| 5. Agent terminal scene | `make_agent_scene.py` | `prebuilt/05b_agent_demo.mp4` — animated terminal replaying the real session |
| 6. Assemble | `build_video.py` | `demo_find_evil.mp4` |

## Rebuild

```bash
# slides (any Python with Pillow)
python make_slides.py

# narration — needs a CUDA env with the voxcpm stack
<cuda-venv>/python synth_voxcpm.py        # writes audio/*.wav
<cuda-venv>/python synth_voxcpm.py         # re-run is idempotent (skips existing)

# live agent scene (SIFT VM up + image mounted at /mnt/windows)
python capture_session.py                  # refresh mcp_session.json from real evidence
python make_agent_scene.py                 # build prebuilt/05b_agent_demo.mp4

# final reel
python build_video.py                      # -> demo_find_evil.mp4
```

## Notes

- The agent terminal scene shows **real data**: user list, 41 suspicious
  executables, the dropper's md5/sha256, the typosquat's HTTP/FTP exfil imports,
  and prefetch proof that SDelete / VeraCrypt / NetStumbler were executed.
- VoxCPM2 model is loaded from the local Hugging Face cache (`openbmb/VoxCPM2`),
  `load_denoiser=False`, `device=cuda`, 30 diffusion steps.
- `clips/` and `agent_frames/` are intermediate and git-ignored.
