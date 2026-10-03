#!/usr/bin/env python3
"""Build karaoke caption data (caps.js) from word timings.

Inputs (in --src):
    words.json       from bin/words.py  ([{w,s,e}...])
    paragraphs.txt   display text, one paragraph per line (Simplified CJK)
    offsets.json     from bin/synth.py  ({p01: start_sec, ...})
    chunk_durs.json  from bin/synth.py  ({p01: dur_sec, ...})

Output: caps.js  ->  var CAPS=[[t0,t1,[[ch,s,e],...]], ...]

Method: each paragraph is split into caption lines (break at，。：； or
16 chars). Within a paragraph, line boundaries are placed PROPORTIONALLY to
character count mapped onto the paragraph's time span. This is an
approximation — whisper's tokenization does not align 1:1 with display
characters (Traditional vs Simplified, homophone errors) — but it yields
smooth, watchable karaoke timing.

Invariants enforced (violating these breaks the HyperFrames timeline):
  - every caption has t1 > t0
  - captions never overlap (t1[i] <= t0[i+1])

Usage:
    python3 captions.py [--src DIR] [--pad 0.45]
"""
import argparse, json, os, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=".")
    ap.add_argument("--pad", type=float, default=0.45,
                    help="extra tail seconds added to each paragraph's span")
    args = ap.parse_args()
    src = os.path.abspath(args.src)

    words = json.load(open(os.path.join(src, "words.json"), encoding="utf-8"))
    paras = [l.strip() for l in open(os.path.join(src, "paragraphs.txt"), encoding="utf-8")
             if l.strip()]
    offsets = json.load(open(os.path.join(src, "offsets.json")))
    durs_raw = json.load(open(os.path.join(src, "chunk_durs.json")))
    # normalize keys: "p01" or "chunks/p01.mp3" -> "p01"
    durs = {}
    for k, v in durs_raw.items():
        base = os.path.basename(k).replace(".mp3", "")
        durs[base] = v

    def para_words(pi):
        key = f"p{pi+1:02d}"
        s, e = offsets[key], offsets[key] + durs[key] + 0.4
        return [w for w in words if s - 0.3 <= w["s"] < e]

    CAPS = []
    for pi, para in enumerate(paras):
        key = f"p{pi+1:02d}"
        pw = para_words(pi)
        if not pw:
            print(f"WARNING: no words for {key}, skipping", file=sys.stderr)
            continue
        t0 = pw[0]["s"]
        t_end = offsets[key] + durs[key] + args.pad
        lines, buf = [], ""
        for ch in para:
            buf += ch
            if ch in "，。：；" and len(buf) >= 8:
                lines.append(buf); buf = ""
            elif len(buf) >= 16:
                lines.append(buf); buf = ""
        if buf:
            lines.append(buf)
        total_chars = sum(len(l) for l in lines)
        total_span = t_end - t0
        acc = 0
        for line in lines:
            f0, f1 = acc / total_chars, (acc + len(line)) / total_chars
            acc += len(line)
            lt0 = round(t0 + total_span * f0, 2)
            lt1 = round(t0 + total_span * f1, 2)
            chars = list(line)
            cw = [[ch, round(lt0 + (lt1 - lt0) * ci / len(chars), 2),
                   round(lt0 + (lt1 - lt0) * (ci + 1) / len(chars), 2)]
                  for ci, ch in enumerate(chars)]
            CAPS.append([lt0, lt1, cw])

    # enforce invariants
    for i in range(len(CAPS) - 1):
        if CAPS[i][1] > CAPS[i + 1][0]:
            CAPS[i][1] = CAPS[i + 1][0]
    for c in CAPS:
        if c[1] <= c[0]:
            c[1] = round(c[0] + 0.3, 2)

    js = "var CAPS=" + json.dumps(CAPS, ensure_ascii=False) + ";"
    open(os.path.join(src, "caps.js"), "w", encoding="utf-8").write(js)
    print(f"caps: {len(CAPS)}, -> caps.js ({len(js)} bytes)")

if __name__ == "__main__":
    main()
