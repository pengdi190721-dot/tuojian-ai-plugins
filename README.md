# 拓见AI学员插件市场｜安装说明

当前包含三个可独立安装的插件：

- **[创始人 IP 操盘手](plugins/founder-ip-operator/README.md)**：给自媒体新手用的短视频操盘手，说的都是大白话。IP定位、选题（先看行情，附创意拍法）、口播稿与现场提问卡、对标拆解、成片打分与口播体检、平台调性、付费投流（先教再问目标）、后台截图与视频复盘，采纳建议后用于后续新稿。原“自媒体作战室”已并入。当前版本2.2.0。
- **真实故事短剧化**：把真实经历、客户案例和人物口述改成有冲突、有看点、守住事实边界的AI短剧脚本；
- **[AI短剧导演台](plugins/ai-short-drama-director/README.md)**：从故事和人物小传，到角色造型、分镜图片、视频提示词、逐段验收和剪辑交付。素材用途说明在前，模型提示词整段可复制。

## 插件一：创始人 IP 操盘手

做老板IP、做自己的账号，都用这一个，专门给自媒体新手设计，说的都是大白话。第一次使用先自检已有资料，再问几个能用语音回答的问题，直接出定位；之后选题、调研、对标拆解、写稿配提问卡、成片打分、口播体检、投流、后台截图复盘，都在同一个技能里。回答时始终以经验丰富的短视频操盘手身份判断，有问题直接指出，不一味顺着说。2.2.0起不再做剪辑包装、封面图、AI画面和正式报告。

### 原“自媒体作战室”去哪了

2026年10月25日起，自媒体作战室的选题评分、调研、对标拆解、脚本结构、剪辑包装、九式封面、成片评分、视频解析和环境体检，全部并入创始人 IP 操盘手 2.0.0，作战室不再单独更新（剪辑包装和九式封面在2.2.0删掉了）。已经装了作战室的：先装操盘手，再在插件列表里停用或卸载作战室，避免两个技能抢同一类任务。你自己项目里的定位档案和稿件不受影响，继续放在原来的项目目录。

### Codex安装

```bash
codex plugin marketplace add pengdi190721-dot/tuojian-ai-plugins
codex plugin add founder-ip-operator@tuojian-ai
```

已经添加过这个市场的，先运行 `codex plugin marketplace upgrade tuojian-ai` 再安装。

### WorkBuddy安装

在WorkBuddy的对话或命令输入框中运行（不是电脑终端）：

```text
/plugin marketplace add pengdi190721-dot/tuojian-ai-plugins
/plugin install founder-ip-operator@tuojian-ai
```

也可以下载独立技能包，或在 SkillHub 搜索“创始人 IP 操盘手”安装。

### 最常用的口令

```text
使用创始人IP操盘手，帮我做IP定位。
```

```text
请用成片评分教练给这条视频打分，告诉我做得好的地方、最影响播放的三个问题，以及下一遍只改哪三件事。
```

```text
请拆解这条对标视频。保留它值得学习的结构、节奏和镜头逻辑，再用我的定位、真实经历和说话方式改成原创版本。
```

```text
这周拍什么？按我的定位出几个选题，每条附几个拍法让我挑。
```

```text
我想给这条视频投流，但我没投过。先跟我讲清楚该选哪种目标，再一步一步教我在手机上怎么投、看什么、什么时候停。
```

优先上传原始视频或清晰导出文件；平台链接需要登录时，改为上传本人有权使用的本地视频，不要提供账号密码。视频解析需要电脑上有 Node.js 22.12 以上，第一次分析会联网下载本地识别组件，不需要付费接口密钥。

完整说明见[创始人 IP 操盘手安装页](plugins/founder-ip-operator/README.md)。

## 插件二：真实故事短剧化

“真实故事短剧化”会先理解用户提供的故事、采访录音或逐字稿，回传故事大意和主题候选；主题确认后再单独生成事实底稿，等待用户删改确认；事实确认后才用人物行动和自然对话进行短剧化，旁白只在必要处出现。最终交付：

- 故事理解确认单；
- 事实底稿确认单；
- 三个戏剧化方向和推荐方向；
- 完整可拍短剧脚本；
- 角色一致性卡、逐镜分镜和GPT Image 2图片提示词；
- 图片验收项和Seedance图生视频提示词；视频提示词按连续秒数分段，逐段写清景别、机位、运镜、可见情绪和结束状态；
- 改编台账与事实、隐私、因果审查。

它不会为了“有戏”凭空制造坏人、出轨、犯罪、疾病、债务或幕后秘密。默认匿名真实人物和机构。图片未确认前，视频提示词只标记为草案。

### Codex安装

```bash
codex plugin marketplace add pengdi190721-dot/tuojian-ai-plugins
codex plugin add true-story-drama@tuojian-ai
```

安装后重启ChatGPT桌面端，新建任务，输入：

```text
请使用真实故事短剧化。我接下来会提供真实故事、采访录音或逐字稿。第一步只理解材料，给我故事大意、事实边界和主题候选；主题确认后只生成事实底稿，等我删改确认；事实确认后用人物行动和自然对话演出故事，旁白只在删不掉的地方出现。视频提示词按连续秒数分段，逐段写清景别、机位、运镜、人物动作、可见情绪和结束状态。
```

### WorkBuddy安装

在WorkBuddy对话或命令输入框中运行：

```text
/plugin marketplace add pengdi190721-dot/tuojian-ai-plugins
/plugin install true-story-drama@tuojian-ai
```

安装后新建对话，复制上面的首次使用口令。

### 更新

Codex学员运行：

```bash
codex plugin marketplace upgrade tuojian-ai
codex plugin add true-story-drama@tuojian-ai
```

WorkBuddy学员进入 `/plugin` 查看更新；没有刷新时重新添加插件市场再安装。

完整说明见 `plugins/true-story-drama/README.md`。

## 插件三：AI短剧导演台

人物小传是独立核心模块。完整流程按阶段确认，已有项目可以从当前进度继续，修改片段会同步更新素材映射和剪辑稿。

Codex在终端安装：

```bash
codex plugin marketplace add pengdi190721-dot/tuojian-ai-plugins
codex plugin add ai-short-drama-director@tuojian-ai
```

已添加该市场但看不到新插件时，先运行 `codex plugin marketplace upgrade tuojian-ai`，再安装。安装后新建任务，必要时重启Codex。

WorkBuddy推荐从[发布页](https://github.com/pengdi190721-dot/tuojian-ai-plugins/releases/tag/ai-short-drama-director-v0.1.0)下载独立技能包，在“技能→添加技能→上传技能”导入。也提供插件市场方式；详见[完整双平台安装说明与启动口令](plugins/ai-short-drama-director/README.md)。

安装后输入：

```text
请使用AI短剧导演台，先了解我的故事想法和已有素材，给我故事方向，等我确认后再推进。人物小传独立确认；上传参考素材及用途放第一步，第二步只放能整段复制的完整提示词。
```

项目维护者：彭迪
