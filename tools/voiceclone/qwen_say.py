#!/usr/bin/env python3
"""Render narration with Qwen3-TTS, cloned from Dave's reference recording.

Loads the model once and renders a batch of lines, so a 16-segment video is one
model load rather than sixteen. Runs in the voiceclone venv (mlx-audio).

    qwen_say.py jobs.json
    jobs.json: {"ref_audio": ".../dave.wav", "ref_text": "...",
                "jobs": [{"text": "...", "out": ".../01.wav"}, ...]}

`[[slnc N]]` pause markers are honoured: each line is split at the markers, the
phrases are voiced separately, and exactly N ms of silence is placed between them.
"""
import json
import re
import sys

import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-8bit"
SLNC = re.compile(r"\[\[slnc (\d+)\]\]")


def phrases(text):
    """[(phrase, pause_ms_before)] with pause markers removed."""
    out, pause = [], 0
    for k, chunk in enumerate(SLNC.split(text)):
        if k % 2:
            pause += int(chunk)
        elif chunk.strip():
            out.append((chunk.strip(), pause if out else 0))
            pause = 0
    return out


def main():
    spec = json.load(open(sys.argv[1]))
    model = load_model(MODEL)
    for job in spec["jobs"]:
        pieces, sr = [], None
        for phrase, pause in phrases(job["text"]):
            audio = []
            for r in model.generate(text=phrase, ref_audio=spec["ref_audio"],
                                    ref_text=spec["ref_text"], lang_code="en"):
                audio.append(np.asarray(r.audio, dtype=np.float32))
                sr = r.sample_rate
            if pause:
                pieces.append(np.zeros(int(sr * pause / 1000), dtype=np.float32))
            pieces.append(np.concatenate(audio))
        sf.write(job["out"], np.concatenate(pieces), sr)
        print(f"  wrote {job['out']}", flush=True)


if __name__ == "__main__":
    main()
