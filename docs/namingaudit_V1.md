# NamingAudit

Local naming inspection for Photoshop and Unreal Editor: rule contracts, scan processing, and source-object location.

The **NamingAudit** project delivers the **Naming Audit plugins**, implemented as a Photoshop UXP panel and an Unreal Editor plugin. Each host applies character-level, identifier-structure, and platform-name constraints defined by `RuleConfigV2`, aggregates diagnostics per source object, and exposes native location actions. Inspection is read-only; name changes, reference validation, and saving remain part of the user's host workflow.

<div class="scope-grid" aria-label="Scope summary">
  <div><strong>Host-native inspection</strong><span>Photoshop UXP panel and Unreal Editor plugin; no standalone executable</span></div>
  <div><strong>Local evaluation</strong><span>No network transport, shared service, or model inference</span></div>
  <div><strong>Read-only diagnostics</strong><span>No automatic rename, move, reference repair, or blocking gate</span></div>
  <div><strong>Host-owned correction</strong><span>Editing, saving, compilation, and reference validation remain native work</span></div>
</div>

## 1. Inspection Targets and Diagnostic Contract {#overview}

The tool supports UI artists, content creators, and technical artists working with PSD documents and layer trees, UE asset names and package directories, and Widget Blueprint source trees. Host adapters determine name granularity and location context. The rule engine does not evaluate a complete filesystem path as a single object name.

| Input category | Preprocessing and evaluation scope | Diagnostic context |
| --- | --- | --- |
| PSD documents, layers, groups, and artboards | Remove the document's final extension; enumerate layer-tree names per object | Document path, object hierarchy, and layer-location identifier |
| UE assets and package directories | Evaluate the asset name and each directory segment separately; exclude the mount root and structural path separators | Asset path, matched directory sources, and native-engine explanations |
| UMG source widgets | Inspect the current blueprint's source `WidgetTree`; do not enter another nested blueprint's internal tree | Owning blueprint, source-widget name, and hierarchy path |

![Naming inspection model: host preprocessing, three predicate granularities, NamingIssueV2 fields, and the per-object aggregation matrix](assets/images/namingaudit/problem.svg)

*The diagram distinguishes scalar, identifier-structure, and whole-name predicates. Default-rule examples illustrate multiple predicate matches aggregated into one object diagnostic; they are not results from a new test run.*

The shared `NamingIssueV2` contract contains three groups:

- **Object identity:** `host`, `targetType`, `name`, `documentPath`, and `hierarchyPath`.
- **Match evidence:** non-empty, deduplicated `ruleIds` and `matchedFragments`; optional `ruleLabels` capture rule display names from the configuration used during evaluation.
- **Location capability:** `canLocate=true` requires a non-empty string `locatorId`; otherwise the identifier is `null`. The identifier is opaque and host-specific.

UE's internal `MatchedPathSegments`, `EngineReason`, and related metadata provide additional path-source and engine explanations. They are not fields in the current shared JSON Schema. That Schema contains neither `severity` nor `blocking`; V2 diagnostics are presented as warnings.

**Rule and evaluation specifications:**

- **19 built-in rules in 5 semantic groups:** identifier structure (3), language and width (4), combining / whitespace / control (3), punctuation and symbols (6), path and platform constraints (3). Grouping organizes the explanation only; `ruleIds` output order is fixed by the contract and independent of grouping.
- **3 predicate granularities:** Unicode scalar predicates, identifier-structure predicates (consecutive or edge underscores), and whole-name platform predicates (Windows reserved names and trailing characters). All three can match the same name.
- **9 required fields:** `host`, `targetType`, `name`, `documentPath`, `hierarchyPath`, `matchedFragments`, `ruleIds`, `canLocate`, and `locatorId`. `ruleLabels` is an optional display-name snapshot.
- **At most one diagnostic per source object:** when several predicates match, rule IDs, fragments, and labels are consolidated into one record. Empty `ruleIds` produce no issue.

## 2. Host Workbenches and Source-Object Location {#workbench}

