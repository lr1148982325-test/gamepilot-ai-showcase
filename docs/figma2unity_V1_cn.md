# Figma2Unity：确定性的 Figma 到 Unity UI 还原管线

在游戏或应用的 UI 管线里，设计稿在 Figma 中"定稿"的那一刻，往往并不是它在引擎里"完成"的那一刻。美术侧已经在 Figma 中完成了页面；客户端侧还需要把这些页面转成可编辑的 Unity UI——层级、布局、文本、图片、控件与接线——才能真正交给玩法使用。这道翻译工序，传统上是整个交付中操作最密集、最受 token 门槛限制、也最容易被改版反复触发的环节。

Figma2Unity 将这道工序产品化为一条确定性管线：一个免 token 的 Figma Desktop 插件，把选中的页面或画框导出为自包含、版本化的 `.f2u.zip` 数据包；Unity 校验该数据包后，物化出可编辑的 UGUI/TMP Prefab 或 UI Toolkit 文档，并提供显式的保真回退与所有权感知的重新导入。它解决的不是"这个设计是什么意思"的语义问题，而是"如何把 Figma 设计可复现地搬进 Unity、保持可编辑、并在设计变化时安全更新"的工程问题。

## 1. 实际应用场景：设计模型已定稿，但可编辑的 Unity UI 仍需产出

在实际项目中，Figma2Unity 面向的是"设计完成"与"Unity 界面可用"之间那一步反复出现的手递手工作。同一条管线、同一份契约、两种渲染器，区别主要在于输入的来源与输出所面向的 Unity 框架。

| 典型场景 | 实际需要完成的操作 | 容易出现的问题 |
| --- | --- | --- |
| 新页面首次实现 | 导出定稿的 Figma 页面 / 画框，把完整层级、布局、文本、图片与控件物化进 Unity。 | 手工重做慢；页面规模越大，节点查找、资源导出与组件配置的操作量越高。 |
| 设计稿局部改版 | 定位受影响的根节点，重新导出，只更新受影响的生成对象。 | 局部变化可能触发整体重建，或覆盖用户已拥有的组件与接线。 |
| 多框架交付 | 先为 UGUI 产出，之后再为 UI Toolkit 产出同一份设计，或把同一数据包交给另一支团队。 | 各框架各自重建会逐渐分叉，资源与命名跨渲染器不一致。 |
| 视觉与功能联合验收 | 在 Unity 结果与 Figma 源之间反复对照位置、层序、文本与保真度。 | 上下文分散在 Figma、Unity、导出资源与报告之间，错位难以追溯。 |

当设计变化时，上述工作会被再次触发：重新导出、重新导入、重新验收。问题并不只是"导出慢"，而是缺少一条可复现、版本化、安全，且能复用源身份、约束写入范围、统一输出规则的工程路径。

## 2. 问题本质：Figma 设计模型与 Unity 运行时 UI 之间缺少免 token 的工程化桥梁

问题并非 Figma 或 Unity 单独缺少能力，而是两者之间缺少一条工程化桥梁。三种传统做法各有各的失败方式：

- **手工重做** 让实现者充当"人工适配器"：读懂设计稿，在 Unity 里逐层重做，再靠返工吸收漂移。慢、易错，且产出的资源无法干净地再次同步。
- **纯 REST 转换** 依赖普通 Figma 用户往往拿不到的 API token，受账号可读范围限制，且无法凭空补出插件 API 独有的证据，例如原始图片字节、完整样式区间、变量 / 组件关系与原型数据。
- **黑盒 Design-to-Code** 重新生成一个"看起来相似"的页面，但结果通常不可编辑、难以维护，没有稳定身份用于重导入，也无法安全保留用户已有成果。

Figma2Unity 用**版本化语义数据包**取代人工 / 黑盒适配器，把它作为架构边界：Figma 专属对象不渗入 Unity 渲染代码，Unity 的序列化细节也不渗入导出器。两条输入路径——免 token 的 Desktop 插件与可选授权的 Figma URL——都汇聚到同一个经过校验的数据包，Unity 才据此落盘。

![Figma2Unity 问题模型：设计定稿与 Unity 运行时之间的人工适配鸿沟](assets/images/figma2unity/figma2unity-problem-model_cn.svg)

*三种传统做法各有失败方式；根因是缺少一条免 token、可复现、安全重导入的工程化桥梁。*

