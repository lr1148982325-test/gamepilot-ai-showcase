# Figma2UE：弥合 Figma 设计稿与 Unreal UMG 之间的实现鸿沟

当游戏 UI 进入 Unreal Engine 项目的实现阶段时，设计侧通常已经就绪：Frame、Auto Layout、组件、Variant 与 Prototype 链接都已在 Figma 中定义完成。剩下的工作是一个高密度的生产环节——把这些视觉语义转译为真实的 UMG 资产：Widget Blueprint、面板层级、锚点与 Slot、纹理、材质、字体，以及团队可以继续开发、评审和重新导入的 Blueprint 绑定。

## 1. 真实场景：设计已完成，引擎侧却从零开始

在生产中，UI 设计与引擎集成运行在两套组织原则不同的工具里：

- 设计师用 Figma 的 Frame、Auto Layout、Constraints、组件/Variant、图片填充和 Prototype 导航定义界面长什么样、界面之间如何连接。
- 开发者用 UMG 的 `CanvasPanel`/`HorizontalBox`/`VerticalBox`/`WrapBox`、锚点、Slot、`UImage`/`UTextBlock`/`UButton`、材质、字体和 Widget Blueprint 绑定定义界面在运行时如何工作。
- 实现阶段这两个模型必须汇合：每个 Frame 要变成 Widget 树，每种填充要变成纹理或材质，每个文本层需要真实字体，导航最终要落成编译通过的 Blueprint 逻辑。

设计文件无法被简单地"导入"。Figma 按视觉构成组织，UMG 按运行时职责组织。一个 Figma 组件可能展开为包含 Switcher、多个面板、图片和文本的 Widget Blueprint；一个 Auto Layout Frame 必须变成带 padding 和尺寸规则的 Box Slot；一个图片填充需要字节、纹理资产和正确的 UV 行为。实现者必须先理解两套结构，才能决定每个节点如何落地。

| 典型场景 | 要做的事 | 常见风险 |
| --- | --- | --- |
| 完整 UI 文件首次导入 | 把全部 Frame/组件层级重建为 Widget 树，产出全部纹理/材质/字体资产，接好 Prototype 导航。 | 数百个节点的手工重建；命名与布局规范随界面漂移。 |
| 已上线界面的设计改版 | 重新转译改动 Frame，重新生成受影响资产。 | 没有稳定身份时，重导入会覆盖或重复资产；手工改过的 Blueprint 内容丢失。 |
| 组件库驱动的 UI | 把 Figma Component、Component Set、Variant、Instance Swap 映射为可复用 Widget Blueprint。 | 远程 Library 组件无法解析；Instance 悄悄退化为贴图。 |
| 多分辨率布局 | 导入后让 Figma constraints 仍然有效，面板在不同尺寸下表现正确。 | 绝对坐标快照只适配一种分辨率；锚点需要手工重建。 |
| 团队交接与评审 | 反复比对生成的 Widget 树、资产和绑定与设计稿。 | 上下文散落在 Figma、导出文件和 Unreal Editor 三处。 |

每次设计改版都会重新触发同一条链：重新找图层、重新切图、重新配置 Widget、重新校对结果。瓶颈不只是切图慢——而是缺少一条能保持语义、约束资产规则、支持安全重导入的连续工程路径。

## 2. 核心问题：设计语义到运行时语义之间没有工程化路径

Figma 和 Unreal Engine 各自的核心能力都不缺。缺口在两者之间：没有一条生产路径能把 Figma 文档的结构、布局规则、组件和交互完整地带进 UMG。实现者实际上成了人肉适配器——读一套层级，在另一套里重建，手工导出资产，再用返工吸收错误。

![Figma2UE 问题模型：人工转译鸿沟](assets/images/figma2ue/figma2ue-problem-model_cn.svg)

