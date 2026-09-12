# NamingAudit

面向 Photoshop 与 Unreal Editor 的本地命名检查：规则契约、扫描处理与源对象定位。

**NamingAudit** 项目交付 **Naming Audit 命名检查插件**，分别以 Photoshop UXP 面板和 Unreal Editor 插件运行。两端依据 `RuleConfigV2` 定义执行字符级、标识符结构及平台名称约束检查，按源对象聚合诊断，并提供宿主内定位能力。检查过程只读文档与资产；名称修改、引用验证及保存由使用者在宿主中执行。

<div class="scope-grid" aria-label="范围说明">
  <div><strong>宿主内检查</strong><span>Photoshop UXP 面板与 Unreal Editor 插件，不是独立可执行程序</span></div>
  <div><strong>本地求值</strong><span>无网络传输、无共享服务、无模型推理依赖</span></div>
  <div><strong>只读诊断</strong><span>不自动改名、搬移、修复引用，也不构成阻断门禁</span></div>
  <div><strong>宿主负责修正</strong><span>改名、保存、编译与引用验证仍属宿主原生工作流</span></div>
</div>

## 1. 检查对象与结构化诊断契约 {#overview}

工具面向 UI 美术、资源制作人员和技术美术，覆盖 PSD 文档及图层树、UE 资产名称与包目录段、Widget Blueprint 的源控件树。宿主适配器负责确定送检粒度与定位上下文，规则引擎不将完整文件路径直接作为单个名称求值。

| 输入类别 | 名称预处理与求值范围 | 诊断上下文 |
| --- | --- | --- |
| PSD 文档、图层、组、画板 | 文档名剥离最后一个扩展名；图层树逐对象枚举名称 | 文档路径、对象层级、图层定位标识 |
| UE 资产与包目录 | 分别求值资产名和各目录段；跳过挂载根及结构性路径分隔符 | 资产路径、命中目录来源、引擎补充说明 |
| UMG 源控件 | 检查当前 Widget Blueprint 的源 `WidgetTree`，不进入其他嵌套蓝图内部树 | 所属蓝图、源控件名称、层级路径 |

![命名检查问题模型：宿主输入预处理、三类谓词粒度、NamingIssueV2 字段与对象级聚合矩阵](assets/images/namingaudit/problem_cn.svg)

*图中区分 scalar、标识符结构与整名级谓词，并通过默认规则示例说明“多规则命中、单对象聚合”的诊断语义。示例不代表本次运行测试结果。*

共享 `NamingIssueV2` 契约由三部分组成：

- **对象身份：**`host`、`targetType`、`name`、`documentPath`、`hierarchyPath`。
- **命中证据：**非空且去重的 `ruleIds`、`matchedFragments`；可选的 `ruleLabels` 保存求值时的规则显示名称快照。
- **定位能力：**`canLocate=true` 时 `locatorId` 必须为非空字符串；否则为 `null`。`locatorId` 是宿主内部不透明标识。

UE 内部的 `MatchedPathSegments`、`EngineReason` 等信息用于补充路径来源与引擎说明，不是当前共享 JSON Schema 的字段。共享 Schema 不包含 `severity` 或 `blocking` 字段；V2 问题按 warning 呈现。

**规则与求值规格：**

- **19 条内置规则 / 5 个语义分类：**标识符结构（3）、语言与字符宽度（4）、组合符、空白与不可见字符（3）、标点与符号（6）、路径与平台约束（3）。分类仅用于组织说明，`ruleIds` 输出顺序由契约固定，与分类无关。
- **3 种求值粒度：**Unicode scalar 谓词、标识符结构谓词（连续 / 首尾下划线）、整名级平台谓词（Windows 保留名与尾随字符）。三类可同时命中同一名称。
- **9 个必填字段：**`host`、`targetType`、`name`、`documentPath`、`hierarchyPath`、`matchedFragments`、`ruleIds`、`canLocate`、`locatorId`；`ruleLabels` 为可选显示名快照。
- **每源对象至多一条诊断：**多个谓词命中同一对象时，规则 ID、字符片段与规则标签聚合到同一记录；`ruleIds` 为空则不创建问题。

## 2. 宿主工作台与源对象定位 {#workbench}

