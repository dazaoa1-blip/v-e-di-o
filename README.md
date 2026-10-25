# 独立游戏视频 EP04 · 素材仓

本仓库存放《独游视频》EP04 制作所需的音频素材，以及预览版成片。

## 目录结构

| 路径 | 内容 | 大小 |
| --- | --- | --- |
| `4录音/4录音1.m4a` ~ `4录音/4录音8.m4a` | 口播录音 1–8 | 共 11.6 MB |
| `背景音乐/于行,仁辰 - 糖果物语.mp3` | BGM《糖果物语》 | 7.1 MB |

## 视频成片

原文件为 `EP04_打击感_预览版_无口播.mp4`（约 308 MB），超出 Git 单文件 100 MB 限制，
因此作为 Release 附件发布。

> GitHub 会把 Release 附件名中的非 ASCII 字符替换为 `.`，所以附件用了英文名
> `EP04_ImpactFeel_Preview_NoVoiceover.mp4`（内容与原名文件完全一致，
> SHA-256 `57f59b83…34ba`）。

**[下载 EP04 打击感预览版（无口播）](https://github.com/dazaoa1-blip/v-e-di-o/releases/download/v1.0/EP04_ImpactFeel_Preview_NoVoiceover.mp4)**

全部附件见 [Releases](https://github.com/dazaoa1-blip/v-e-di-o/releases) 页面。

## 封面

`cover/` 下是 EP04《打击感先改哪？》的 8bit 像素风封面（左 35% 灰暗痛点区 vs 右 65% 高饱和效果区）：

| 文件 | 尺寸 |
| --- | --- |
| `cover/EP04_打击感_封面_3x4.png` | 1080×1440 |
| `cover/EP04_打击感_封面_4x3.png` | 1440×1080 |
| `cover/EP04_打击感_封面_16x9.png` | 1920×1080 |
| `cover/EP04_打击感_封面_16x10.png` | 1600×1000 |

封面由 `python3 cover/make_cover.py` 生成（依赖 Pillow、numpy 和系统字体 fonts-wqy-zenhei）。
所有像素都按整数倍最近邻放大，边缘无模糊；改文案或位置时直接改脚本里的 `FORMATS` 后重新运行即可。

## 说明

- 录音为手机/录音笔直录的 m4a，未做降噪与响度处理。
- 背景音乐仅用于本系列视频剪辑，版权归原作者所有。
