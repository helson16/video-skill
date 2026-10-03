# Narrated Video Skill — 口播讲解视频工作流

把"先设计成网页、后期配音"的 AI 视频制作方法沉淀为可复用的工作流。
已实战验证：二极管讲解（17s）、万用表使用指南（146s）。

## 这是什么

一条完整的口播讲解视频流水线：

```
文案（一段一场景）
  → TTS 分段合成配音
  → faster-whisper 词级时间戳
  → karaoke 字幕数据
  → HyperFrames 网页动画合成（HTML/CSS/JS + GSAP）
  → 逐帧渲染 → MP4（1920×1080 / 30fps / H.264+AAC）
```

核心思想：**画面用代码画（SVG+CSS 动画），时间轴与配音逐词对齐，
用无头浏览器逐帧截图再编码**。改文案只改文本，改画面只改代码，
配音、字幕、动画自动对齐。

## 目录

```
├── SKILL.md              # 方法论：6 步工作流（Agent 入口，先读这个）
├── bin/
│   ├── synth.py          # 文案 → 分段 TTS → narration.mp3 + offsets.json
│   ├── words.py          # 音频 → 词级时间戳 words.json
│   └── captions.py       # 时间戳 + 文案 → karaoke 字幕 caps.js
├── references/
│   ├── pitfalls.md       # 17 条实战踩坑（必读）
│   └── scenes.md         # 7 种场景模式（拨盘/插孔/连线/粒子/卡片组…）
└── assets/
    └── template.html     # HyperFrames 合成起手模板
```

## 给 Agent 的使用说明

1. 读 `SKILL.md`，按 6 步工作流执行。
2. `bin/` 脚本处理脏活：`synth.py` 避开 TTS 长文本损坏坑，
   `captions.py` 保证字幕时间合法。
3. 遇到怪问题先查 `references/pitfalls.md`。
4. 场景动画参考 `references/scenes.md` 的模式。

## 依赖

- Python 3 + `faster-whisper`（词级时间戳）
- Node.js + HyperFrames（`npx hyperframes`）
- TTS：任意中文 TTS（实战用 `avocado_v2:vd2_exacting_pillar` 沉稳男声；
  **绝不克隆现实人物音色**）
- FFmpeg

## 效果示例

- 二极管单向导电讲解（17s）
- 万用表使用指南（146s，9 场景，7 条安全卡片）

## License

MIT
