# 口播剪辑助手 · WorkBuddy 专家包

口播视频剪辑包装师。干两件事：

- **口播剪辑加包装成片**：发来出镜口播视频，剪掉口误、念错重来和长停顿，加人像小窗、要点卡、金句卡、动态字幕和音效，直接出成片。
- **口播科普视频成片**：发想法和截图，先写口播稿，录音后用截图配圈注动画出科普视频。

专家守则在 `agents/koubo-editing-assistant.md`：分线、每条回复的格式、两条线的步骤和停顿点、一条消息定方案、硬规矩、判断规矩、默认值、交付返修、出问题怎么办。具体命令和文件写法在 `skills/voiceover-explainer/`（同仓库的“口播剪辑助手”技能）。

## 包里有什么

```
koubo-editing-assistant/
├── .codebuddy-plugin/plugin.json      专家配置（标识、名称、头衔、描述、分类、标签、推荐提示词）
├── agents/koubo-editing-assistant.md  专家守则（系统提示词）
├── avatars/koubo-editing-assistant.png 头像，512×512
├── skills/voiceover-explainer/         技能：脚本、动画引擎、参考文档
└── README.md
```

## 怎么用

- **上架专家市场**：WorkBuddy 开放平台上传这个 zip，提交审核。
- **企业内部用**：企业版管理后台“上传企业专家”，上传这个 zip。
- 要在用户电脑上运行（WorkBuddy 选本地模式）。第一次用会自动装程序、下载约 230MB 的中文语音识别模型。

## 运行要求

本地模式；Python 3；第一次用自动安装 numpy、pillow、playwright、sherpa-onnx、imageio-ffmpeg、opencv-python-headless 4.x（国内镜像）。

作者：彭迪 · 版本 2.1.0 · MIT