| 核心痛点 | 传统流程中的表现 | 需要的工程能力 |
| --- | --- | --- |
| 跨结构转译 | Figma 按视觉构成组织，UMG 按 Widget 职责组织，粒度与层级很少一一对应。 | 保留官方 REST 文档语义的类型化 Parser，把节点确定性地映射到 UMG 面板、Slot 与属性。 |
| 资产语义丢失 | 图片填充、渐变、描边、矢量图形、字体各自需要不同的资产处理。 | 按类型的资产 Builder：显式身份、填充模式 UV 映射、渐变/描边材质、复杂矢量的光栅回退。 |
| 布局意图被丢弃 | Auto Layout、constraints、尺寸规则被压平成一张静态快照。 | H/V/Wrap Box 映射、HUG/FILL 尺寸、绝对定位例外处理，以及在真实 Canvas Slot 上的 constraints→Anchors 转译。 |
| 组件无法往返 | Library 组件、Variant、Instance Swap 默认没有 UMG 对应物。 | 跨文件引用修复、按轴稳定状态的 WidgetSwitcher、按 stable key 解析 Instance Swap。 |
| 重导入是破坏性的 | 重新导入会覆盖手工修改，或留下孤儿资产。 | 稳定 node-ID 身份 + ownership manifest，先分类 Added/Updated/Unchanged/Orphaned 再谈删除。 |
| 凭据与安全 | Token、超大图片、重新压缩的归档会腐蚀管线或泄露机密。 | 会话级凭据、构建前的容器预检、像素解码前的字节预算。 |

## 3. 产品定位：两个正式输入，一条共用 UMG 构建链

> **通过两个正式入口之一取得 Figma 文档，然后运行同一条 Parser/Builder 管线，产出真实、可重导入的 UMG 资产。**

Figma2UE 由一个 Figma Desktop 导出器和一个面向 Unreal Engine 5.7 的源码级 Editor 插件组成。**Token REST** 与 **Plugin ZIP** 是两个正式入口：它们只在"如何取得 canonical REST-compatible 文档与资源字节"上不同。获取之后，两路汇合到同一条 `PrepareCanonicalFile` → `FixReferences` → Asset/Widget Builders → Blueprint 编译/重载/绑定/保存链路。没有第二套文档模型、Parser 或 ZIP 专用构建语义。

| 项目 | 产品契约 |
| --- | --- |
| 输入 A — Token REST | Personal Access Token + File Key，可选 node-ID 子集（`Ids`）与自动下载的 Library File Keys；图片 URL 按可配置批量与 `NodeImageScale` 获取。 |
| 输入 B — Plugin ZIP | 1 个 main 归档 + 0..N 个手工选择的 Library 归档，每个文件由同一个 Figma Desktop 导出器生成。无需 Token；导入阶段不访问 Figma 网络。 |
| Canonical 契约 | 两个入口都产出官方 `JSON_REST_V1` 文档形状 + 资源字节；archive v1 记录真实 `documentKey`、scope（`FILE` / `NODE_IDS`）与光栅倍率。 |
| 输出 | `ContentRootFolder` 下的 Widget Blueprint、纹理、材质与字体引用（`Components/`、`Menu/`、`Textures/`、`InstanceTextures/`、`Material/`），可直接按普通 UMG 资产使用。 |
| 共享构建选项 | 同一个 `URequestParams` 模型驱动两条入口：Prototype flow、frame-to-button、缺图策略、Widget overrides、Google Fonts、ContentRoot、末尾保存。 |
| 结构原则 | 获取是两路唯一允许不同的环节。canonical 文档之后的一切——引用修复、Builder、编译、绑定、保存——全部共用。 |
| 重导入 | 同一入口、同一路径：稳定 node-ID 身份更新生成资产、应用 Figma 侧删除/重排、保留用户自建 Blueprint 内容，并报告孤儿资产。 |

