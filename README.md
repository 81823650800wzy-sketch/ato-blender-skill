# 自主剪辑与混合合成 · ato-blender

可安装的 Codex skill。根据歌曲、视频/图片素材和剪辑意图，自主选择叙事、音乐混剪、vlog 或海报 MV，统筹声音、切镜、排版、调色、生图与二维/Blender 合成，交付成片和可编辑工程。ATO/ODD 在这里表示参考作品中的视觉语言，不宣称统一官方规范。

二维适合抠像、排字、界面和图像重构；需要相机解算、真实空间遮挡或体积交互时再使用 Blender。按内容选择技术，保留净实拍和阅读窗口。

## 轮廓与画面增强

- **通用生图轮廓参考法**：模型提供透明主体或语义分区参考，原帧配准与精修形成最终遮罩；适用于去背景、前后景分层、遮挡、孔洞、描边和转场选区。保真实拍 RGB 仍取当前源视频，动态段另做传播与检查。
- **单帧重构卡点**：截取音乐落点帧，模型保持构图重构材质，沿实际事物轮廓逐块露出对应区域；所有权互补、坐标一致，定格和回接动态分别设计。
- **动态漫画与联想手绘**：从实际画面形象选择分格、描画、运动线或具象联想；按节奏分时展开，让开脸部、动作和组件，不机械填满画面。
- **声音与双重收尾**：音乐、环境、拟音及界面音效分轨；结合最后动作、重音、尾响、环境声桥与画面淡出安排收束。
- **动漫冲击帧与威力递进**：接触曝光、独立换形的缠绕闪电、追踪粒子与手部遮挡、空间波动和环境反馈；变速保护关键稿，音效分别组织攻击、可听主体和深低频。见 [冲击帧与逐级强化](references/impact-frames-and-escalation.md)。

详见 [通用抠图方法](references/image-led.md)、[单帧重构与动态手绘](references/frame-reconstruction-and-ink.md)、[乐理与动作落点](references/music-rhythm.md) 和 [声音设计](references/sound-design.md)。

## 安装与使用

将仓库放入 Codex 的 `skills/ato-blender` 目录。PowerShell 示例：

```powershell
$skillDir = Join-Path $env:USERPROFILE '.codex/skills/ato-blender'
git clone https://github.com/81823650800wzy-sketch/ato-blender-skill.git $skillDir
```

已有安装先检查本地修改，避免覆盖用户改动；技能列表尚未刷新时开启新会话。

示例：使用 `$ato-blender`，根据我提供的歌曲、素材和参考制作约 20 秒城市生活混剪；小卡点采用画中画与轮廓重构，按画面选择手绘增强，并完成音画双重收尾。

入口：[SKILL.md](SKILL.md)。详细分工与交付规范在 [references](references)。Python 工具需要 Pillow、NumPy；媒体探测和编码需要 FFmpeg/FFprobe。Blender 桥接脚本在 Blender 内执行，二维方案无需强制经过 Blender。

## 检查与来源边界

```shell
python scripts/test_contours.py
python scripts/contour_parts.py --help
python scripts/media_check.py --help
python scripts/inspect_reference.py --help
```

脚本支持确定性处理和证据抽取，不自动评价审美、识别所有音乐事件或替代最终视听检查。编码可播放、轮廓精度和艺术判断分别记录；没有听觉检查时如实说明。历史工具验证见 [VALIDATION.md](VALIDATION.md)。

仓库包含通用说明、脚本和安装元数据，不包含用户原视频、截图、歌曲、字体、聊天记录或生产工程。参考案例为匿名技术观察，不随仓库分发对应素材。代码与文档使用 MIT 许可；用户素材及生成资产的使用许可由各自来源决定。