| 核心痛点 | 传统流程中的表现 | Figma2Unity 的应对方式 |
| --- | --- | --- |
| token 门槛 | 转换依赖 REST token 或手工重做。 | 免 token 的 Desktop 插件只读当前登录用户可见文件，导出本地数据包。 |
| 跨工具链路割裂 | 设计在 Figma，层级、资源与验收在 Unity，上下文靠人工传递。 | 一份版本化数据包承载层级、布局、文本、图片、组件、变量、样式与报告。 |
| 产物不可编辑 | 生成的"相似"页面难以编辑、维护与扩展。 | 原生优先的 UGUI/TMP Prefab 与 UI Toolkit 文档，仍是普通可编辑 Unity UI。 |
| 身份不稳定 | 以命名为唯一同步键，改个名就断链。 | 稳定的 Figma ID、源元数据与所有权索引驱动重导入。 |
| 静默近似 | 不支持的视觉被猜或丢弃。 | 显式的 `NATIVE` / `SVG` / `RASTER` / `CONTAINER` 表示，并记录回退原因。 |
| 重导入不安全 | 重导入覆盖用户成果，或输出路径不可预测。 | 所有权感知同步：更新源拥有字段，保留用户拥有组件。 |

## 3. 产品定位：确定性的、以数据包为边界的 Figma 到 Unity 管线

> **在 Figma 中导出一次，即可确定性地物化出可编辑的 Unity UI——免 token、带显式保真回退与安全重导入。**

Figma2Unity 是面向团队的一条确定性 Figma-to-Unity 管线，提供可编辑的 Unity UI、显式的保真回退与安全的重新导入。免 token 的 Figma Desktop 插件把选中的页面或画框导出为自包含、版本化的 `.f2u.zip` 数据包；Unity 校验该数据包后，生成 UGUI/TMP Prefab 或 UI Toolkit 文档。显式授权的 Figma URL 是可选第二条输入路径。

常规手递手只需运行 Desktop 插件导出一份数据包；在 Unity 中创建场景 Converter，选择数据包、一个输出目录、恰好一种渲染器，再导入选中的根节点。Desktop ZIP 与授权 URL 两条路径汇聚到同一套校验器、导入计划、决策流程与渲染器边界。

| 项目 | 产品契约 |
| --- | --- |
| 输入 | 一份来自 Figma Desktop 插件的免 token `.f2u.zip` 数据包，或一个显式授权的 Figma URL（PAT 或 OAuth）。 |
| 输出 | 可编辑的 UGUI/TMP Prefab（默认）或 UI Toolkit UXML/USS 文档，外加图片、矢量、字体、本地化资产、设计 Token、源映射、原型流程资产与诊断报告。 |
| 统一入口 | 导出、数据包校验、渲染器选择、导入计划与审查，通过一条管线与一份版本化契约协同。 |
| 引擎职责 | 提取层级 / 布局 / 文本 / 资源 / 设计系统证据；校验；为每个节点选定显式表示；导入资源；同步 Prefab；审计几何与像素。 |
| 运行原则 | 校验后的数据包是架构边界；生成对象携带稳定源 ID 与内容哈希，使重导入确定。 |
| 处理范围 | 每次导入一份数据包；生产恰好选择一种渲染器（`UGUI` 或 `UI Toolkit`）；Nova 已退役。 |

产品边界限定在手递手工序：Figma2Unity 不替代设计创作、玩法逻辑、交互脚本与最终人工验收。它产出一个原生、可编辑、可重导入的 Unity UI 投影——而非对每个 Figma 效果的像素级截图。当 Unity 无法无损表达某个视觉时，导入器记录显式回退，而不是静默近似。

这一定位区别于通用 Design-to-Code。Figma2Unity 不以从提示词或压平图片生成"相似"页面为目标，而是把完整 Figma 文档模型经由版本化契约搬运过来，投影为普通 Unity 组件，使其仍便于持续开发、集中验收与安全重导入。

## 4. 统一工作台体验

Figma2Unity 横跨两个工作台——数据包的两侧各一个——围绕同一条"观察 → 配置 → 导出 / 导入 → 验收"流程组织。

### 4.1 Figma Desktop 导出器