产品边界是"设计稿到 UMG"的实现环节。Figma2UE 不做视觉设计，不发明 Prototype 数据之外的交互逻辑，也不替代对生成 Widget 的最终人工评审。导入器只在 Editor 中运行；打包游戏直接使用生成资产，不依赖导入器。

## 4. 统一导入面板：单入口与双路径的对称设计

Content Browser 中的单一入口——**Add New → Import Figma...**——打开一个品牌化面板。分段 Tab 栏在 REST API 与 ZIP Package 两个子页面之间就地切换；两个子页面共用同一条实时状态条、主操作按钮和校验行为。

![Figma2UE 统一导入面板解析](assets/images/figma2ue/figma2ue-importer-panel_cn.svg)

*面板显示从 `.uplugin` 读取的真实插件版本；任一导入进行中时锁定 Tab 栏；输入无效时禁用主操作；成功、失败或取消后终态消息持久保留。*

| 区域 | 信息与操作 |
| --- | --- |
| 品牌头部 | 插件标题与真实版本号、一句用途说明、`FIGMA → UMG` 徽标和强调色分隔条。 |
| 分段 Tab | `SSegmentedControl` 切换由 `SWidgetSwitcher` 承载的 REST / ZIP 子页面；导入进行中锁定。 |
| REST 子页面 | 完整 14 字段 `URequestParams` details view；**Get Token**、**Find File Key**、**Get API Key** 按钮只用系统默认浏览器打开 Figma/Google 官方说明。 |
| ZIP 子页面 | 面内 **Browse...** 选择恰好一个 main 归档，**Choose Libraries...** 按需多选 Library 归档；显示 8 个共享构建字段，隐藏 6 个 REST 获取字段。 |
| 状态条 | 四态圆点（idle / working / success / error）+ 持久消息行。 |
| 操作行 | 主按钮在导入中显示忙碌指示与 `Importing…`，输入未通过校验时保持禁用。 |

前置校验在任何请求发出之前执行：REST 缺 Token 或 File Key、ZIP 未选主档、主档或 Library 归档被删除，都会立即弹出可操作的模态错误，而不是发起一次注定失败的导入。终态同时呈现在三处——状态条、编辑器通知（成功带完成图标）和 `Figma2UE` Output Log。

## 5. 核心工作流

![Figma2UE 核心工作流：双入口，一条共用构建链](assets/images/figma2ue/figma2ue-core-workflow_cn.svg)

### 5.1 两个正式输入

**Token REST** 保留参考工作流：Token + File Key 拉取完整文件或 `Ids` 子集；Library File Keys 自动下载；rendered-image URL 按可配置批量（`MaxURLImageRequest`，默认 20）和选定 `NodeImageScale` 请求。HTTP 408/429/502/503/504 走 UE 的有限重试管理器并原生支持 `Retry-After`；超时或被拒绝的过重渲染批次只对该恢复集合二分拆批直到单 ID，处理完成后恢复用户配置的批量。

**Plugin ZIP** 把获取环节搬进 Figma Desktop。导出器逐页 `loadAsync()`，调用官方 `page.exportAsync({ format: 'JSON_REST_V1' })`——不维护手写字段级 serializer。两种 scope：`Entire file` 导出全部 page；`Current selection` 把原始选择记录为 `NODE_IDS`，保留所有 Canvas 壳与通往选择的祖先分支，并闭包本地 Component/ComponentSet 定义和实际 interaction/transition 目标——Canvas 的 `prototypeStartNodeID` 本身不会把无关 screen 带入归档。导出器通过私有插件 API 读取真实 `figma.fileKey` 写入归档 `documentKey`，按 `imageRef` 收集图片填充字节，按选定倍率把复杂矢量与未解析 Instance 渲染为 PNG node-raster；必需资源不可读、不是可解码 PNG/JPEG 或超出像素预算时明确失败。UI iframe 用 `networkAccess: none` 的环境把 `manifest.json + assets/*` 组装为确定性 STORE ZIP（fflate，level 0）。

