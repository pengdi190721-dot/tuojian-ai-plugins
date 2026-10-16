# 创始人 IP 操盘手｜学员安装

当前版本：**1.7.0**。

第一次使用先自检已有资料，问几个能用语音回答的问题，直接出IP定位报告。帮助创始人完成访谈建档、本人表达提炼、定位与内容计划、口播稿及现场提问卡，开头、结构与封面按期待、维持、兑现检查；上传后台截图和视频后，核对数据、定位问题、修改文案并安排下次验证。用户采纳建议后，保存到该创始人的档案，后续写稿主动沿用。

## 最简单的安装方式

把本页链接和下面这段话一起发给你的智能体：

> 请从这个仓库安装“创始人 IP 操盘手”1.7.0。插件位于 plugins/founder-ip-operator，独立技能位于 plugins/founder-ip-operator/skills/founder-ip-operator。按你当前环境支持的方式安装，保留所有配套文件。已有旧版时先备份，避免留下两个同时启用的同名版本。安装后检查版本及附件完整性，告诉我如何调用；不支持持久安装时如实说明。

## Codex 插件安装

首次添加学员工具市场，在终端运行：

```bash
codex plugin marketplace add pengdi190721-dot/tuojian-ai-plugins
codex plugin add founder-ip-operator@tuojian-ai
```

已经添加过这个市场的学员，先刷新再安装：

```bash
codex plugin marketplace upgrade tuojian-ai
codex plugin add founder-ip-operator@tuojian-ai
```

检查：

```bash
codex plugin list --marketplace tuojian-ai --json
```

应看到 founder-ip-operator，版本1.7.0，已安装并启用。安装后新建对话，必要时重启应用。当前无法访问GitHub时，先解决网络访问或使用下载的完整技能包，不能把安装失败当成功。

## 独立技能包

在[发布页](https://github.com/pengdi190721-dot/tuojian-ai-plugins/releases)下载最新的独立技能包，也可以在 SkillHub 搜索“创始人 IP 操盘手”安装。支持上传技能的工具可以导入；支持本地技能目录的工具可解压后安装整个 founder-ip-operator 文件夹。具体入口以当前工具为准。

WorkBuddy也可使用插件市场方式，在其对话或命令输入框运行（不是电脑终端）：

```text
/plugin marketplace add pengdi190721-dot/tuojian-ai-plugins
/plugin install founder-ip-operator@tuojian-ai
```

本次已核对市场配置格式，未在学员的WorkBuddy环境实测；遇到兼容问题可改用独立技能包。

## 安装后怎么用

第一次用，先做IP定位：

> 使用创始人IP操盘手，帮我做IP定位。

它会先查已有资料，再问几个问题，按住说话用语音回答就行，答完直接出定位报告。

已有访谈逐字稿时建档：

> 使用创始人 IP 操盘手。客户是【姓名或代号】，业务是【业务】。这是访谈逐字稿，请单独建档，保留真实故事和本人说话方式，完成当前资料支持的策划。每条口播稿都配现场提问或提示卡。

视频复盘：

> 这是【客户】的视频后台截图和对应视频。请核对数据，结合实际视频定位问题，给我完整改稿、配套现场提问卡及下一条验证建议。建议逐条编号；我采纳后再写入这位客户的长期写稿规则。

采纳建议：

> 采纳第【编号】条，今后用于【客户／平台／栏目】；第【编号】条仅下次试用。请保存并在之后写稿时读取。

## 使用范围

- 一人一档，客户截图、视频和已采纳规则保存在学员自己的工作区，不放进插件或公开仓库。
- 核心方法可独立使用。视频读取、录音转写、联网、媒体生成等由当前工具提供；没有相应工具时明确已完成范围，不假称看过视频。
- 每条稿件都有现场提问卡；截图不清、缺少视频或证据不足时，明确缺口，不编数据和经历。
- **定期联网更新需要在学员自己的工具中另外创建任务**，安装本插件不会自动获得彭迪账号下的周一更新任务。可发指令：“每周一上午9点检查视频号与抖音官方资料和有依据的运营经验，把变化保存到当前项目，每次复盘再核查相关来源。”只有工具确认创建成功才算启用。
- 包内历史示例不代表真实客户成效；10月13日资料快照也不代替以后任务的当次核查。

详细方法见[学员操作卡](skills/founder-ip-operator/学员操作卡.md)、[完整复盘流程](skills/founder-ip-operator/references/video-performance-review.md)和[采纳与沿用规则](skills/founder-ip-operator/references/client-learning.md)。