<div class="screenshots">
  <figure>
    <div class="figure-heading"><span class="host-label">UNREAL EDITOR</span><span>UE 4.27 · 插件 v1.3.6</span></div>
    <img alt="UE4.27 实机面板：扫描 3 个测试资产，发现 2 个问题，可查看详情并定位" src="assets/images/namingaudit/namingaudit-unreal-panel.png" />
    <figcaption>UE4.27 独立测试工程的实际扫描结果：3 个资产、2 个问题。面板包含扫描范围、分组诊断、详情、定位与分页控件。</figcaption>
  </figure>
  <figure>
    <div class="figure-heading"><span class="host-label">PHOTOSHOP</span><span>26.1 · 插件 v1.3.8</span></div>
    <img alt="Photoshop 26.1 实机面板：检查当前 PSD、筛选问题、定位图层和个人设置" src="assets/images/namingaudit/namingaudit-photoshop-panel.png" />
    <figcaption>Photoshop 26.1 的实际 UXP 面板，包含扫描、筛选、分页与对象定位。截图使用含自定义规则的本机配置，问题数量不对应默认规则基线。</figcaption>
  </figure>
</div>

诊断以源对象为单位组织。同一对象命中多个谓词时，规则 ID、字符片段和规则标签聚合到同一条记录，问题对象数量与规则命中数量分别解释。

- **Unreal：**结果按来源分组，详情包含完整路径、目录来源与控件层级。资产定位同步 Content Browser；UMG 定位打开所属蓝图并尝试选中源控件，精确选择不可用时保留蓝图入口与层级提示。
- **Photoshop：**结果支持按名称、路径或规则筛选，可定位图层、组和画板。文档名诊断不提供图层定位操作。
- **快照语义：**当前结果对应上一次扫描时的名称与规则状态。名称、配置或对象层级变化后，需要重新扫描。

## 3. 扫描处理流程与结果语义 {#workflow}

![扫描处理流程：手动与自动入口、范围解析、名称枚举、规则求值、有序聚合、宿主定位及扫描状态分支](assets/images/namingaudit/workflow_cn.svg)

*流程图同时标注处理阶段和中间数据。插件执行只读检查与定位；人工改名、保存、编译和引用验证位于扫描器职责之外。*

### 3.1 核心处理规则

1. **确定读取范围：**PS 使用当前文档树或已识别的导出选择；UE 使用资产选择、目录、当前 UMG 或 `/Game`，自动入口限定为相应事件对象。
2. **枚举与预处理：**普通 UE 资产读取 Asset Registry 元数据；检查 Widget Blueprint 源控件时才加载并遍历源树。名称按 Unicode scalar 遍历，不拆分 UTF-16 代理对，不改写名称。
3. **执行已启用谓词：**关闭的规则既不贡献 `ruleIds`，也不贡献 `matchedFragments`。字符、结构和整名级规则可同时命中。
4. **生成有序诊断：**内置规则按固定契约顺序输出，自定义规则按配置顺序追加；片段去重，逐 scalar 片段按首现位置排列，整名级片段随后追加。`ruleIds` 为空则不创建问题。
5. **呈现与定位：**保留规则显示名快照，按宿主提供筛选、分组、分页和源对象定位。对象已删除或层级变化时需重扫或使用定位回退信息。

### 3.2 Unreal 扫描入口

| 检查范围 | 前置条件 | 面板入口 |
| --- | --- | --- |
| 指定资产集合 | 在 Content Browser 中选中目标资产 | **当前选择** |
| 指定目录及其子目录 | 在目录树中选中目标目录 | **选择目录** |
| 当前 Widget Blueprint | 打开并激活目标蓝图编辑器 | **当前 UMG** |
| 项目 `/Game` 挂载点下的资产 | 确认当前规则配置与检查范围 | **全项目 /Game** |

执行顺序：确认规则 → 发起扫描 → 检查完成状态 → 展开诊断与定位 → 在 UE 内修改 → 按需编译、保存和验证引用 → 使用相同范围复查。

> `/Game` 不包含所有磁盘文件，也不自动包含 `/Engine` 或其他插件挂载点。取消扫描后保留已处理部分的结果，不能作为完整范围检查结论。分批调度不能约束单个 Widget Blueprint 同步加载的耗时。

### 3.3 Photoshop 扫描入口

打开目标 PSD，确认个人规则后执行**检查当前 PSD**。扫描包含嵌套图层、组和画板；文档名剥离最后一个扩展名后送检。使用者在 Photoshop 中修改并保存后再次扫描；名称变更影响导出文件名时，需重新执行宿主原生导出。

