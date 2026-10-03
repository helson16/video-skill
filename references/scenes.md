# HyperFrames 场景模式

## 项目骨架
```bash
cp -r <某个已有项目> <新项目名>/          # 复用 node_modules/gsap/字体
rm -rf <新项目名>/renders
# 或 npx hyperframes init <新项目名>  （慢，需下载）
```
`hyperframes.json` 固定版本（如 `0.8.114`），`index.html` 里：
- `#root`：`data-duration="总秒数"`（= 音频时长 + 1s 余量）
- `<audio id="narration" src="assets/narration.mp3">`
- 背景层（grid + glow）`data-track-index="0"`
- 场景 `<section class="clip" data-track-index="1">`，`data-start` 比语音段落早 0.2s
- 字幕层 `#cap-layer`（`data-track-index="10"`），淡出层（`data-track-index="20"`）
- `<script>` 末尾：`buildCaptions(); window.__timelines["main"] = tl; tl.seek(0);`

## 字幕 karaoke（固定写法）
```js
var CAPS = []; // 由 bin/captions.py 生成的 caps.js 内容替换
function buildCaptions(){
  var layer = document.getElementById("cap-layer");
  CAPS.forEach(function(cap, ci){
    var t0 = cap[0], t1 = cap[1], cwords = cap[2];
    var el = document.createElement("div");
    el.className = "cap"; el.id = "cap" + ci;
    cwords.forEach(function(w){
      var s = document.createElement("span");
      s.textContent = w[0]; el.appendChild(s);
      if (/^[，。：、]$/.test(w[0])) return;
      tl.set(s, { color: "#ffd166" }, w[1]);   // 逐字高亮
      tl.set(s, { color: "#f1f5f9" }, w[2]);
    });
    layer.appendChild(el);
    tl.set(el, { opacity: 1 }, t0);
    tl.set(el, { opacity: 0 }, t1);
  });
}
```
CSS：`.cap { position:absolute; bottom:44px; width:100%; text-align:center;
font-size:42px; font-weight:700; text-shadow:0 2px 12px rgba(0,0,0,.9); opacity:0; }`

## 常用场景模式（SVG + GSAP）

### 1. 标题开场
大标题 `fromTo opacity/y` 入场 + 副标题淡入 + 主视觉 SVG 上浮。
结尾 `tl.to("#s-inner", {opacity:0, duration:0.3}, 场景结束-0.3)`。

### 2. 拨盘/档位（multimeter S2）
圆 + 指针（`transformOrigin:"50% 100%"`）+ 周围标签。
`tl.to("#pointer", {rotation: deg, duration:0.7, ease:"power2.inOut"}, t)`，
标签用 `tl.set(label, {opacity:1, color:"#ffd166"}, t)` 点亮。
时间 t 对照 words.json 关键词。

### 3. 步骤高亮（multimeter S3 插孔）
元素 `fromTo y:-40→0` 入场，再 `to y:+190` 插入；
目标用 `strokeWidth` 脉冲强调（`yoyo:true, repeat:1`）；
警告用 `scale:0.85→1, ease:"back.out(1.6)"` 弹出。

### 4. 连线绘制
`path` 加 `class="draw" pathLength="100"`，CSS `.draw{stroke-dasharray:100;stroke-dashoffset:100}`，
`tl.to("#p", {strokeDashoffset:0, duration:0.7}, t)` 绘制。

### 5. 流动粒子（电流/信号）
JS 循环创建 div，`fromTo x:0→950 opacity` + 尾段淡出，
stagger 用 `70.0 + i*0.35` 时间递增。

### 6. 警示卡片组（multimeter S8）
`.warn-card` 绝对定位网格布局，按语音序号时间
`fromTo {opacity:0, y:40, scale:0.92} → {1,0,1} back.out(1.4)` 逐个弹出。

### 7. 结尾
大字 `scale:0.85→1 back.out` + 全片 `tl.to("#fadeout",{opacity:1,duration:0.5}, 总时长-0.5)`。

## 时间轴组织
- 场景 `data-start/duration` 与 `offsets.json` 对齐（早 0.2s 开始）。
- 关键动画时间从 `words.json` 查关键词 `s` 字段，不要估。
- 所有 `tl.set/to` 时间用绝对秒数（相对音频 0 点）。

## 渲染
```bash
cd <项目> && mkdir -p tmp && TMPDIR=$PWD/tmp npx hyperframes render
# 146s/30fps ≈ 7 分钟，后台跑
```
先 `npm run check`（0 error 才渲染），渲染后每场景抽帧目检。
