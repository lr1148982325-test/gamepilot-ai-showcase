# PSD2UMG：从图层整理、切图到Unreal UMG

一份 UI 设计稿完成后，真正进入项目之前还有一段繁琐的实现工作。

| 主要角色 | PSD 交付后仍需处理的工作 |
|---|---|
| UI 设计师 | 整理图层，确认切图粒度，处理文字、状态和资源复用 |
| UE UI 开发 | 导入资源，搭建 Widget Tree，配置布局、样式和绘制顺序 |

这条管线不是把 PSD 图层机械地逐项转换成 `Image` 或 `CanvasPanel` 节点。Agent 会结合完整画面、图层结构和运行时需求，判断资源粒度、可编辑文字、状态、复用关系以及 UMG 控件结构；MCP 再检查这些决策并将其转换为可执行产物。

## 1. 这条管线减少了哪些繁琐工作

| 传统方式 | 管线方式 |
|---|---|
| 逐层检查、重新分组和命名 | Agent 根据完整画面与图层结构生成整理方案 |
| 手工判断合并、独立、状态和复用 | 生成具有运行时用途的资源规划 |
| 逐项导出、导入并搭建 Widget Tree | 生成正式切图、UMG 布局和 UE 构建脚本 |
| 修改后重复执行整套下游工作 | 沿用正式中间产物重新生成受影响的下游结果 |

> 管线输出的是可以继续接入数据、事件、动画和交互的 Widget Blueprint 实现初版，不是“无需人工即可上线”的承诺。

## 2. 管线包含两个 AI skills

![两个 AI skills 的决策分工、MCP 共享支撑与正式产物关系](assets/images/psd2umg/01-skill-contract.svg)

- `psd-organizer` 指导 Agent 分析 PSD，决定图层整理、英文命名、切图粒度、可编辑文字、状态和资源复用。
- `psd-to-umg` 指导 Agent 使用 organizer 的正式事实，决定区域关系、控件、容器、slot、sizing、style 和嵌套结构。

> `psd-to-umg` 读取 organizer 的正式产物，不重新整理 PSD 或重新切图。

## 3. `psd-organizer`：整理 PSD 图层并生成切图

![psd-organizer 的 AI 决策、校验和执行闭环](assets/images/psd2umg/02-organizer-sequence.svg)

organizer 的核心不是逐层导出，而是判断哪些视觉应该合并成一张切图、哪些内容必须独立、哪些文字需要保持可编辑，以及不同状态和重复实例如何复用资源。Agent 在 `psd-organizer` 的指导下作出这些资源决策；MCP 提供图层事实和执行约束，检查方案并冻结可执行的切图合同。

合同冻结后，`save_plan` 会生成当前 revision 的审阅页。人工可以批准当前方案，或一次性提交修改意见；反馈会触发方案重建和重新审阅，只有当前 revision 获批后才会通过 Windows COM 调用 Photoshop 完成重组、保存和原生 PNG 渲染。这是整理与切图方案的执行前审阅，不替代 UE 侧的最终视觉验收。

![psd-organizer 的执行前人工审阅页](assets/images/psd2umg/06-organizer-review.png)

## 4. `psd-to-umg`：把整理结果搭建成 UMG

![psd-to-umg 的 AI 区域决策、布局校验和 UE 交付闭环](assets/images/psd2umg/03-umg-sequence.svg)

UMG 阶段直接读取 organizer 交付的 PNG、文字、来源位置、状态、复用和绘制顺序，不重新整理 PSD 或重新切图。MCP 根据这些事实建立保真底座和关系布局候选；Agent 审查画面区域，选择控件、容器、嵌套、slot、sizing 和 style，并只修订没有通过检查的区域。

Delivery Gate 通过后，MCP 生成正式 `layout.json`、`build_widget.py` 和运行时审计说明。项目人员在 UE Editor 中运行脚本。

## 5. 当前支持的 UE 控件

![当前直接生成的 UE 控件范围](assets/images/psd2umg/04-supported-ue-widgets.svg)

当前生成模板具有以下 19 类原生直接创建路径：