远程 Library 使用同一个导出器：逐个打开 Library 源文件、每文件导出一个 ZIP，再在导入选项中手工多选。Figma Plugin API 在无 Token 时不能读取另一个文件的完整文档，因此逐文件导出 + 手工选择就是当前的产品流程，而不是临时捷径。

### 5.2 共用的确定性管线

两路在 Parser 之前汇合。整条管线是 `UFigmaImporter` 上的串行状态机：

1. **PrepareCanonicalFile**——每个文档（REST main、REST Library、ZIP main、ZIP Library）都经过同一个 `DeserializeReflectionFields → PostSerialize → SetImporter`；ZIP 会先对整批做容器与身份预检，任何失败都发生在第一个 Builder 启动之前。
2. **FixReferences**——本地与远程 Component/ComponentSet 引用按文档命名空间修复（REST 按 `FileKey`，ZIP 按 `documentKey`）；启用 Prototype flow 时同步预备导航目标，生成独立 Widget Blueprint。
3. **Asset Builders**——纹理（`imageRef` 原图或 `node-raster` 回退）、填充/渐变/描边材质、FIT/TILE/轴对齐 STRETCH 的共享 UI 材质、字体与 Widget Blueprint 壳；每个资产请求以 `(documentKey, kind, sourceId)` 为键。
4. **Widget Builders**——Canvas/HorizontalBox/VerticalBox/WrapBox 面板、SizeBox、Image、TextBlock、Button、Border、WidgetSwitcher 组装 UMG 树；Figma constraints 在真实 Canvas Slot 上转为 UMG 锚点，`HUG`/`FILL`/`layoutGrow` 映射为 Slate 尺寸规则，绝对定位子节点退出 Auto Layout 流。
5. **编译、绑定、保存**——两轮 compile/reload，随后绑定与属性 patch，最后 `SaveAllAtEnd`；ownership manifest 只在完整成功的保存之后落账。

布局与绘制遵循显式来源规则而不是猜测：`absoluteBoundingBox` 负责布局占位，`absoluteRenderBounds` 只通过 paint-only RenderTransform 表达外溢；简单 FILL 图片填充生成带居中裁切 UV 的纹理；复杂或旋转的 paint 输出显式 unsupported 诊断而不是静默降级；`TEXT_PATH`、`TRANSFORM_GROUP` 等新节点类型复用矢量光栅回退；`EMOJI` 与 `VIDEO` paint 记录 warning 并跳过。

### 5.3 稳定重导入与所有权

重导入是会修改项目内容的构建步骤，并且按构建步骤来设计：

- Package 身份锚定真实 `documentKey`、manifest name、Figma node ID 与 `ContentRootFolder`——重命名 ZIP 不会改写身份。
- 导入器写入 ownership manifest（`Saved/Figma2UE/Ownership`）并在 package metadata 中记录相同所有权，随后把上一次运行分类为 Added / Updated / Unchanged / Orphaned。
- 删除默认关闭、只报告；即使显式开启，也只在 build、两次编译、重载、绑定与保存全部成功后，删除当前 metadata 与记录所有权双重精确匹配的孤儿资产。
- 自动化验证了这条契约：同一路径重复导入保留用户自建 Blueprint 变量，正确应用 Figma 侧子项删除与重排；独立的第二个 Editor 进程冷启动后仍能从磁盘加载全部生成资产与用户 Blueprint。

## 6. 系统架构与责任边界

Figma2UE 横跨两个桌面应用，彼此不在对方进程中运行：Figma Desktop 导出器（主沙箱 + iframe UI）和 UE 5.7 Editor 插件（面板、导入状态机、Parser、Builder）。archive-v1 ZIP 是离线交接物；Figma 云端只有 REST 入口会接触。

![Figma2UE 系统架构与责任边界](assets/images/figma2ue/figma2ue-architecture_cn.svg)