插件运行在 Figma Desktop 内，只读当前登录用户可访问的文件与节点，并写出本地数据包。生产 manifest 声明不允许任何外部网络域。

| 区域 | 主要信息与操作 |
| --- | --- |
| 画框选择 | 发现当前页可见的顶层画框；按稳定 Figma 节点 ID 搜索、选择或批量选择根节点，按页面顺序输出。 |
| 导出选项 | 面向吞吐的默认项（仅 PNG 矢量、无文字栅格、无根预览），以及 Advanced 下按需开启的 SVG+PNG 回退、文字栅格证据、根预览、栅格密度与隐藏图层。 |
| 结果摘要 | 生产级阻塞项会中止下载；质量建议与保真提示单独报告，绝不伪装成成功。 |

### 4.2 Unity Editor 工作台

在 Unity 中，场景 Converter 持有本次导入。其 **Settings** 工作台按任务组织页面；框架专属页面仅在对应渲染器激活时出现。

| 区域 | 主要信息与操作 |
| --- | --- |
| Main Settings | 源、输出目录、渲染器、命名、审查、备份与保真默认项。 |
| Figma Auth | 授权 URL 路径的 OAuth / PAT 账号与租户设置。 |
| Images & Sprites | 栅格、SVG、Sprite 导入器、PPU、压缩与图集策略。 |
| Text & Fonts | 字体来源与映射、Google Fonts、文本后端与生成策略。 |
| Buttons / Shadows / Prefab Creator | UGUI 专属的组件与过渡、阴影、可复用 Prefab 设置。 |
| UI Toolkit | UI Toolkit 专属的 UXML / USS / 模板 / linker / `UIDocument` 设置。 |
| Localization / Script Generator | 逻辑字符串输出与 CSV 设置；类型化语义绑定生成。 |
| Import Events / MCP Server / Debug | 源读取 / 下载 / 导入回调；受限本地 MCP；报告、校验、缓存与备份。 |

**Import Review** 不是常驻设置页。它只在活动导入因布局、Sprite 或排版决策而暂停时替换普通导航，决策解决后即返回普通设置。普通观察与配置从不写资产；只有显式导入（或显式发起的设置）才会改动生成产物。

## 5. 核心工作流

![Figma2Unity 核心工作流：两条入口汇聚为同一份数据包，五个确定性阶段产出可编辑 Unity UI](assets/images/figma2unity/figma2unity-core-workflow_cn.svg)

*Desktop 插件与授权 URL 两条入口共用同一份契约 2.2.0 数据包；校验、共享资产物化、渲染器投影与审计全部确定性执行。*

### 5.1 免 token 导出（主路径）

1. 打开包含待交付画框的 Figma 页面；插件作用于当前页。
2. 搜索并选择要导出的可见顶层根节点，按页面顺序输出。
3. 保持吞吐默认项，仅在交付或视觉验收流程需要时开启 Advanced 选项。
4. 选择 **Export .f2u.zip**，等待校验与资源渲染完成。
5. 查看摘要——生产级阻塞项会中止下载；把原始 ZIP 交给 Unity，不要解压或重打包。

### 5.2 Unity 导入（ZIP 路径）

1. 选择 **Tools → Figma2Unity → Create Converter**，选中 Converter GameObject。
2. 将 **Import mode** 设为 **Desktop Plugin ZIP**，拖入或浏览 `.f2u.zip`。
3. 在 `Assets/` 下选择 **Output folder**，并选择恰好一种 **UI framework**（`UGUI` 或 `UI Toolkit`）。
4. 选择 **Read ZIP project**，查看 Page/Frame 树，选择要导入的画框。
5. 选择 **Import n selected frame(s)**。若导入暂停，完成聚焦的 **Import Review**，或在不接受的情况下停止。

### 5.3 授权 Figma URL 路径（可选）

URL 路径是可选的，从不取代免 token 工作流。它只拉取配置账号可读的内容，在 `Library/Figma2Unity/FigmaApi` 下准备一个有界的本地 `.f2u.zip`，然后运行与 ZIP 路径相同的校验器、计划器与渲染器边界。相比 Desktop ZIP，它可能缺少插件 API 独有的证据。

### 5.4 确定性重导入

