#!/usr/bin/env python3
"""Chunked TTS narration synthesis.

Reads paragraphs.txt (one paragraph per non-empty line), synthesizes each
paragraph as a separate MP3 via the tts CLI, then concatenates them with
short silences into narration.mp3. Also writes offsets.json mapping each
paragraph to its start time in the final audio.

Why chunked: single-shot TTS of >~400 CJK chars corrupts the middle of the
audio (whisper transcribes garbage like "Reset with 104"). Per-paragraph
synthesis is reliable.

Usage:
    python3 synth.py [--src DIR] [--voice VOICE] [--lang zh] [--speed 115] [--gap 0.5]

Outputs in DIR: chunks/pNN.mp3, narration.mp3, offsets.json, chunk_durs.json
"""
import argparse, json, os, subprocess, sys

TTS = "/opt/hatch/bin/tts"

def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(f"CMD FAILED: {' '.join(cmd)}\n{r.stderr[-2000:]}", file=sys.stderr)
        sys.exit(1)
    return r

def probe_dur(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", path]).stdout.strip()
    return float(out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".", help="working dir containing paragraphs.txt")
    ap.add_argument("--voice", default="avocado_v2:vd2_exacting_pillar")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--speed", default="115")
    ap.add_argument("--gap", type=float, default=0.5, help="silence seconds between paragraphs")
    args = ap.parse_args()

    src = os.path.abspath(args.src)
    os.makedirs(os.path.join(src, "chunks"), exist_ok=True)
    paras = [l.strip() for l in open(os.path.join(src, "paragraphs.txt"), encoding="utf-8")
             if l.strip()]
    if not paras:
        print("paragraphs.txt is empty", file=sys.stderr); sys.exit(1)

    # TTS emits 24000Hz mono mp3; build silence to match exactly
    silence = os.path.join(src, "chunks", "silence.mp3")
    run(["ffmpeg", "-v", "error", "-f", "lavfi",
         "-i", "anullsrc=r=24000:cl=mono", "-t", str(args.gap),
         "-q:a", "9", "-acodec", "libmp3lame", silence, "-y"])

    durs, offsets = {}, {}
    for i, para in enumerate(paras, 1):
        key = f"p{i:02d}"
        chunk = os.path.join(src, "chunks", f"{key}.mp3")
        print(f"[{key}] {para[:36]}...", flush=True)
        for attempt in (1, 2):
            r = run([TTS, "speak", "--voice", args.voice, "--language", args.lang,
                     "--speed", args.speed, "--output", chunk, "--text-stdin"],
                    input=para)
            d = probe_dur(chunk)
            # sanity: expect roughly 1.5-8 chars/sec; retry once if wildly off
            cps = len(para) / max(d, 0.1)
            if 1.0 < cps < 9.0 or attempt == 2:
                break
            print(f"  suspicious pace ({cps:.1f} chars/s), retrying...", flush=True)
        durs[key] = round(d, 2)
        print(f"  -> {d:.1f}s ({len(para)/d:.1f} chars/s)")

    # concat with gaps, re-encode to uniform params (never -c copy: mixed
    # mp3 headers cause decode failures downstream)
    lst = os.path.join(src, "chunks", "list.txt")
    with open(lst, "w") as f:
        for i in range(1, len(paras) + 1):
            f.write(f"file 'p{i:02d}.mp3'\n")
            if i < len(paras):
                f.write("file 'silence.mp3'\n")
    narration = os.path.join(src, "narration.mp3")
    run(["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
         "-ar", "24000", "-ac", "1", "-acodec", "libmp3lame", narration, "-y"])

    t = 0.0
    for i in range(1, len(paras) + 1):
        key = f"p{i:02d}"
        offsets[key] = round(t, 2)
        t += durs[key] + (args.gap if i < len(paras) else 0)
    json.dump(offsets, open(os.path.join(src, "offsets.json"), "w"), indent=1)
    json.dump(durs, open(os.path.join(src, "chunk_durs.json"), "w"), indent=1)
    total = probe_dur(narration)
    print(f"done: {len(paras)} paragraphs, narration.mp3 = {total:.1f}s")

if __name__ == "__main__":
    main()
