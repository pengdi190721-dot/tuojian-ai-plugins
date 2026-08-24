# 自媒体作战室｜学员安装说明

“自媒体作战室”帮助已经有产品或服务、但不知道拍什么和服务哪类客户的学员，从首次获客定位开始，逐步完成选题、调研、写稿、视频制作、发布包装和数据复盘。

## 安装后会获得什么

- 首次定位诊断：用5道生活化问题了解产品、真实客户、客户原话、可拍素材和拍摄条件，每次只问一个问题。
- 选题、调研、人设、脚本、视频制作、发布复盘等9个内置技能。
- 视频号主版本和小红书适配版本。
- 第一轮十条内容测试和获客复盘方法。

插件内置技能会随插件一起安装。FFmpeg、TrendRadar、Agent Reach、HyperFrames、huashu-design、Nuwa和品牌语气工具属于可选增强，不影响首次定位、基础选题、写稿和复盘。

## Codex学员安装

适用于安装了ChatGPT桌面端或Codex命令行工具的学员。

打开终端，依次运行：

```bash
codex plugin marketplace add pengdi190721-dot/tuojian-ai-plugins
codex plugin add self-media-war-room@tuojian-ai
```

安装完成后重启ChatGPT桌面端，新建一个任务，输入：

```text
第一次使用自媒体作战室，请逐题帮我找到最适合获客的自媒体定位，每次只问一个问题。
```

检查是否安装成功：

```bash
codex plugin list
```

列表中应出现 `self-media-war-room@tuojian-ai`。

## WorkBuddy学员安装

下面两条指令要在WorkBuddy的对话或命令输入框中运行，不是在电脑终端运行：

```text
/plugin marketplace add pengdi190721-dot/tuojian-ai-plugins
/plugin install self-media-war-room@tuojian-ai
```

安装后新建对话，输入：

```text
第一次使用自媒体作战室，请逐题帮我找到最适合获客的自媒体定位，每次只问一个问题。
```

检查插件市场：

```text
/plugin marketplace list
```

也可以输入 `/plugin`，查看并安装“自媒体作战室”。

## 首次使用规则

第一次使用时不要直接索要爆款选题。系统不会要求学员先说清专业定位或90天商业结果，而是依次询问：现在卖什么、谁曾经来买、客户为什么来、手里什么内容最多、哪种拍摄方式能坚持。五题结束后，系统负责归纳客户方向、账号类型、内容栏目和第一轮测试选题。

定位档案会保存在学员自己的项目目录中，不会随插件上传到本仓库。客户姓名、手机号、账号密码等敏感信息不要写入定位档案。

## 更新插件

Codex学员运行：

```bash
codex plugin marketplace upgrade tuojian-ai
codex plugin add self-media-war-room@tuojian-ai
```

WorkBuddy学员进入 `/plugin` 查看更新；如果没有自动刷新，重新添加插件市场后再安装一次。

## 常见问题

1. 安装后没有触发首次定位：请新建任务或新建对话，再复制上面的首次使用口令。
2. 环境体检显示可选工具缺失：基础流程仍然可用，不需要一次装齐全部增强工具。
3. 插件安装失败：先确认能够正常访问GitHub，再检查插件市场名称是否为 `tuojian-ai`。
4. 想继续上次项目：在同一项目目录中输入“继续上次的自媒体项目”。

项目维护者：彭迪
