---
name: "narrated-video"
description: "Produce a narrated explainer video (HTML→video pipeline): script to TTS narration, word-level captions, HyperFrames animated composition, render to MP4. Use when the user asks to make an explainer/tutorial video, or to replicate the 'webpage first, dub later' AI video workflow."
---

# Narrated Video — 口播讲解视频流水线

## Purpose
把"先写文案 → 配音 → 网页动画 → 逐帧渲染"做成可重复的流水线，
产出 1920×1080 / 30fps / H.264+AAC 的中文口播讲解视频。
已实战验证：二极管讲解（17s）、万用表使用指南（146s）。

## Workflow

### 0. 建项目
```bash
PROJ=~/workspace/<name>
mkdir -p $PROJ/src && cd $PROJ/src
# 文案：一段一场景，一行一段，定稿后再进流水线
$EDITOR paragraphs.txt
```

### 1. 合成配音
```bash
python3 ~/workspace/skills/narrated-video/bin/synth.py --src $PROJ/src \
  --voice avocado_v2:vd2_exacting_pillar --lang zh --speed 115
# 产出: narration.mp3, offsets.json（每段起始秒）, chunk_durs.json
# 必须分段合成：单次 >~400 字会损坏中段音频。合成后核验时长。
```

### 2. 词级时间戳
```bash
VENV=~/workspace/diode-video/.venv   # 装有 faster_whisper 的环境
NO_PROXY=localhost,127.0.0.1 no_proxy=localhost,127.0.0.1 \
  $VENV/bin/python ~/workspace/skills/narrated-video/bin/words.py --src $PROJ/src
# 产出: words.json [{w,s,e}...]。只取时间，不取文本（whisper 有错字）。
```

### 3. 生成字幕
```bash
python3 ~/workspace/skills/narrated-video/bin/captions.py --src $PROJ/src
# 产出: caps.js（var CAPS=[[t0,t1,[[ch,s,e]...]],...]），已保证 t1>t0 且不重叠
```

### 4. 搭建 HyperFrames 工程
```bash
cp -r ~/workspace/diode-video/multimeter $PROJ/web   # 复用 gsap/字体/node_modules
rm -rf $PROJ/web/renders
cp $PROJ/src/narration.mp3 $PROJ/web/assets/
cp ~/workspace/skills/narrated-video/assets/template.html $PROJ/web/index.html
# 按 references/scenes.md 写场景：每段落一个 <section>，
# data-start = offsets.json 时间 - 0.2s；关键动画时间查 words.json 关键词
# 把 caps.js 内容填入 __CAPS_JS__ 处；data-duration = 音频时长 + 1
```

### 5. 检查 → 渲染 → 质检
```bash
cd $PROJ/web && npm run check          # 0 error 才继续
mkdir -p tmp && TMPDIR=$PWD/tmp npx hyperframes render   # 后台跑，146s约7分钟
# 每场景抽帧目检：ffmpeg -ss <t> -i renders/*.mp4 -frames:v 1 qa.jpg
```

## Output Contract
- `renders/*.mp4`：1920×1080，30fps，H.264 + AAC，时长 = 音频时长 ±1s
- 全程中文 karaoke 字幕（当前字金黄高亮）
- 场景动画与配音关键词对齐（误差 <0.5s）
- `npm run check` 0 error

## Operating Rules
1. **文案先定稿**：改一字就要重跑全链（合成→时间戳→字幕→渲染）。
2. **时间一律用工具结果**：场景起止看 `offsets.json`，动画关键帧查
   `words.json`，不用估、不用猜。
3. **先 check 后渲染**：对比度/重叠问题在渲染前解决。
4. **渲染后台跑**：不要 poll 等，用 `yield_ms` 让它后台完成。
5. 遇到怪问题先读 `references/pitfalls.md` —— TTS 损坏、采样率、
   字幕负时长这些坑都记在里面了。
6. 声音：默认用沉稳科技男声（非真人模仿）。**绝不克隆现实人物音色**，
   除非用户给出明确授权。