<div class="screenshots">
  <figure>
    <div class="figure-heading"><span class="host-label">UNREAL EDITOR</span><span>UE 4.27 · Plugin v1.3.6</span></div>
    <img alt="Real UE4.27 panel: three test assets scanned, two issues found, with details and Locate actions" src="assets/images/namingaudit/namingaudit-unreal-panel.png" />
    <figcaption>Actual scan in an isolated UE4.27 test project: 3 assets and 2 issues. The panel contains scope selection, grouped diagnostics, details, location actions, and pagination.</figcaption>
  </figure>
  <figure>
    <div class="figure-heading"><span class="host-label">PHOTOSHOP</span><span>26.1 · Plugin v1.3.8</span></div>
    <img alt="Real Photoshop 26.1 panel: scan the current PSD, filter issues, locate layers, and configure personal settings" src="assets/images/namingaudit/namingaudit-photoshop-panel.png" />
    <figcaption>Actual Photoshop 26.1 UXP panel with scanning, filtering, pagination, and source selection. The local configuration includes custom rules; the issue count is not a default-rule baseline.</figcaption>
  </figure>
</div>

Diagnostics are organized by source object. When several predicates match one object, rule IDs, fragments, and labels are consolidated into one record. The number of affected objects is distinct from the number of predicate matches.

- **Unreal:** results are grouped by source and expose full paths, directory origins, and widget hierarchies. Asset location synchronizes the Content Browser. UMG location opens the owning blueprint and attempts source-widget selection; if exact selection is unavailable, the blueprint entry and hierarchy path remain available.
- **Photoshop:** filter by name, path, or rule, and locate layers, groups, and artboards. Document-name diagnostics do not expose a layer-location action.
- **Snapshot semantics:** displayed results reflect the names and rules used by the preceding scan. Changes to names, configuration, or object hierarchy require another scan.

## 3. Scan Processing and Result Semantics {#workflow}

![Processing pipeline: manual and automatic entries, scope resolution, enumeration, evaluation, ordered aggregation, native location, and scan-state branches](assets/images/namingaudit/workflow.svg)

*The diagram identifies both processing stages and intermediate data. The plugin performs read-only inspection and location; manual renaming, saving, compilation, and reference validation are outside the scanner's responsibility.*

### 3.1 Core Processing Rules

1. **Resolve the read scope:** PS uses the current document tree or a recognized export selection. UE uses selected assets, directories, the current UMG blueprint, or `/Game`; automatic scans are restricted to the relevant event objects.
2. **Enumerate and preprocess:** ordinary UE assets use Asset Registry metadata. Widget Blueprints are loaded when source-widget inspection is required. Names are traversed as Unicode scalars without splitting UTF-16 surrogate pairs or rewriting names.
3. **Evaluate enabled predicates:** disabled rules contribute neither `ruleIds` nor `matchedFragments`. Character, structure, and whole-name rules can match the same object.
4. **Produce ordered diagnostics:** built-in IDs follow the fixed contract order, followed by custom IDs in configuration order. Scalar fragments are deduplicated in first-occurrence order; whole-name fragments are appended and deduplicated. Empty `ruleIds` produce no issue.
5. **Present and locate:** retain the rule-label snapshot, then expose host-specific filtering, grouping, pagination, and location. Removed objects or changed hierarchies require rescan or location fallback information.

### 3.2 Unreal Scan Entries

| Scope | Preconditions | Panel entry |
| --- | --- | --- |
| Selected asset set | Select assets in the Content Browser | **Current Selection / 当前选择** |
| Selected directories and descendants | Select directories in the directory tree | **Selected Directories / 选择目录** |
| Current Widget Blueprint | Open and activate the target blueprint editor | **Current UMG / 当前 UMG** |
| Assets under the project `/Game` mount | Confirm the active rule configuration and intended scope | **Entire Project / 全项目 /Game** |

Execution sequence: confirm rules → start the scan → inspect completion status → expand diagnostics and locate → edit in UE → compile, save, and validate references as required → rescan the same scope.

> `/Game` does not represent every disk file and does not automatically include `/Engine` or other plugin mount points. Cancellation preserves only the processed subset; it is not a complete-scope result. Batch scheduling does not bound the duration of a single synchronous Widget Blueprint load.

### 3.3 Photoshop Scan Entry

Open the target PSD, confirm personal rules, and execute **Check Current PSD / 检查当前 PSD**. Nested layers, groups, and artboards are included. The document name is evaluated after removing its final extension. After editing and saving in Photoshop, scan again. If a name change affects exported filenames, repeat the native export operation.

