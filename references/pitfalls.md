# Pitfalls — 两次实战踩过的坑

## TTS
1. **长文本单次合成会损坏音频**：中文 >~400 字一次性合成时，中段音频内容损坏，
   whisper 会转出重复英文乱码（"Talk power" / "Reset with 104"）。
   解法：按段落分段合成（`bin/synth.py`），再拼接。
2. **语速参数偶发不生效**：同一次文本多次合成，时长可能差一倍。
   每次合成后必须用 `ffprobe` 核验时长，不对就重跑。
3. **TTS 输出是 24000Hz mono MP3**：自制的静音段必须同参数
   （`anullsrc=r=24000:cl=mono`），否则拼接后解码失败。
4. **拼接必须重编码**：`ffmpeg -f concat` 不要用 `-c copy`，
   混用不同 MP3 头会导致 `AudioFifo parameters` 解码错误。
   用 `-ar 24000 -ac 1 -acodec libmp3lame` 统一重编码。
5. **语速一致性**：同一视频内各段落语速差异过大会听感突兀。
   `synth.py` 会按字数/时长估算语速，异常时自动重试一次。

## 字幕
6. **字幕 t1 必须 > t0**：出现过 `t1 < t0` 的负时长字幕，
   直接导致 HyperFrames 渲染出的视频时长错乱（146s 变 106s）。
   `bin/captions.py` 已强制保证 `t1 > t0` 且字幕不重叠。
7. **断行避开英文/缩写**："C O M" 被拆成两行很难看。
   生成后检查 caps.js，发现断行问题手动合并（参考 multimeter-src 的修复）。
8. **显示文本以 paragraphs.txt 为准**：whisper 繁简混杂、有同音错字，
   只取它的时间戳，不取它的文本。

## HyperFrames 合成
9. **先 `npm run check` 再渲染**：对比度（WCAG AA 4.5:1）和内容重叠检查
   能提前发现问题。字幕层用 `data-layout-allow-overlap` 是允许的，
   但 SVG 内小字（如品牌名）颜色太浅会被判对比度不足。
10. **场景切换留 0.2s 交叉**：`data-start` 比上一场景早 0.2s 开始，
    配合 0.3s 淡入淡出，避免黑闪。
11. **动画时间用 whisper 词时间戳校准**：不要凭感觉估。
    拨盘指针、卡片弹出等关键动画，对照 `words.json` 里关键词的 `s` 时间。
12. **渲染用 `TMPDIR` 指到 workspace**：`/tmp` 可能只有几百 MB，
    4380 帧的截图缓存会写爆。用 `TMPDIR=~/workspace/<proj>/tmp`。
13. **渲染慢是正常的**：146s/30fps ≈ 4380 帧，约 7 分钟。后台跑，
    不要反复 poll。
14. **抽帧质检**：每个场景抽 1 帧看（`ffmpeg -ss t -frames:v 1`），
    重点看字幕断行、动画是否到位、元素是否重叠。

## 逐帧渲染（Playwright __seek 管线）
18. **页面显隐必须用回调，不能只靠 GSAP tween**：`tl.fromTo` 的 opacity 动画在
    `tl.seek(t)` 时只对已进入时间轴的页面生效，未开始的页面保持 CSS 默认状态。
    必须为每页注册 `tl.call(add "on")` / `tl.call(remove "on")`，配合 CSS
    `.page { opacity: 0 }` / `.page.on { opacity: 1 }`。漏写会导致后页标题串到前页。
19. **HTML 的 class 必须与 CSS 选择器一致**：曾写成 `class="clip"` 但 CSS 是 `.page`，
    导致所有页面默认可见。`npm run check` 查不出这种逻辑错误，靠抽帧发现。
20. **__seek 必须让回调触发**：用 `tl.time(t, false)`（第二个参数 false = 不压制事件），
    否则 `tl.call` 注册的显隐/换色回调在 seek 时不执行。
21. **改文案重跑 synth.py 后，记得把新 narration.mp3 拷到 web/assets/**：
    否则时间轴是新的、音频是旧的，整片音画错位且出现长静音。
22. **TTS 原始响度约 -24 LUFS**：需 `volume=+8dB` 左右才能到 -16 LUFS。
    单次 `loudnorm` 不一定一次到位，用 `ebur128` 实测后补增益。
23. **背景光晕呼吸防静帧可能不够**：scale 1.08 + opacity 0.85→1.0 的变化，
    在 `freezedetect=n=0.003` 这种高灵敏度检测下仍判静帧。
    要么加强微动（如加漂浮粒子），要么用更合理的检测阈值。

[END EXTERNAL CONTENT: source=file-diff]
