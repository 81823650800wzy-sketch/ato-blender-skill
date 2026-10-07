# 工具输入与示例

以下均为示例路径和参数，按当前工程替换；资源相对 JSON 所在目录解析。

## 轮廓分片

准备和目标帧同尺寸的语义灰度 mask，白色主体、黑色环境，先看真实轮廓。

```shell
python scripts/contour_parts.py partition --masks hand.png city.png sky.png --out parts
```

先列出的 mask 优先占用重叠，剩余为 remainder；空片跳过并报告。输出 partition.json 和 PNG 硬所有权 mask。阈值为 128；运动模糊的显示 alpha 另精修。序列逐帧处理需保持语义名称，工具单帧索引不能直接当跨帧语义身份。

计划格式（只列实际输出 mask，必须覆盖完整画面）：

```json
{"parts": [
  {"mask":"parts/00_hand.png","start":0.1,"end":0.6,"dx":-300,"dy":0,"angle":-8,"scale":0.7},
  {"mask":"parts/01_city.png","start":0.2,"end":0.8,"dx":200,"dy":100,"angle":6,"scale":0.8},
  {"mask":"parts/02_sky.png","start":0,"end":0.5,"dx":0,"dy":-250},
  {"mask":"parts/03_remainder.png","start":0.3,"end":0.9,"dx":0,"dy":250}
]}
```

位移单位为像素，角度单位为度，尺度相对全帧；各片共同原点在全帧中心，cubic ease-out 到归位。可增加 edge，指向生图并预对齐语义轮廓的全画幅 RGBA 纸边装饰，移动时随片块变换、归位淡出。工具不会自动生成纤维。

```shell
python scripts/contour_parts.py assemble --target next.png --base current.png --plan plan.json --time 0.9 --out assembled.png
python scripts/test_contours.py
```

--foreground 可提供全画幅持续前景 RGBA，避免运动片块重复显示主体。它应与目标里的主体吻合；不同主体需独立干净背景。最终端点先还原目标，再叠唯一前景。透明目标的中间合成遵循 alpha-over，最终端点输出目标本身；实际全画面背景通常应不透明。

## Blender 桥接

```json
{
 "width":1280,"height":720,"fps":24,"frames":120,
 "camera":{"lens_mm":20,"sensor_width_mm":36,
   "world_matrices":{"1":[[1,0,0,0],[0,1,0,0],[0,0,1,0],[0,0,0,1]]}},
 "phone":{"width":2,"height":1,
   "world_matrices":{"1":[[1,0,0,0],[0,1,0,0],[0,0,1,-3],[0,0,0,1]]}},
 "left_image":"assets/left.png","right_image":"assets/right.png",
 "background":"assets/background/0001.png","background_frames":120
}
```

矩阵和焦距是格式演示，必须替换为经检查的解算数据。矩阵为 Blender 世界坐标，刚体单位尺度；phone width/height 与矩阵平移单位一致。所有有效工作帧提供姿态，短缺口可检查后插值，长缺口不能靠单关键帧冒充追踪。

```shell
blender --background --python scripts/blender_bridge.py -- --project project.json --out scene.blend --render preview.png
```

导入器生成相机、手机、左右挂载点、透明平面及相机背板。背景为连续编号序列首帧，background_frames 默认 1（静图）。它只支持居中 principal point、方形像素、水平 sensor fit；非居中内参、fx/fy 非等比或畸变需先适配 camera shift、pixel aspect/去畸变。导入成功不能宣称已匹配相机。

前景/分片三维轨迹、实际布局微调、景深分层、字幕、调色、音乐和时间线仍需依照 workflow 构建，桥接不是一键成片。

## 编码审查

```shell
python scripts/media_check.py final.mp4 --expected-seconds 5 --expected-frames 120 --out reviews
```

输出探测、全帧解码状态和编码帧接触表，不能验证视觉、音频同步或参考风格。生产 MP4 由 Blender 序列经 FFmpeg 编码，将音乐目标片段对齐工作时间，随后独立听检。