## 4. Rule Configuration, Migration and Host Exchange {#rules}

The `RuleConfigV2` root contains `schemaVersion`, `builtInRules`, and `customRules`. Built-in configuration requires all 19 fixed boolean keys, enabled by default. Exports must not omit disabled entries or replace `false` with the default `true`.

![RuleConfigV2 technical model: all 19 rule IDs, configuration fields, validation and replacement control flow, V1 migration, and shared regression constraints](assets/images/namingaudit/rule-exchange.svg)

*Categories organize the explanation; numeric indices denote fixed output order. Configuration import performs a complete replacement, not a merge. The preview concerns rules, not an asset-renaming map.*

| Example name | Main default-rule result | Contract interpretation |
| --- | --- | --- |
| `Btn_Login_01` | No match | Characters and underscore structure pass; type-prefix semantics are not checked |
| `Btn__Login` | `repeated_underscore` | Two or more consecutive underscores; `matchedFragments` contains a single `_` |
| `_Btn_` | `edge_underscore` | An underscore occurs at the beginning or end of the name |
| `登录按钮` | `ascii_only`, `cjk` | Overlapping predicates are aggregated into one object diagnostic |
| `Btn` + `U+200B` + `Login` | `ascii_only`, `invisible_control` | `U+200B` is a zero-width space, not a match for the ordinary whitespace rule |
| `CON` | `windows_filename` | Whole-name Windows reserved-name evaluation |

Custom rules contain `id`, `name`, `enabled`, and `forbiddenCharacters`. Each forbidden item must be one valid Unicode scalar; the character array is non-empty and deduplicated, and rule IDs are unique. These semantic constraints must be validated in addition to the Schema. Custom rules do not support regular expressions, words, naming templates, or replacement operations.

### 4.1 Import and Persistence

Read text → parse JSON → strict version-specific Schema and semantic validation → migrate V1 when required → preview enabled / total counts for built-in and custom rules → explicit user confirmation → replace and persist the complete configuration.

Validation failure or cancellation preserves the active configuration. The current UE writer does not implement a temporary-file swap or backup-recovery mechanism, so this control flow is not a crash-safety guarantee for arbitrary disk failures. Export the previous configuration as needed before replacement, then scan again after successful import.

### 4.2 V1 Migration and Consistency Constraints

- V1 must pass the frozen 13-key contract. Existing switches and `customRules` are preserved; six added switches inherit the old `ascii_only` state.
- PS reads and migrates V1 only when V2 storage is absent. A damaged existing V2 configuration does not cause fallback to the older V1 configuration.
- Shared schemas and fixtures define selection states, migration expectations, and evaluation outputs. Regression comparisons include both the content and order of `ruleIds` and `matchedFragments`.
- Reminder preferences, scan results, and asset contents are excluded from portable rule JSON. There is no automatic configuration-synchronization service.

## 5. Automatic Inspection and Result Lifecycle {#reminders}

![Automatic inspection sequence: host callbacks, admission filters, scope capture, evaluation, conditional feedback, and manual-result isolation](assets/images/namingaudit/reminders.svg)

*The five participants represent logical responsibilities inside each host. PS and UE message paths are independent alternatives, not cross-host communication. Automatic and manual results have different presentation and replacement conditions.*

| Event entry | Scope and execution | Presentation and update condition |
| --- | --- | --- |
| Photoshop native export notification | Listen for `export` and verified `invokeCommand` IDs; deduplicate per document and inspect the recognized layer or group descendants | Show a confirmation only for issues inside that scope; OK dismisses the message without locating a layer |
| Unreal asset import / save delegate | Queue the relevant objects and scan on a subsequent editor tick | Write automatic issues to Message Log and issue a non-blocking notification without replacing manual results |
| Unreal notification-link access | Read the latest cached automatic result | Show the cache when no manual scan is active; otherwise open the panel only and retain manual results |

A missing PS export scope does not escalate to a full-document scan; unrecognized export routes may produce no reminder. Disabling PS reminders invalidates queued or in-flight results through listener lifecycle state. The checker does not block exports, imports, saves, commits, or builds.

Automatic reminders are supplementary checks rather than complete-scope acceptance. Before handoff, confirm the configuration, complete the intended manual scan, and validate modified assets through the project workflow.

## 6. System Architecture and Runtime Boundaries {#impact}