## 4. 规则配置、迁移与跨宿主交换 {#rules}

`RuleConfigV2` 根对象包含 `schemaVersion`、`builtInRules` 和 `customRules`。内置规则必须完整包含 19 个固定布尔键，默认全部开启；导出不能省略关闭项，也不能将 `false` 回填为默认 `true`。

![RuleConfigV2 技术模型：19 条规则 ID、配置字段、严格校验与确认替换流程、V1 迁移及共享回归约束](assets/images/namingaudit/rule-exchange_cn.svg)

*规则分类用于组织说明，数字序号对应固定输出顺序。配置导入是完整替换，不是合并；预览对象为规则配置，而非资产改名映射。*

| 名称示例 | 默认规则下的主要结果 | 契约解释 |
| --- | --- | --- |
| `Btn_Login_01` | 不命中 | 字符与下划线结构通过；不校验类型前缀语义 |
| `Btn__Login` | `repeated_underscore` | 连续两个或以上下划线；`matchedFragments` 仅记录一个 `_` |
| `_Btn_` | `edge_underscore` | 名称首部或尾部包含下划线 |
| `登录按钮` | `ascii_only`、`cjk` | 重叠谓词聚合为一条对象诊断 |
| `Btn` + `U+200B` + `Login` | `ascii_only`、`invisible_control` | `U+200B` 为零宽空格，不属于普通空白字符规则 |
| `CON` | `windows_filename` | 整名级 Windows 保留名称检查 |

自定义规则包含 `id`、`name`、`enabled` 和 `forbiddenCharacters`。每个禁止项必须恰好是一个合法 Unicode scalar；数组非空、字符去重、规则 ID 唯一。Schema 校验后仍需执行这些语义校验。自定义规则不支持正则、词组、命名模板或替换操作。

### 4.1 配置导入与持久化

读取文本 → 解析 JSON → 按版本严格校验 Schema 与语义 → 必要时迁移 V1 → 预览内置和自定义规则开启数 / 总数 → 使用者确认 → 替换并持久化完整配置。

校验失败或取消不改变当前活动配置。UE 当前配置写入不具备临时文件交换与备份恢复机制，因此不能将该控制流程解释为任意写盘故障下的崩溃安全保证。替换前应按需导出原配置备份，替换成功后重新扫描。

### 4.2 V1 迁移与一致性约束

- V1 必须先通过冻结的 13 键契约；旧开关及 `customRules` 保留，新增六项开关继承旧 `ascii_only` 状态。
- PS 仅在 V2 存储不存在时读取并迁移 V1；已有 V2 不因损坏而回退套用旧配置。
- 两端以共享 Schema 和 fixture 约定配置状态、迁移结果及求值输出；回归比较包含 `ruleIds` 和 `matchedFragments` 的内容与顺序。
- 提醒偏好、扫描结果和资产内容不属于可交换的规则 JSON；没有自动配置同步服务。

## 5. 自动检查事件链与结果生命周期 {#reminders}

![自动检查时序：宿主回调、准入过滤、范围捕获、扫描求值、条件反馈和手动结果隔离](assets/images/namingaudit/reminders_cn.svg)

*五类参与者表示每个宿主内的逻辑职责。PS 与 UE 消息路径为独立分支，不表示跨宿主通信；自动检查结果与手动扫描结果具有不同的更新条件。*

| 事件入口 | 范围与执行方式 | 呈现与更新条件 |
| --- | --- | --- |
| Photoshop 原生导出通知 | 监听 `export` 及已验证命令 ID 的 `invokeCommand`；按文档去重，检查已识别图层或组及其后代 | 仅在范围内发现问题时显示确认提示；“确定”关闭提示，不自动定位 |
| Unreal 资产导入 / 保存委托 | 缓存对应对象，在后续 editor tick 执行扫描 | 自动结果写入 Message Log 并产生非阻塞通知，不主动替换手动结果 |
| Unreal 通知链接访问 | 读取最近一次缓存自动结果 | 手动扫描未运行时可展示缓存；手动扫描进行中只打开面板，保留手动结果 |

PS 导出范围不可用时不扩大为全 PSD 检查；未知导出入口可能不产生提醒。关闭 PS 提醒后，排队或在途结果通过监听生命周期状态失效。导出、导入、保存、提交和构建不受该检查器阻断。

自动提醒属于补充检查，不是完整范围验收。交付前应确认配置、完成目标范围的手动扫描，并依照项目流程验证修改后的资产状态。