保留现有 Converter、输出目录、生成资源、源 sidecar 与 `.meta` 文件。导出一份新数据包，通过同一 Converter 重导入。稳定源 ID 让 Unity 更新已接受的源拥有字段，同时保留已注册的用户拥有组件与子节点。只有成功导入的根节点才推进其已保存快照；未选中的变化保持待定。

### 5.5 保真策略

每个节点都被赋予显式的 `representation`：

1. **NATIVE**——层级与视觉可由受支持的 Unity 组件无损表达。
2. **SVG**——矢量源为准；可附带 PNG 预览。
3. **RASTER**——节点图片为准，通常用于叶子或压平的子树。
4. **CONTAINER**——仅层级 / 布局，自身无图形。

导出器记录每次回退的原因；导入器从不猜测某个回退等价于原生。不支持的蒙版、效果、绘制合成、排版或变换，使用显式的 SVG / 栅格 / 静态预览属主，或产生阻塞性诊断。

![Figma2Unity 保真策略：四种显式表示在可编辑性与像素保真上的定位](assets/images/figma2unity/figma2unity-fidelity-policy_cn.svg)

*同一源节点按支持矩阵被分类为四种表示之一；回退必记录原因，未知或未来类型失败关闭。*

## 6. 系统架构与职责边界

Figma2Unity 将提取、传输、校验与物化分层。受约束的数据契约把 Figma 模型、数据包、共享资源库与生成产物分别纳入独立边界。

![Figma2Unity 系统架构：Figma 与 Unity 两个本机进程以版本化数据包为唯一交接边界](assets/images/figma2unity/figma2unity-architecture_cn.svg)

*数据包是架构边界；Figma 专属对象不渗入 Unity 渲染代码，Unity 序列化细节也不渗入导出器。*

- **Figma Desktop 插件（导出器）**——发现可见根节点，提取层级 / 布局 / 变换 / 文本区间 / 设计系统证据 / 交互 / 图片 / 矢量 / 预览，选定显式表示，写出确定性的数据包条目、哈希、诊断与质量报告。它从不抓取任意文件、绕过权限、导入 Unity 或写回 Figma。
- **版本化语义数据包**——架构边界。包含 `manifest.json`、`project.json`、逐根的 `nodes/*.json`、`images/`、`vectors/`、`previews/` 与 `reports/`。导入器拒绝不支持的主版本、容忍增量次字段；ZIP 解压路径安全且有界。
- **校验与迁移**——在任何写入前校验契约、哈希、路径、大小与图；把历史 `1.x` 数据包迁移到当前契约。
- **共享资源 / 字体 / Token**——位于 `Assets/Figma2Unity/Shared/` 下、与输出无关的存储，配以按 blob/profile 与 GUID 键控的所有权索引（`SharedAssetIndex`、`SharedFontIndex`）。复用需所有权、profile、字节与 GUID 全部匹配。
- **渲染器输出**——恰好一种生产渲染器：UGUI/TMP（或 Unity UI Text）Prefab，或 UI Toolkit UXML/USS/源映射。选择是 Unity 消费方策略，绝不写入数据包。
- **审计**——每个根节点保存后，导入器在隔离预览场景中实例化它，按契约测量几何；视觉管线捕获逐渲染器像素证据用于 diff。

可选集成（Unity Vector Graphics、Unity Localization）在独立适配器程序集中持有全部第三方类型；其缺失不会破坏基础包的编译。

## 7. 运行时协作

一次正常导入是跨越数据包边界的一条协同流程。Desktop 插件（或授权 URL 适配器）准备一份已校验数据包；Unity 导入器校验并迁移它、制定导入计划、物化共享资源 / 字体 / Token、投影所选渲染器，最后运行几何与像素审计。可审查的决策——布局、Sprite 复用与排版——可暂停导入以做出显式选择，而非静默猜测。

![Figma2Unity 运行时协作：导出、校验与计划、物化与投影、审计与交付四个相位](assets/images/figma2unity/figma2unity-runtime-collaboration_cn.svg)

*Import Review 的可选暂停用虚线标出：决策解决后导入才继续；审计产出的诊断与 diff 证据随报告落盘。*

## 8. 质量、安全与运行边界

### 8.1 保真策略

