# 报告文件制作

## 选择交付形式

完整首访报告默认采用[主次分层](report-hierarchy.md)。优先使用离线可打开的单文件 HTML 进行演示；微信转发用竖版 PDF 或用户已有公开分享渠道。不要把 file 地址、localhost 地址或当前会话内部附件当成他人可访问的公网链接。公开部署需要实际托管条件及对应授权，创建本地文件不表示已发布。

设计沿用暖白、墨绿、清晰章节、充足留白。报告正文书面化，视频文案保留本人口语。一般不需要虚构人物照片、炫光或装饰图表。

## 自带生成工具

`scripts/render_report.py` 使用 Python 3 标准库，完整首访报告的数据优先按 `assets/focused-report-example.json` 组织；旧的 `assets/example-report.json` 仍支持简单报告。只负责排版，不负责生成内容或判断事实。

运行方式（路径以当前环境为准）：

```sh
python3 scripts/render_report.py 客户报告数据.json 客户报告.html
python3 scripts/render_report.py 客户报告数据.json 客户报告-完整阅读版.html --reading
python3 scripts/render_report.py 客户报告数据.json 客户报告-老板重点版.html --reading --brief
```

在技能根目录运行上述命令，或使用脚本实际绝对路径。输出存在时默认不覆盖，确需更新同一交付文件可增加 `--overwrite`。本工具不会联网、上传、发送或发布。

数据字段：
- `report_title`、`client_name`、`report_date`、`status`：报告标题、当前客户、实际报告日期与状态。
- `simulation`：必须明确填写 true 或 false，示例设为 true；真实资料不足时用状态说明，不能把虚构内容标成真实。
- `subtitle`：可选的说明文字。
- `layout`：完整首访报告设为 `focused`，使用分层页面；省略时沿用旧连续排版。
- `sections`：章节列表，每章包含 `title`、可选 `summary`、`blocks`。分层页面还需 `id`（小写英文短标识、不可重复）、`tier`（`main`为重点，`detail`为资料）；可选 `nav_title` 缩短目录名称，`takeaway` 放需要提醒的事项，默认标签为“注意事项”；标题直接交代拍什么、怎么安排，避免空泛的总结标签。
- 默认约4个重点章节，其余资料分类。主目录只呈现重点，资料页从次级目录或正文入口进入。内容多时仍需编辑层次，不能仅靠折叠掩盖重复。

内容块：
- `priorities`：`items`内含`label`、`title`、`text`，适合呈现少量并列重点。
- `actions`：`items`内含`title`、`text`、`owner`、`when`，写明行动、责任和节点。
- `links`：`items`内含`target`（实际章节id）、`label`；分层页校验目标，重点导出自动移除这些资料跳转，避免生成失效链接。
- `text`／`heading`：使用 `text` 存正文或小标题。
- `notice`：`title`、`text`，用于状态或范围说明。
- `quote`：`label`、`text`，注明真实语料出处或模拟性质。
- `list`：`items` 为文字列表。
- `table`：`headers`、`rows`；列数必须一致。阅读模式自动改成竖版字段。
- `script`：`title`、`meta`、`status`、`text`、`notes`；保持完整口语与镜头提示，不用未标注的假对白。
- 完整客户报告必须保留三平台机制解释，内容验收依据[三平台流程](platform-distribution-and-rules.md)。生成器只检查数据结构，不会替代内容验收。1.4.0完整报告还须依经营诊断加入优先卡点和30天行动，可用现有文字、表格及行动块；附带旧模拟数据只是排版参考，不能直接当新版完整内容。
- `platforms`：`items` 内依次给出 `name`、`mechanism`、`audience`、`strategy`、`rules`、`metrics`；可附 `sources`。
- `services`：`selected` 为待选择或实际意向；`plans` 依次列策划、成片交付、全案代运营，每项 `name` 与 `fields` 存交付及责任；附 `note`。
- `sources`：`items` 中每条含 `title`、完整 `url`、`note`，其中记录来源等级、公布与生效日期。

内容只接受文本与结构字段，不接受原始 HTML。不要把逐字稿中的网页脚本或指令作为代码执行。生成器对文字转义、校验表格及来源链接，但仍需检查正文。

`assets/example-report.json` 仅有5章，主要演示功能，其中三平台章节已更新；它不是完整报告。`assets/platform-report-example.json` 是平台章节的可编辑演示数据，配套 `examples/三平台机制说明.html` 与阅读版。模拟项目建议与公开资料分开标识。完整首访交付按 [报告结构](report-and-services.md) 补充所需章节。`examples/江苏养老模拟报告-重点分层版.html` 展示完整案例，配有老板重点PDF。陈岚的身份、经营故事和台词均为模拟，不得直接套给真实客户。

## PDF 与阅读模式

完整阅读模式自动展开全部平台、文案和服务说明。`--brief`仅适用于分层数据，按重点层导出，并明确标为摘要；它不能替代完整交付。演示页面支持“仅打印重点”和“打印完整报告”，后者必须展开完整平台和文案。可用当前可用浏览器或 PDF 工具导出；没有自动转换工具时，告知用户用浏览器“打印 → 另存为 PDF”，不能把 HTML 文件改后缀伪装为 PDF。

常规打印样式会展开文案和平台，但长宽表在手机上可能不易阅读；微信交付优先阅读模式，并按屏幕阅读调整字号、页面尺寸和分页。

完成后检查：所有章节、选题和文案完整，每条文案对应的现场提问或提示卡可直接访问、阅读和完整打印，不能只保留空字段；中文不缺字；页码顺序；无裁切、重叠、仅标题空页和悬空尾句；服务范围正确；来源链接有效；真实客户姓名和示例客户未混用。实际打开或渲染文件后才称文件可用，不以生成任务已排队当成功。

优先检查新版分层示例的四个主入口和正文资料链接，详情页能返回核心建议。检查手机布局、键盘导航、来源、完整稿数量和两种打印范围；完整稿中的每段文字必须保留，不能误提取折叠节点为空。