## 6. 系统架构与运行边界 {#impact}

![双宿主本地架构：入口、宿主适配与求值、诊断呈现、共享契约、个人持久化及运行约束](assets/images/namingaudit/coverage_cn.svg)

*实线表示宿主内调用，虚线表示契约约束或配置交换。共享 Schema 与 fixture 是开发期一致性依据，不是运行时共享服务。*

| 职责层 | Photoshop | Unreal Editor |
| --- | --- | --- |
| 入口与事件 | `panel-controller.ts`、`export-monitor.ts` | `SNamingAuditPanel`、`NamingAuditModule` |
| 源对象读取与规则求值 | `photoshop-adapter.ts`、`rule-engine.ts` | `NamingAuditScanner.cpp`、`NamingAuditRules.cpp` |
| 诊断与定位 | 结果筛选、分页、规则明细、图层选择 | 来源分组、分页、Content Browser / UMG Designer 定位、Message Log |
| 个人规则持久化 | UXP `localStorage` | `<Project>/Saved/NamingAudit/RuleConfigV2.json` |

**检查边界：**不批量解析关闭的 PSD，不进入智能对象内部文档；不递归进入另一个嵌套 Widget Blueprint 的内部树；不检查图像质量、材质内容或蓝图业务逻辑。

**修改边界：**不生成替换名称、不自动或批量改名、不搬移资产、不修复引用，不提供撤销资产修改或自动回滚机制。名称修改与引用验证由宿主工作流负责。

**规则边界：**当前规则不检查全局大小写、名称长度、首字母或资产类型前缀。Unicode 分类采用约定的固定或保守范围，不替代宿主原生名称校验及项目专属规则。

**执行边界：**检查在本机完成，无 AI 语义推理或网络同步依赖。分批与分页属于运行优化，不构成大型项目无卡顿或固定帧耗时保证。

## 7. 运行环境、交付版本与验证依据 {#delivery}

| 宿主 | 已有交付 | 菜单入口 |
| --- | --- | --- |
| UE 4.27 / Windows Win64 | 插件 v1.3.6，`NamingAudit-UE4.27-Win64.zip` | Window → 命名规范检查 |
| UE 5.7 / Windows Win64 | 插件 v1.3.6，`NamingAudit-UE5.7-Win64.zip` | Tools → 命名规范检查 |
| Photoshop 2025 / 26.x / Windows | 正式插件 v1.3.8，配套 Windows Installer r2 ZIP / CCX | 插件 → PSD 命名规范检查 |

**UE 按项目安装：**关闭编辑器，将对应版本的 `NamingAudit` 文件夹放入项目 `Plugins`，确认 `Plugins/NamingAudit/NamingAudit.uplugin` 路径正确，重新打开项目并启用插件。4.27 与 5.7 二进制包不能混用，模块仅在编辑器运行。

**Photoshop 安装：**使用完整 Windows Installer r2 交付及随包说明。该交付手册采用配套 CMD 入口，不将双击 CCX 视为通用安装条件。安装结果以宿主内实际加载及版本显示为准。

<details class="evidence-notes">
<summary>源码、契约与历史验证记录</summary>
<p>本页依据 <code>uassetRename</code> 仓库实际契约与实现编写。交付基线为 2026-09-09 操作手册所列版本；后续 Photoshop 字形测试包不纳入该正式基线。</p>
<ul>
<li><code>shared/schema/rule-config-v2.schema.json</code>、<code>shared/schema/naming-issue-v2.schema.json</code>：配置和诊断字段定义。</li>
<li><code>shared/config/default-rule-config-v2.json</code>、<code>docs/rule-config-v2.md</code>：19 条规则、启用语义、聚合顺序与迁移条件。</li>
<li><code>docs/user-guide/NamingAudit_详细操作手册.md</code>：宿主入口、扫描范围、定位行为和实机截图说明。</li>
<li><code>docs/code-review-2026-09-09.md</code>、<code>docs/release-status.md</code>：实现边界及交付状态。</li>
<li><code>artifacts/verification/code-audit-20260909/</code>：UE4.27 / UE5.7 各有 19 项通过的历史报告，本次未重新运行插件测试。</li>
</ul>
<p>技术图为机制说明，实机 PNG 保持原始内容；本页不报告未经项目实测的效率、漏检率或性能指标。</p>
</details>
