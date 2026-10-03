#!/usr/bin/env python3
"""Word-level timestamps for narration audio.

Uses faster-whisper (CPU, int8) to transcribe narration.mp3 with
word_timestamps=True, writing words.json:
    [{"w": "word", "s": 12.34, "e": 12.56}, ...]

Needs the project venv that has faster_whisper installed, e.g.:
    VENV=~/workspace/diode-video/.venv
    NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 $VENV/bin/python bin/words.py --src DIR

Whisper mis-hears some words (homophones, "O FF" for 欧米伽) — that is fine;
we only need TIMINGS. Display text always comes from paragraphs.txt.
If a long stretch transcribes as repetitive English garbage ("Talk power",
"Reset with 104"), the TTS audio itself is corrupt: re-run synth.py
(per-paragraph synthesis avoids this).

Usage:
    python3 words.py [--src DIR] [--model small]
"""
import argparse, json, os, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".")
    ap.add_argument("--model", default="small")
    args = ap.parse_args()
    src = os.path.abspath(args.src)
    audio = os.path.join(src, "narration.mp3")
    if not os.path.exists(audio):
        print(f"missing {audio}", file=sys.stderr); sys.exit(1)
    from faster_whisper import WhisperModel
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio, language="zh", word_timestamps=True)
    words = [{"w": w.word, "s": round(w.start, 2), "e": round(w.end, 2)}
             for seg in segments for w in (seg.words or [])]
    if not words:
        print("no words transcribed", file=sys.stderr); sys.exit(1)
    # garbage check: >30s of a single repeated token means corrupt TTS audio
    from collections import Counter
    top, n = Counter(w["w"] for w in words).most_common(1)[0]
    if n > 60 and len(top.strip()) > 2:
        print(f"WARNING: token {top!r} repeats {n}x — TTS audio may be corrupt; "
              f"re-run synth.py", file=sys.stderr)
    json.dump(words, open(os.path.join(src, "words.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    print(f"words: {len(words)}, span {words[0]['s']}-{words[-1]['e']}")

if __name__ == "__main__":
    main()