关键架构边界：

- **获取边界：**两个入口只允许在"如何取得 canonical JSON 与资源字节"上不同。REST 入口访问 `api.figma.com`；ZIP 路径在导入期间对 Figma 的网络请求为零。
- **沙箱边界：**导出器的 `code.js` 运行在 Figma 主沙箱，只读取当前打开文档；iframe 在 `networkAccess: ["none"]` 环境下组装 ZIP，fflate 在构建期内嵌锁定版本。
- **预检边界：**UE 适配器先校验 central directory，拒绝非 STORE / ZIP64 / 加密 / 多盘 / data descriptor 归档，并在任何解析与构建开始之前执行聚合预算与身份唯一性检查。
- **线程边界：**后台线程只处理有界字节与纯 JSON；反射、`PostSerialize`、节点 `NewObject` 与引用修复统一在 GameThread 完成。
- **管线边界：**一套 Parser、一批 Asset/Widget Builder、一条编译/绑定/保存链。没有 ZIP 专用后处理，也没有第二套文档模型。
- **存储边界：**canonical ZIP 是交接物；运行时所有权状态在 `Saved/Figma2UE/Ownership`；生成资产在配置的 `ContentRootFolder` 下，是普通项目内容。

## 7. 运行时协作

一次导入以串行状态机运行，分四个相位。面板提交参数；导入器取得 canonical 载荷（REST 分批重试，或 ZIP 整批预检后的内存字节），逐文档解析、修复引用，构建资产与控件，然后编译、绑定、保存。协作式取消通道在每个安全边界轮询；每次运行以唯一终态——Success、Error 或 Cancelled——结束。

![Figma2UE 导入运行时协作](assets/images/figma2ue/figma2ue-runtime-sequence_cn.svg)

取消刻意不做破坏性回滚：当前 retry/HTTP、图片或字体请求被请求中止，后续相位不再启动，但已创建的内存资产不会被强行拆除。Blueprint 编译与保存是 UE 单次调用，无法从内部中断；较晚的取消在下一个安全边界生效，并在日志中如实报告。

## 8. 安全、质量与运行边界

### 8.1 ZIP 容器预检与预算

| 阶段 | 保护 |
| --- | --- |
| 容器 | 读取任何 member 前做 central-directory 与 local-header 预检；只接受配套 exporter 生成的确定性 STORE ZIP32。 |
| 批量预算 | 单次最多 64 个文档；物理 ZIP 合计 512 MiB、manifest 合计 16 MiB、资产总数 4096、单资产 64 MiB、资产载荷合计 512 MiB。 |
| 图片安全 | 仅 PNG/JPEG 且扩展名必须匹配解码内容；任一边 ≤ 16384 像素、总像素 ≤ 64M，exporter 与 UE 都在完整像素解码前检查。 |
| 身份 | 重复 `documentKey`、重复本地 Component/ComponentSet stable key、同文档跨 kind 的 sourceId 歧义都会整批失败；资产按 `(documentKey, kind, sourceId)` 隔离。 |
| 缺失字节 | exporter 省略的必需资源由共享的 `ProgressOnFailToDownloadImage` 策略裁决；实际到达的非法字节直接硬失败。 |

### 8.2 凭据与网络

- Figma Token 与 Google Fonts API Key 是会话级密码字段；不写入项目配置、ZIP 或日志。
- 帮助按钮只打开 Figma Token 官方生成页、File Key 官方说明与 Google Fonts 取 Key 小节；不读取剪贴板或浏览器登录态。
- ZIP 路径不调用 Figma REST。两条路径都只有在启用下载且会话 Key 非空时才可能访问 Google Fonts；否则文本通过确定性的 family/style/weight 映射解析项目/引擎已有字体，未解析时给出明确诊断。
- 导出器依赖 `enablePrivatePluginApi` 读取真实 `figma.fileKey`，因此以 Development 或组织 Private plugin 形态分发，不作为公开 Community 插件发布。

