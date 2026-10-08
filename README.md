# ATO Blender 实景拼贴 Skill

可安装的 Codex skill，支持 Blender 实拍音乐剪辑、极繁拼贴、运动追踪合成和撕纸转场。ATO 指参考视频的剪辑语言，不是统一官方规格。

核心规则：**有明显分割时优先沿真实轮廓裁切**（城市/天空、手部/环境、手机/背景）。下一镜头先以部分片块入镜，随后拼成完整画面，各片共享目标时间、坐标和 UV；不默认规则四分块。

## 覆盖流程

参考连续帧/教程字幕 → 素材探测与音乐镜头表 → 多平面相机解算与运动手机独立追踪 → 生图纸纤维和风格控件 → 前景精修/遮挡 → 轮廓分片入镜 → Blender 空间、景深与合成 → 滤镜、编码、审查、工程交付。

相机有效焦距结合实际画面验证；悬浮控件沿手机边框左右分布，其他场景按实际挂载面重新布局。纸质细节用内置生图提供，Blender 负责承载和动画。剪映可作为可验证的抠像来源，主合成仍在 Blender。

## 场景与主题设计

多数控件借鉴熟悉程序的导航、播放器和通知等结构，配合歌词设计内部状态与空间动画。追踪误差超限或音乐需要留白时采用无控件布局，相关磨砂与影子同步退出。增强内容也包括场景歌词、裁切视频、模型和图片；强调歌词时让文字参与场景透视与遮挡。

切镜可采用同主体换背景、同背景换主体、先场景后主体等关系，保留下一画面沿轮廓分片入镜并拼合的规则。生成素材和最终色彩曲线按情节主题选择，例如欢快 vlog 可采用纯白手写与明亮自然色，emo 段采用适合的沉静色彩，均须检查实际编码画面。

详见 [视觉语言](references/visual-language.md)、[主题与调色](references/style-and-color.md) 及 [参考研究的证据边界](references/reference-study.md)。

## 安装

将仓库内容放入 Codex 的 `skills/ato-blender` 目录。PowerShell 示例（默认 Codex home；已自定义时按实际路径修改）：

```powershell
$skillDir = Join-Path $env:USERPROFILE '.codex/skills/ato-blender'
git clone https://github.com/81823650800wzy-sketch/ato-blender-skill.git $skillDir
```

若目录已有本 skill，检查本地修改后更新，不覆盖用户改动。在 Codex 中调用 `$ato-blender`；若当前会话未刷新技能列表，开启新会话。

例：使用 $ato-blender，分析我的实拍与参考视频，优先沿手部和天空轮廓裁切，生成撕纸素材，用 Blender 做 5 秒转场验证。

## 使用与依赖

入口：[SKILL.md](SKILL.md)。完整流程、追踪、语义轮廓、生成资产、输入格式和审查规范在 [references](references)。Python 辅助需要 Pillow、NumPy；视频审查需要 FFmpeg/FFprobe；桥接导入器在 Blender 内执行（在 4.5.10 LTS 验证）。内置生图、抠像和真实追踪由执行环境与素材决定。

```shell
python scripts/test_contours.py
python scripts/contour_parts.py --help
python scripts/media_check.py --help
blender --background --python scripts/blender_bridge.py -- --help
```

脚本是可复用处理工具，不是一键完成语义分割、相机解算或完整 MV 的生成器。真实轮廓、追踪与听感仍须按 workflow 验证，不能以脚本成功代替视觉通过。

## 验证

7 项确定性测试覆盖互补遮罩、重叠优先级、空片处理、尺寸拒绝、动画起止、前景和最终还原。另用无隐私合成 fixture 验证 Blender 工程保存/渲染，以及 1 秒 24 帧带音轨 MP4 全解码和接触表输出。检查结果见 [VALIDATION.md](VALIDATION.md)。

仓库仅包含通用说明、脚本与安装元数据，不包含用户私片、聊天截图、原曲、字体或生产工程。

代码和文档使用 MIT 许可；用户输入及生成资产的许可由各自来源决定。