![Dual-host local architecture: event entry, host adapters and evaluation, diagnostic presentation, shared contracts, personal persistence, and runtime constraints](assets/images/namingaudit/coverage.svg)

*Solid arrows denote host-local calls; dashed arrows denote contract constraints or configuration exchange. Shared schemas and fixtures define development-time consistency, not a deployed runtime service.*

| Responsibility | Photoshop | Unreal Editor |
| --- | --- | --- |
| Entry and events | `panel-controller.ts`, `export-monitor.ts` | `SNamingAuditPanel`, `NamingAuditModule` |
| Source reads and rule evaluation | `photoshop-adapter.ts`, `rule-engine.ts` | `NamingAuditScanner.cpp`, `NamingAuditRules.cpp` |
| Diagnostics and location | Filtering, pagination, character details, layer selection | Source grouping, pagination, Content Browser / UMG Designer location, Message Log |
| Personal rule persistence | UXP `localStorage` | `<Project>/Saved/NamingAudit/RuleConfigV2.json` |

**Inspection boundary:** no batch parsing of closed PSDs or traversal into smart-object documents; no recursive inspection of another nested Widget Blueprint's internal tree; no image-quality, material-content, or blueprint business-logic inspection.

**Modification boundary:** no replacement-name generation, automatic or batch renaming, asset relocation, reference repair, asset-edit undo, or automatic rollback. Name changes and reference validation remain host-workflow responsibilities.

**Rule boundary:** no global case, name-length, initial-character, or asset-type prefix checks. Unicode categories use specified fixed or conservative ranges and do not replace native host validation or project-specific conventions.

**Execution boundary:** inspection is local and does not require AI semantic inference or network synchronization. Batching and pagination are runtime optimizations, not guarantees of hitch-free large-project scans or fixed per-frame duration.

## 7. Runtime Requirements, Delivery and Verification {#delivery}

| Host | Available delivery | Menu entry |
| --- | --- | --- |
| UE 4.27 / Windows Win64 | Plugin v1.3.6, `NamingAudit-UE4.27-Win64.zip` | Window → 命名规范检查 |
| UE 5.7 / Windows Win64 | Plugin v1.3.6, `NamingAudit-UE5.7-Win64.zip` | Tools → 命名规范检查 |
| Photoshop 2025 / 26.x / Windows | Released plugin v1.3.8, matching Windows Installer r2 ZIP / CCX | Plugins → PSD 命名规范检查 |

**Unreal project installation:** close the editor, place the matching `NamingAudit` folder in the project's `Plugins` directory, verify `Plugins/NamingAudit/NamingAudit.uplugin`, reopen the project, and enable the plugin. The 4.27 and 5.7 binaries are not interchangeable. The module is Editor-only.

**Photoshop installation:** use the complete Windows Installer r2 delivery and its bundled instructions. That delivery manual uses the matching CMD installer; double-clicking a CCX is not a universal installation condition. Verify actual loading and the displayed version in the host.

<details class="evidence-notes">
<summary>Source code, contracts, and historical verification</summary>
<p>This page is based on the actual contracts and implementations in the <code>uassetRename</code> repository. The delivery baseline follows the 2026-09-09 user guide; later Photoshop glyph test packages are excluded from that released baseline.</p>
<ul>
<li><code>shared/schema/rule-config-v2.schema.json</code> and <code>shared/schema/naming-issue-v2.schema.json</code>: configuration and diagnostic field definitions.</li>
<li><code>shared/config/default-rule-config-v2.json</code> and <code>docs/rule-config-v2.md</code>: 19 rules, enabled-state semantics, aggregation order, and migration conditions.</li>
<li><code>docs/user-guide/NamingAudit_详细操作手册.md</code>: host entries, scan scopes, location behavior, and screenshot provenance.</li>
<li><code>docs/code-review-2026-09-09.md</code> and <code>docs/release-status.md</code>: implementation limits and delivery status.</li>
<li><code>artifacts/verification/code-audit-20260909/</code>: historical UE4.27 and UE5.7 reports with 19 passing cases each. Plugin tests were not rerun for this page.</li>
</ul>
<p>Technical diagrams describe mechanisms; real PNG screenshots retain their original content. No unmeasured productivity, miss-rate, or performance metrics are reported.</p>
</details>
