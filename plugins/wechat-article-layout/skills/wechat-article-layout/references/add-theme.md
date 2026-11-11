# 加新主题

主题的长相只在一个地方：`scripts/themes.py`。主题清单（`references/themes.md`）和插件安装页上的预览图都是从它生成的，不会出现“说明写的和实际不一样”。

## 步骤

1. 在 `scripts/themes.py` 里复制一个最接近的主题类，改：
   - `no`（编号，接着往下排）、`id`（英文标识，小写加横线）、`name`（中文名）
   - `fit`（适合什么文章）、`look`（长相一句话）、`recommend`（推荐栏目）、`swatch`（三个代表色）
   - 颜色变量和各个组件的样式
2. 把新主题加进文件末尾的 `THEMES`。
3. 用样稿排一遍，看检查是否通过：
   ```
   python3 scripts/render.py assets/sample.md --theme 新编号
   ```
4. 看缩略图：`python3 scripts/render.py --pick`，打开「选主题.html」。
5. 在源码仓库里跑插件的打包脚本，它会重新生成主题清单和预览图、检查版本号、打包。加主题算中等更新，版本号第二位加一（比如 1.0.0 → 1.1.0）。

## 每套主题要实现的组件

| 组件 | 必须自己写 | 说明 |
|---|---|---|
| cover | 是 | 封面：栏目、期数、标题、副标题、信息 |
| toc | 是 | 目录 |
| chapter | 是 | 章节标题，`last` 为真时是“写在最后” |
| step | 是 | 步骤标题 |
| shot | 是 | 截图框 + 图号说明 |
| prompt | 是 | 代码框 |
| tip | 是 | 踩坑提醒 |
| olist | 是 | 编号清单 |
| quote | 是 | 金句 |
| footer | 是 | 署名 + 互动 |
| subhead、ulist、saying、compare、divider、placeholder | 否 | 有通用版本，按颜色变量自动配色；想要特别的样子再重写 |

## 粘进公众号不掉格式的规矩

- 只用 `section`、`p`、`span`、`strong`、`img`。不用 `div`，不写 `class`、`id`。
- 样式全写在元素自己的 `style` 里，颜色写死。不用渐变、样式变量、定位、浮动、网格布局、`@media`。
- 每段文字都包在 `<span leaf="">` 里（用 `leaf()`、`sp()` 这几个积木就自动包好了）。
- 左右排用 `display:flex`。
- 读者开深色模式时，微信会自动调颜色：深色块里用浅字，浅色块里用深字，转换后才看得清。

`scripts/check.py` 会查这些，排版时自动跑。
