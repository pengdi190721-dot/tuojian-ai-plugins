# AI短剧导演台

**从故事想法，到人物小传、分镜图片、视频提示词与剪辑验收。**

版本：0.1.0 · 作者：彭迪 · 技能标识：ai-short-drama-director

[公开仓库](https://github.com/pengdi190721-dot/tuojian-ai-plugins) · [下载本版安装包](https://github.com/pengdi190721-dot/tuojian-ai-plugins/releases/tag/ai-short-drama-director-v0.1.0) · [查看完整技能](skills/ai-short-drama-director/SKILL.md)

## 可以帮你做什么

| 阶段 | 得到什么 |
|---|---|
| 设计故事 | 一句话故事、主题、开场、冲突、笑点、燃点和结尾 |
| 人物小传 | 每人职责、性格、动机、说话方式、动作、人物关系、外形与声线 |
| 完整剧情 | 可表演的对白、动作、听者反应与情绪递进 |
| 统一参考 | 三视图、情绪九宫格、场景与产品图的制作安排 |
| 分镜规划 | 景别、视线、反应镜头、图片复用和补图清单 |
| 图片制作 | 上传素材及用途＋可整段复制的图片提示词 |
| 视频制作 | 根据实际成图写镜头、时间段、动作、情绪、台词与声音 |
| 逐段修改 | 检查人数、造型、中文、发音、声线与前后连续性 |
| 剪辑交付 | 剪辑顺序、节奏、素材映射、当前版本和验收记录 |

支持真人、机器人及拟人角色，不限定电商。人物数量、产品、画幅、长度、模型和声音要求由项目决定。

## 这套流程怎么用

故事方向确认→人物小传确认→完整剧情确认→统一参考→分镜图片确认→按实际成图写视频提示词→分段生成和检查→剪辑交付。

已有小传就先读已有小传；已有确认素材就从当前阶段继续。每次只做用户需要的阶段，不要求重新走一遍。

**人物小传是独立核心模块。**同一人物的台词、三视图、情绪九宫格、声线和表演都以它为依据。

**图片、视频提示词都分两步：**

1. 上传参考素材及用途：图的名称、标签、参考什么、不照搬什么，操作说明都放这里。
2. 可直接整段复制的提示词：只包含给模型的完整指令，必要的参考关系仍写入正文。

## Codex安装

在电脑终端依次运行：

```bash
codex plugin marketplace add pengdi190721-dot/tuojian-ai-plugins
codex plugin add ai-short-drama-director@tuojian-ai
```

已经添加过该市场但看不到新插件时，先刷新再安装：

```bash
codex plugin marketplace upgrade tuojian-ai
codex plugin add ai-short-drama-director@tuojian-ai
```

安装后新建任务；看不到技能时重启Codex。检查：

```bash
codex plugin list --marketplace tuojian-ai
```

应看到 ai-short-drama-director 已安装并启用。若提示找不到 codex 命令，可使用下面独立技能包方式。

### 独立技能包方式

从本版发布页下载 ai-short-drama-director-skill-v0.1.0.zip，解压后将整个 ai-short-drama-director 文件夹放入用户技能目录：

- 苹果电脑：~/.agents/skills/
- Windows：用户目录下的 .agents/skills/

最终目录应为 .agents/skills/ai-short-drama-director/SKILL.md，保留同级 references、assets、agents 和 LICENSE。这些路径是电脑文件夹位置，不是在对话里发送的命令。

也可以将下文“请帮我安装”口令连同仓库地址发给Codex，由它读取并安装。插件安装和独立技能包二选一，避免同名技能重复出现。

## WorkBuddy安装

**推荐：导入独立技能包。**

1. 从本版发布页下载 ai-short-drama-director-skill-v0.1.0.zip。
2. 打开WorkBuddy的技能页面，选择“添加技能→上传技能”。
3. 选择下载的技能包，导入后在已安装列表确认它已启用。部分版本按技术标识 ai-short-drama-director 显示，可用该名称搜索。
4. 新建对话，复制下方启动口令。

该入口依据 [WorkBuddy官方技能说明](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)。不同版本的按钮位置可能不同。

**插件市场方式：**如果当前版本有“插件→＋添加市场”，输入仓库地址，找到并安装AI短剧导演台（或搜索 ai-short-drama-director）。操作依据 [官方插件说明](https://www.workbuddy.cn/docs/workbuddy/Plugins)。

支持命令入口的版本，可以在应用的插件命令输入框依次运行，**不是在电脑终端运行**：

```text
/plugin marketplace add pengdi190721-dot/tuojian-ai-plugins
/plugin install ai-short-drama-director@tuojian-ai
```

若应用没有该命令入口，使用技能包导入。命令格式依据 [官方插件市场文档](https://www.workbuddy.cn/docs/cli/plugin-marketplaces)，不会将命令入口存在视作所有桌面版本的保证。

## 复制给学员：请帮我安装

```text
请帮我安装“AI短剧导演台”。
公开仓库：https://github.com/pengdi190721-dot/tuojian-ai-plugins
技能目录：plugins/ai-short-drama-director/skills/ai-short-drama-director
请先阅读该插件README，按我当前使用的Codex或WorkBuddy选择对应安装方法，保留完整技能目录，安装后验证是否能发现并读取技能。只安装这一项。
```

## 第一次启动

```text
请使用AI短剧导演台。我接下来会提供一个故事想法和已有素材。
先了解我要给谁看、发生什么事、希望观众记住什么，给我故事方向，等我确认。
之后按人物小传、完整剧情、统一参考、分镜图片、视频提示词和剪辑交付逐步推进。
已有材料先读再用，不重做已确认内容。
每条提示词都把上传素材与用途放在第一步，第二步给我能整段复制的完整正文。
本轮先只做故事方向。
```

Codex需要显式指定时，可在开头使用 $ai-short-drama-director。

## 其他常用口令

**只做人物小传：**

```text
请用AI短剧导演台，先阅读我已有的故事方向，设计人物关系，再逐个写人物小传给我确认。每人写清职责、性格、说话方式、动作习惯、关系、外形不变项、声线与剧情作用。本轮先不生成图片。
```

**继续当前项目：**

```text
继续这个AI短剧项目。先核对当前执行版本、已确认小传、图片与片段记录，告诉我接下来做什么；从未完成阶段继续，不重新设计已确认内容。
```

**按成图写视频：**

```text
这批分镜图已经确认。请先看实际图片，检查角色、站位与服装差异，再写对应视频提示词。逐段写时间、景别、机位、运镜、动作、可见情绪、台词、声线和结束状态。上传说明在第一步，第二步只放可整段复制的模型指令。
```

**修改局部：**

```text
我只替换视频中的一个片段。请保留其他已确认内容和编号，更新对应提示词、图片映射、生成总表、剪辑对照稿和预计时长，旧版本标清不再执行。
```

## 安装后的简单验证

输入“请用AI短剧导演台，只列制作阶段和人物小传包含的项目，不开始生成”。

应能说明人物小传是独立阶段，图片确认后才按成图写最终视频提示词，并知道素材说明与复制正文分开。没有触发时先新建对话，再确认技能已启用。

## 工具与制作范围

这是流程和提示词技能包，基础使用不需要另外申请接口密钥。实际图片、视频、语音和剪辑由当前环境可用工具或学员自己的平台完成；平台订阅、生成费用按其规则计费，不包含在技能包中。

没有生成工具仍可完成故事、小传、分镜、提示词和交接清单。写提示词不会自动提交收费生成。媒体生成成功不等于通过验收。

默认交付可编辑项目或剪辑对照稿；实际导出、发布按用户要求执行。素材与项目记录保存在学员自己的项目，不随技能公开。

## 更新

Codex刷新市场后重新安装；WorkBuddy按当前安装渠道更新插件或导入新版技能包。重新打开任务后核对版本，避免插件包与独立技能包同时安装。

## 维护与检查

维护者在仓库根目录运行以下命令，用Python 3.10及以上构建两个可分发压缩包，并检查清单、版本、引用和包内文件：

```bash
python3 plugins/ai-short-drama-director/scripts/build_release.py --output-dir output/ai-short-drama-director-release
```

该脚本只打包和检查，不联网、不安装插件、不调用生成服务。技能运行本身不依赖Python。

技能格式依据 [OpenAI官方技能文档](https://learn.chatgpt.com/docs/build-skills)，插件分发依据 [官方插件文档](https://learn.chatgpt.com/docs/plugins)。安装说明核对日期：2026年9月14日。平台入口发生变化时以当前官方说明为准。
