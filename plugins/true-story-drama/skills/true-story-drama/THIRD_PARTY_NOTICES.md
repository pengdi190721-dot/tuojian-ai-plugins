# 第三方能力说明

“真实故事短剧化”从0.x版本起，就以开源项目 `zenstory-ai/drama-skills` 的三个技能为方法底座重新编排和改写。1.0.0是重写版，这部分方法继续保留：

- `short-drama-develop`：可追溯改编、故事发动机、人物选择、代价与状态变化；
- `short-drama-write`：因果节拍、可表演动作、中文短剧剧本与事实边界；
- `short-drama-review`：证据式审查、连续性、去模板感与分级结论。

来源仓库：https://github.com/zenstory-ai/drama-skills

- 许可证：MIT
- 核验提交：`5ca7d5a32332e9b0dfd8fdd1a4bdf081476aa974`
- 核验日期：2026-09-01
- 原始许可证：插件包里的 `licenses/zenstory-ai-drama-skills/LICENSE`，原文也附在本文件末尾

本技能没有复制上游完整产线、生成适配器或项目工具。在上游方法之外，本技能新增了：故事与主题确认关卡、事实底稿确认关卡、改编台账、“故事为什么平”诊断表、大众情绪回报设计、开场与节奏统一标准、台词去AI腔、人物定妆图与场景图与定帧图的提示词写法、适配LibTV里Seedance 2.0的按秒分段视频提示词，以及剧本体检和提示词校验两个脚本。

本技能中的写作方法资料由作者用自己的话重新撰写，不包含任何第三方作品的原文。

上游项目及其贡献者不为本技能的修改、分发、教学或使用结果背书。

## 上游许可证原文

```text
MIT License

Copyright (c) 2026 drama-skills contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