| 类别 | 控件 |
|---|---|
| 基础显示与交互 | `Image`、`TextBlock`、`Button`、`ProgressBar`、`Spacer` |
| 布局容器 | `CanvasPanel`、`Overlay`、`HorizontalBox`、`VerticalBox`、`ScrollBox`、`GridPanel`、`UniformGridPanel`、`WrapBox` |
| 集合、状态与适配 | `ListView`、`TileView`、`WidgetSwitcher`、`SizeBox`、`ScaleBox`、`SafeZone` |

`ListView` 和 `TileView` 可以生成 Entry Widget、方向、尺寸、间距和设计器预览配置，但业务数据源、字段绑定和交互仍由项目接入。`CheckBox`、`Slider`、`ComboBox`、`EditableText` 与 `TreeView` 不在当前原生直接生成清单中。

Widget Catalog 是可选的项目增强：配置并匹配成功时，可以复用项目已有的按钮、文字样式、分页点或数量选择器等封装控件；没有配置或没有合适匹配时，管线仍然使用原生 UMG 生成基础结构。

## 6. 实际案例：Demo RPG

以下结果来自一张 2560 × 1440 的角色状态界面分层 PSD，本文称为 Demo RPG。

输入 PSD 包含 128 个来源节点、37 个组和 31 个文字层。organizer 按正式方案执行 91 个 PSD 重组操作和 38 个渲染任务，最终得到 33 个物理 PNG 与 67 项 manifest 信息：38 表示生产任务，33 表示实际文件，67 还包含文字、来源实例和资源复用事实，其中包括 7 项组合切图、33 项独立资源和 27 项文字。

Agent 在 UMG 阶段根据画面关系和来源事实为不同区域选择了以下结构：

| 区域 | 实际 UMG 结构 |
|---|---|
| 页签 | `Overlay → HorizontalBox → TextBlock + Spacer` |
| 属性 | `VerticalBox → HorizontalBox` |
| Buff / Debuff | `VerticalBox → Overlay → Image / TextBlock` |
| 头像 | `Overlay → HorizontalBox → local Overlay` |
| 操作入口 | `Button` |
| HP Fill | `Image` |

正式布局实际使用了 `Button`、`CanvasPanel`、`HorizontalBox`、`Image`、`Overlay`、`Spacer`、`TextBlock` 和 `VerticalBox` 8 类控件；构建报告记录 119 / 119 个 Widget 节点创建并保存。固定属性行使用 `VerticalBox` 和多组 `HorizontalBox`，没有被包装成业务 `ListView`；HP Fill 在这个案例中是 `Image`。

![Demo RPG 的完整 PSD 来源、真实 UE Designer 和独立渲染](assets/images/psd2umg/05-demo-evidence.png)

UE Designer 中的红框区域在下方以完整尺寸展示。

## 7. 在 Codex 等AI Agent中怎么使用

| 1. 准备                                                      | 2. 整理 PSD                       | 3. 生成 UMG                    |
| :----------------------------------------------------------- | :-------------------------------- | ------------------------------ |
| 启用 `psd-organizer` 和 `psd-to-umg` 两个 skills<br>配置 `psd-pipeline` MCP<br>打开 Photoshop<br />模型使用 `GPT-5.5 / High` | `psd-organizer "D:\...\xxxx.psd"` | `psd-to-umg "D:\...\xxxx.psd"` |

> 第 3 步在 organizer 完整结束后执行，仍传原始 PSD 路径；生成的 `build_widget.py` 由项目人员在 UE Editor 中运行。
>
> 当前只在 `GPT-5.5 / High` 配置下完成测试。

## 8. 项目人员仍需完成什么

管线负责整理方案、切图执行编排、UMG 结构和布局、UE 构建脚本以及构建结果检查。项目人员仍需：

- 在项目 UE Editor 中运行并确认生成脚本；
- 接入业务数据、事件和字段绑定；
- 处理输入、导航、动画与复杂交互；
- 检查多分辨率表现和项目特殊规则；
- 完成最终视觉验收。

管线自动化的是实现初版，不替代业务接入和最终视觉验收。

## 9. 演示视频

**[观看完整演示视频→](./assets/video/psd2umg.mp4)**