- 原生优先：只要能无损表达源，就优先使用 Unity 组件。
- 显式回退：不支持的视觉获得记录的 SVG / 栅格属主或阻塞性诊断——绝不静默近似。
- 源与渲染分离：原始 PNG/JPEG 字节（`purpose: SOURCE`）保存在 `Assets/Sources/` 下，但绝不能填充 Prefab Image；只有渲染保真通道可以。
- "原生或精确"是刻意策略：成功导入不承诺每个节点都保持可编辑，也不承诺每个原生投影都像素级等价。

### 8.2 安全导入边界

- ZIP 解压有界：10,000 个条目、每条目 256 MiB、解压总量 1 GiB；绝对路径、`..` 穿越、超限大小、重复 ID 与非法哈希一律失败关闭。
- 不支持的契约主版本、不安全归档、所有权漂移与不可用渲染器一律失败关闭。
- 带阻塞项的 Figma 数据包不会被下载；必需的资源 / 导出 / 契约 / 图失败仍是生产错误。

### 8.3 所有权感知的重导入

- 生成对象携带稳定源节点 ID 与内容哈希；Figma 名称是公开标签，而非同步键。
- 重导入更新已接受的源拥有字段，保留用户组件、持久化 UnityEvent 与显式用户拥有的子节点。
- 被移除的源节点会被报告并要求显式清理策略；源元数据是本地重导入链接，而非 Unity 到 Figma 的双向同步。

### 8.4 网络与凭证边界

- 插件运行时声明 `allowedDomains: ["none"]`；主路径不把设计数据发送到外部服务。
- 可选 URL 路径是配额被动的：仅在显式拉取后执行网络工作，且从不绕过 Figma 权限。
- 机密存放在当前用户的 Unity `EditorPrefs`（或 CI 环境变量）中，绝不进入工程设置、数据包、报告或 Git。

### 8.5 验证门禁

每次变更必须通过规定门禁：Figma 导出器的 Node 测试与生产构建、契约的 .NET 测试与 Python 离线包检查；有 Unity Editor 可用时还需运行 EditMode 套件，并对照匹配的 Figma 预览执行截图 diff。已执行发布基线为 Windows + Unity `2021.3.36f1c1` + Built-in Render Pipeline；像素证据要求真实图形设备，`-nographics` 输出不构成有效视觉证明。

## 9. 能力范围与使用条件

### 9.1 当前能力

| 能力 | 当前行为 |
| --- | --- |
| 免 token 导出 | Desktop 插件把选中页面 / 画框导出为自包含 `.f2u.zip`；无 REST token、无外网。 |
| 授权 URL 导入 | 可选 PAT/OAuth 路径准备同一数据包；账号权限与租户边界被强制执行。 |
| 两种生产渲染器 | 可编辑 UGUI/TMP（或 Unity UI Text）Prefab，或 UI Toolkit UXML/USS/源映射；Nova 已退役。 |
| 确定性重导入 | 稳定 Figma ID、源元数据、可预测路径、共享资产索引与所有权感知同步。 |
| 显式保真策略 | 原生优先 + SVG/栅格回退 + 阻塞性诊断；源与渲染资源分离。 |
| 丰富设计证据 | 组件、变体、变量、样式、本地化、原型动作、字体要求、可访问性元数据与诊断。 |
| 可审查导入 | 布局、Sprite 复用与排版决策可暂停导入以做显式选择。 |
| 安全本地工具 | 有界且路径安全的 ZIP 解压；可选本地 MCP 证据只读、写操作需显式确认，且绝不写回 Figma。 |

### 9.2 环境与依赖

| 项目 | 要求 |
| --- | --- |
| Figma | Figma Desktop，用于免 token 导出器；插件通过本地 `manifest.json` 加载。 |
| Unity | Unity `2021.3` 或更新；已执行发布基线 `2021.3.36f1c1`（Windows / Built-in）。 |
| 包依赖 | Newtonsoft JSON `2.0.2`、2D Sprite `1.0.0`、TextMeshPro `3.0.6`（UGUI/TMP 输出需 TMP Essential Resources）。 |
| 可选集成 | Unity Vector Graphics `[2.0.0-preview.24, 2.1.0)`；Unity Localization `[1.0.0, 2.0.0)`。 |
| Python | `3.10+` 仅用于可选本地 MCP 服务（脚本随包附带）。 |
| Node.js | `22+` 仅用于源码开发构建路径。 |

## 10. 演示视频

**[观看完整 Figma2Unity 演示视频 →](assets/video/figma2unity.mp4)**