### 8.3 失败与取消语义

- 终态只发出一次；取消之后晚到的 HTTP 完成回调不能继续推进管线。
- 编译/保存失败按失败传播——坏构建永远不会回报成功。
- 取消不回滚已创建资产；日志精确说明运行停在哪一步，ownership 报告让下一次运行保持诚实。

### 8.4 验证门禁

每次变更必须通过四项规定门禁：Figma 导出器的 Node 测试与生产构建、确定性 smoke ZIP fixture 生成，以及 UE 5.7 Harness 运行 Editor smoke 套件和独立的冷启动持久化进程。当前 `v0.8.0` 基线为 Node 39/39、16 个 ZIP fixture、Editor smoke 31/31（0 warning、0 fail）、持久化 1/1。专门的 parity 测试把同一 canonical fixture 分别经模拟 REST seam 与真实 STORE ZIP 字节导入隔离 ContentRoot，比较归一化语义快照——资产集合、Widget 树、Slot、Brush、绑定、函数/事件图与纹理指纹——必须完全一致。

## 9. 能力范围与运行要求

### 9.1 当前能力

| 能力 | 当前行为 |
| --- | --- |
| 双入口 | Token REST（完整文件或 `Ids` 子集，Library 自动下载）与 Plugin ZIP（1 个 main + N 个手工选择的 Library 归档），汇合到同一管线。 |
| 布局 | Canvas/绝对定位、Horizontal/Vertical/Wrap Auto Layout、padding、spacing、alignment、`FIXED`/`HUG`/`FILL`、绝对定位子节点、GRID 降级为已解算几何 Canvas、constraints → UMG 锚点。 |
| 视觉 | 纯色填充、FILL 居中裁切 UV 的图片填充、FIT/TILE/轴对齐 STRETCH 共享 UI 材质、渐变、描边、圆角，以及矢量与复杂节点的 PNG 光栅回退。 |
| 组件 | Component、Instance、Component Set、单轴 Variant（WidgetSwitcher）、多轴按轴稳定状态与确定性回退、`TEXT`/`BOOLEAN`/`INSTANCE_SWAP` 属性。 |
| Prototype | 已验证的同文件 `NAVIGATE` 及 `OVERLAY`/`SWAP`/`CLOSE` 接线与 frame-to-button 规则；`BACK`/`SCROLL_TO`/`CHANGE_TO` 保留结构化数据并输出精确诊断。 |
| 文本与字体 | 真实 UMG 文本 + 本地 family/style/weight 字体映射；两条入口均可选 Google Fonts 下载。 |
| 命名 | Designer 层级显示原始 Figma 图层名；内部 `--nodeId` 后缀保持重名、引用与重导入身份稳定。 |
| 重导入 | 稳定身份更新、Figma 删除/重排生效、用户内容保留、Added/Updated/Unchanged/Orphaned 报告与可选清理。 |
| 运行 | 串行获取 + 有限重试与批次恢复、协作式取消、前置校验与终态通知。 |

### 9.2 环境与依赖

| 项目 | 要求 |
| --- | --- |
| Figma | Figma Desktop；导出器以 Development plugin 或组织 Private plugin 运行。 |
| Node.js | `22+`，用于导出器测试与 `dist/` 生产构建。 |
| Unreal Engine | `5.7`；项目级源码插件，需匹配的 C++ 工具链。 |
| 操作系统 | 已验证与描述符 allow-list 目标是 Windows/Win64；macOS/Linux 未验证。 |
| Figma 网络 | 仅 REST 入口需要；ZIP 入口对 Figma 完全离线。Google Fonts 两路均为可选。 |
| 运行时 | 导入器只在 Editor 运行；打包游戏直接使用生成资产。 |

## 10. 演示视频

**[观看完整 Figma2UE 演示视频 →](assets/video/figma2ue.mp4)**
