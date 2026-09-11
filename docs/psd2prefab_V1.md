# PSD2Prefab: Bridging the Game UI Implementation Gap Between Photoshop and Unity

When a game UI enters implementation and integration, both primary artifacts usually already exist: artists have completed the PSD/PSB in Photoshop, while developers have prepared a foundational Unity Prefab containing components, layout constraints, and interactions. The remaining work is an intensive production step—translating the visual design accurately into that existing functional structure.

## 1. The Real-World Scenario: Visual Design and Functional Structure Are Ready, but Cross-Tool Implementation Remains

In production, game UI art and functional development typically proceed in parallel:

- Artists use PSD/PSB groups, layers, text, shapes, effects, clipping relationships, and compositing order to define what the interface should look like.
- Developers use `RectTransform`, `Image`, Text/TMP, `Selectable`, `LayoutGroup`, masks, animation, and event bindings to define how the interface should behave at runtime.
- During UI implementation, these artifacts must converge: each visual element must be mapped to the correct functional node, layers must become Unity-compliant assets, component properties must be populated correctly, and the result must be reviewed against the source design.

This cannot be solved by simply importing a PSD. The design file is organized around visual composition, while the Prefab is organized around runtime responsibilities; names, granularity, and hierarchy rarely align. A single button, for example, may consist of separate background, stroke, icon, and label layers in Photoshop, but correspond to `Button`, `Image`, TMP, and state-control nodes in Unity. The implementer must understand both structures before deciding how to composite, export, import, and populate them.

| Typical scenario | Required work | Common risk |
| --- | --- | --- |
| First implementation of a new screen | Understand the complete PSD/PSB and Prefab hierarchies, then establish the overall mapping between visual elements and functional nodes. | As the screen grows, node discovery, asset slicing, import, and component configuration scale rapidly. |
| Local design revision | Identify the affected region, regenerate the relevant assets, and update the corresponding Prefab nodes. | A local change can force full-page reinterpretation, while the write range and side effects remain difficult to control. |
| Section-based delivery of a complex screen | Implement the background, top bar, content area, button groups, or state branches independently. | Repeated passes can introduce inconsistent naming, trimming, nine-slice, and Importer conventions. |
| Joint visual and functional review | Compare PSD/PSB output and the Unity UI repeatedly for placement, draw order, visibility, and visual fidelity. | Context is fragmented across tools, windows, and directories, making diagnosis and traceability difficult. |

Every design revision can reactivate the same sequence: find the layers again, regenerate assets, reconfigure components, and repeat the cross-tool visual comparison. The issue is therefore not merely slow asset slicing; game UI implementation lacks a continuous engineering pipeline that can reuse context, constrain the write range, and enforce consistent asset rules.

## 2. The Core Problem: No Engineering Mapping Between Visual and Functional Structures

Neither Photoshop nor Unity is missing its own core capability. The gap lies between them: there is no continuous production path designed for implementing game UI art into an existing runtime structure. The operator effectively becomes a manual adapter—interpreting both hierarchies, identifying visual elements in Photoshop, locating functional nodes in Unity, processing assets, configuring components, and validating the result through repeated tool switching.

This cross-tool step translates visual semantics into functional semantics. It is one of the most operation-intensive and experience-dependent parts of UI delivery, and it is repeatedly triggered by design changes. On complex screens, visual layers and functional nodes are rarely one-to-one; even a small revision may require rediscovery, re-export, reconfiguration, and another review cycle.

![PSD2Prefab structural mismatch and manual cost flywheel](assets/images/psd2prefab/psd2prefab-problem-model.svg)

| Core pain point | Manifestation in the conventional workflow | Required engineering capability |
| --- | --- | --- |
| Fragmented cross-tool workflow | Visual review and asset preparation happen in Photoshop, while functional nodes, asset configuration, and runtime verification live in Unity. Context is transferred manually. | Organize design sources, functional structure, execution progress, and review results in one operational workspace. |
| Difficult cross-structure mapping | PSDs are organized by visual composition; Prefabs by component responsibility. Names, granularity, and hierarchy usually differ. | Build verifiable semantic mappings from structure, type, position, and visual evidence. |
| Operation-intensive implementation | Node discovery, asset confirmation, export, trimming, import, component configuration, and visual review require many consecutive manual actions. | Connect asset processing, import, component population, and preview refresh in a repeatable production pipeline. |
| Inconsistent deliverables | Naming, trimming, reuse, nine-slice settings, and Importer properties depend on individual practice. | Standardize assets and component properties through deterministic rules. |
| Low reuse across iterations | A local visual change can trigger full-screen reinterpretation and processing. | Support targeted reruns through explicit context and a constrained write scope. |
| Fragmented review evidence | Design layers, functional nodes, asset settings, and runtime results are distributed across tools and directories. | Present design preview, runtime output, mappings, logs, and recovery state together. |

## 3. Product Positioning: A UI Implementation Workbench for Existing Prefabs

> **Bring the Photoshop-to-Unity UI implementation step into a unified Unity workbench.**

PSD2Prefab is a game UI implementation workbench embedded in the Unity Editor. It brings PSD/PSB visual information, the functional structure of an existing Prefab, and Unity asset conventions into a single task context. Semantic mapping proposes correspondences between design elements and functional nodes; a deterministic pipeline then performs validation, visual baking, asset normalization and import, Prefab population, preview refresh, and recovery from failed Apply operations.

When Photoshop is required for higher-fidelity visual processing, the plugin also orchestrates the invocation and collection of its outputs, reducing manual transfer of context and intermediate artifacts between the two applications. A first full-screen implementation can use Global Auto Match. Large screens, local revisions, and incremental fixes can use Local Auto Match within a selected Scope. Both scales share the same asset-processing and delivery rules.

| Item | Product contract |
| --- | --- |
| Input | One PSD/PSB file and one existing Unity UGUI/TMP Prefab. |
| Output | The populated target Prefab, plus sprites, rasterized text fallbacks, and any required TMP TextFX materials written to `_Res` or a configured `Assets/...` directory. |
| Unified workspace | PSD/PSB parsing, visual evidence, Prefab structure, mappings, production progress, and review results are coordinated in one Unity workbench. |
| AI responsibility | Propose semantic mappings between PSD nodes and Prefab nodes using structural, type, spatial, and visual evidence. |
| Engineering-pipeline responsibility | Validate mappings and execute bake, trim, deduplication, nine-slice detection, import, fill, preview refresh, and failed-Apply recovery. |
| Structural principle | Preserve the existing Prefab as the functional baseline. The tool does not freely delete, reorder, or reconstruct the complete application screen. It may create tool-owned `_AI` `Image`/`RawImage` nodes only under explicit policy, or perform controlled text-component adaptation. |
| Matching scope | Support both Global Auto Match across the complete source and target hierarchies and Local Auto Match within the current Scope. |

The product boundary is the UI implementation step. PSD2Prefab does not replace visual design, functional Prefab construction, interaction logic, animation authoring, or final human review. Auto Match produces mapping proposals; deterministic validation and user confirmation jointly constrain the actual write range.

This positioning differs from general-purpose design-to-code systems. PSD2Prefab does not attempt to regenerate a merely similar-looking screen. It integrates visual implementation into the existing project structure, preserves the existing functional structure, and produces Unity UI assets that remain suitable for continued development, centralized review, and recovery if Apply fails.

## 4. Unified Workbench Experience

The Unity Editor plugin provides a resizable four-column workbench that brings structural inspection, Scope selection, task execution, and result review into one window.

![PSD2Prefab Unity workbench with annotated functional regions](assets/images/psd2prefab/psd2prefab-workbench-annotated.png)

*The workbench presents PSD/PSB and Prefab structures, selected-node previews, Dual Live Preview, Properties, Scope controls, and matching actions in one Unity window. Complete root hierarchies support Global Auto Match, while a selected PSD Group and Prefab Container define a focused Local Auto Match Scope.*

| Area | Primary information and operations |
| --- | --- |
| PSD Structure | PSD/PSB groups, layers, text, shapes, visibility, bounds, and hierarchy. |
| Prefab Structure | Prefab hierarchy plus `RectTransform`, `Graphic`, `Image`, Text/TMP, `Selectable`, and layout information. |
| Live Preview | Prefab rendering above and PSD/PSB rendering below, with Zoom, Pan, Fit, 100%, Frame, and Pick. |
| Details | Properties, optional Control Library, Settings, Log, and the selected node's provenance, quality state, assets, diagnostics, and editable properties. |

The trees, Preview Pick, node inspector popup, and Properties panel share one node identity and selection model. Users can select a node in a tree, double-click to Frame it, or Pick directly in a preview. Repeated clicks at the same location cycle through overlapping nodes according to their actual front-to-back order.

Preview visibility is independent from the business Scope. Eye, Show All, Restore Source, Zoom, Pan, Fit, Frame, and Pick affect observation state only; they neither alter Auto Match input nor mutate the source PSD/PSB or Prefab.

Property changes use a separate, explicitly initiated editing path. Prefab properties are applied through controlled Unity-side services; writing source PSD properties requires Photoshop. This path does not change the read-only contract of ordinary Preview operations or grant the AI write permission.

## 5. Core Workflow

![PSD2Prefab core workflow](assets/images/psd2prefab/psd2prefab-core-workflow.svg)

### 5.1 Global and Local Auto Match

Auto Match supports two processing scales through the same underlying capability. Scope is not a synonym for “local mode”; it defines both the matching context of a task and the range that a subsequent Apply operation may modify.

| Mode | Scope selection | Recommended use |
| --- | --- | --- |
| Global Auto Match | Include the complete PSD/PSB root hierarchy and complete Prefab root hierarchy in Scope. | First full-screen implementation, medium-sized screens, or establishing the complete visual-to-functional mapping. |
| Local Auto Match | Select the corresponding PSD Group and Prefab Container. | Large screens, local redesigns, state branches, incremental fixes, or a narrower rerun after failure. |

Both modes share the same Context, Visual Evidence, LLM Mapping, Normalize/Validate, Bake, Import, Fill, Preview Refresh, and Rollback contracts. For especially complex screens, first inspect the complete structures, then run a medium-sized Scope such as the background, top bar, main content area, or button group. Validate the result before expanding the Scope.

The LLM considers both hierarchies, node paths, node types, positions, dimensions, the active Scope, visual evidence, project-level Mapping Instructions, and optional Control Library information. It returns only a structured Mapping Proposal. The plugin then normalizes and deterministically validates the proposal. If some suggestions are rejected because of missing targets, duplicate conflicts, or incompatible types, the user must confirm the valid subset before any write occurs.

### 5.2 Manual Fill

When the relationship between the visual source and functional target is already known, Manual Fill can bypass the LLM:

- One or more PSD image layers or Groups → one Prefab `Image`, `RawImage`, or `Selectable` Graphic.
- One PSD text layer → one Prefab Text/TMP component.
- Multiple PSD sources → one composited target sprite.

If the required font asset is unavailable and a visual fallback is permitted, the plugin can create or reuse a controlled `_AI` `Image` node—after user confirmation—to display rasterized text. It does not freely generate new application-control structures. Manual Fill reuses the same Validate, Bake, Trim, Deduplicate, Nine-slice, Import, Fill, and Preview Refresh rules as Auto Match, ensuring consistent asset standards across automated and manual paths.

### 5.3 Deterministic Asset Production

After a mapping passes validation, the plugin first completes the visual bake in the Session workspace. Before generating final assets or modifying the target Prefab, it creates a Restore Point and then executes a deterministic Apply Plan:

1. Bake the PSD layers or Groups selected by the Mapping.
2. Snapshot the target Prefab, `.meta` files, asset directory, and relevant Importer state.
3. Trim transparent bounds, reuse duplicate images by content, and detect reusable borders.
4. Write and import sprites into the Prefab-adjacent `_Res` directory or a user-configured `Assets/...` path.
5. Apply image, text, visibility, and layout results to existing Prefab nodes.
6. Refresh the Prefab Preview for side-by-side review against the PSD Preview.

Nine-slice parameters are not chosen by the LLM. Only when a valid, non-zero border is detected and the target is a slice-compatible `UnityEngine.UI.Image` does the plugin write `TextureImporter.spriteBorder` and set the Image type to `Sliced`. `RawImage` and Filled Image components preserve their existing semantics.

## 6. System Architecture and Responsibility Boundaries

PSD2Prefab separates presentation, orchestration, semantic analysis, and deterministic production. These layers cooperate through constrained data contracts, while runtime intermediates, final assets, and the target Prefab remain under distinct ownership boundaries.

![PSD2Prefab system architecture](assets/images/psd2prefab/psd2prefab-architecture.svg)

The key architectural boundaries are:

- **Observation boundary:** Trees, Preview, Properties, and Scope belong to the presentation layer. Ordinary Preview interaction never writes assets.
- **AI permission boundary:** The semantic layer produces only a Mapping Proposal; it has no permission to write a Prefab, sprite, or Importer setting.
- **Source boundary:** PSD-side data comes from Photoshop visual output or the Runtime Reader; Prefab-side data comes from structural and component inspection inside Unity.
- **Automated production write boundary:** Auto Match and Manual Fill can invoke Bake, asset import, Prefab Fill, and Rollback only through deterministic production services after validation succeeds.
- **Explicit property-editing boundary:** Property changes are submitted by the user and executed by deterministic property services. Source PSD write-back is available only through the Photoshop path.
- **Storage boundary:** Runtime intermediates live under `Library/Psd2Prefab/Sessions/<sessionId>/`; final visual assets live under `Assets/...`; the target Prefab accepts controlled modifications while retaining its existing functional structure as the baseline.

## 7. Runtime Collaboration

For an Auto Match task, the Workbench organizes inputs and Scope, while the Semantic Layer produces a Mapping Proposal. The Workbench and deterministic services then normalize the proposal, detect conflicts, and request user confirmation when required. Once validated, the Production Pipeline completes the bake in the Session workspace, creates a Restore Point before writing final assets or changing the target Prefab, and then performs asset import, Prefab Fill, and Preview Refresh. The runtime collaboration is shown below.

![PSD2Prefab runtime collaboration](assets/images/psd2prefab/psd2prefab-runtime-collaboration.svg)

## 8. Safety, Quality, and Runtime Boundaries

### 8.1 Isolation Between Preview and Source Assets

- Prefab Preview uses a read-only clone in a Unity Preview Scene. It does not open a separate Prefab Mode or modify the source Prefab.
- After the initial PSD/PSB visual source is established, Eye, Pick, Zoom, Pan, Fit, Frame, and selection update only in-memory state and rendering output.
- Preview Selection, Preview Visibility, source visibility, and business Scope are four independent states; Eye state never contaminates Mapping, Bake, or Fill input.
- Ordinary Preview interaction never relaunches Photoshop, reparses the PSD, reuploads textures, or writes to disk.

### 8.2 Photoshop and the Runtime Reader

| Mode | Best suited for | Quality boundary |
| --- | --- | --- |
| Photoshop | High-fidelity production baking and processing of complex text effects, Smart Objects, advanced blending, and similar content. | Initial cold processing may be slower. Pixel-identical output is not guaranteed for every arbitrary layer-visibility combination involving complex effects. Ordinary Preview interaction does not invoke Photoshop again after processing completes. |
| Runtime Reader | Environments without Photoshop, fast structure browsing, standard layers, and simple text. It can also serve as a degraded production-bake path. | Complex blending, adjustment layers, Smart Objects, and Photoshop-specific effects are approximated. |

### 8.3 Validation and Recovery

| Stage | Protection |
| --- | --- |
| Mapping | Check missing targets, duplicate conflicts, type compatibility, and result completeness before writes. |
| Before Apply | Snapshot the Prefab, `.meta` files, complete target asset directory, and relevant Importer state. |
| During Apply | Final asset writes and Prefab Fill follow a deterministic plan; free-form LLM property writes are never accepted. |
| Apply Failure | After the Restore Point is established, any asset-write or Prefab-Apply failure triggers automatic recovery. Rollback Restore can also be invoked explicitly. |
| Runtime artifacts | Context, Evidence, Cache, Log, and Restore Point data live under `Library/Psd2Prefab/Sessions/<sessionId>/`. |
| Final assets | Sprites, rasterized text fallbacks, and TMP TextFX materials live in the Prefab-adjacent `_Res` directory or a user-configured `Assets/...` path. |

### 8.4 Model Request and Configuration Boundaries

- Auto Match sends the PSD/Prefab structural context within the current Scope, visual evidence, Mapping Instructions, and optional Control Library information to a user-configured Azure/OpenAI-compatible endpoint. Manual Fill does not issue an LLM request.
- Before sending a request, the plugin validates image count, per-image and aggregate pixel counts, prompt byte size, and total request-body size locally. Requests that exceed a limit are stopped with the measured values reported to the user.
- The API key is stored in Unity `EditorPrefs` for the current Windows user. It is not written to the project's `settings.json`, committed with `Assets`, or included in a delivery package.

## 9. Capability Scope and Operating Requirements

### 9.1 Current Capabilities

| Capability | Current behavior |
| --- | --- |
| Structure and property inspection | Inspect PSD/PSB and Prefab hierarchies, types, bounds, components, and properties in one Unity window. |
| Dual Live Preview | Render the Prefab through a Unity Preview Scene and the PSD through Photoshop or the Runtime layered visual source. |
| Unified selection and inspection | Trees, Preview Pick, Frame, node inspector popup, and Properties share one node identity. |
| Explicit property editing | Inspect and submit supported PSD/Prefab property changes in Properties. Writing source PSD properties requires Photoshop. |
| Global / Local Scope | Cover the complete source and target hierarchies, or constrain reasoning and Apply to a panel, button group, or state region. |
| AI Auto Match | Generate a Mapping Proposal from structural and visual evidence, then pass it through deterministic validation before writing. |
| Manual Fill | Bypass the LLM for known one-to-one or many-to-one relationships while reusing the deterministic production pipeline. |
| Asset production | Bake, transparent-bound trimming, content-based deduplication, nine-slice detection, Unity Sprite import, and production of required rasterized text and TMP TextFX materials. |
| Prefab Fill | Populate images, text, visibility, and layout while preserving the existing functional structure. Under explicit policy, create tool-owned `_AI` `Image`/`RawImage` nodes or perform text-component adaptation. |
| Optional Control Library | Browse reusable project controls and property templates, and stage template properties for the current target node. |
| Failure recovery | Create a Restore Point before Apply, roll back automatically on write failure, and support explicit Rollback. |

### 9.2 Environment and Dependencies

| Item | Requirement |
| --- | --- |
| Runtime environment | Windows and Unity Editor. The current validated baseline is Unity `2021.3.36f1c1`. |
| Python | Python `3.10+` is recommended. Backend dependencies must be installed into the same interpreter configured in the plugin. |
| UI framework | UGUI is supported. Projects whose target Prefabs use TMP must have TextMeshPro installed and initialized. |
| Auto Match | Azure/OpenAI-compatible Chat Completions endpoint. |
| Manual Fill | No LLM endpoint required. |
| Photoshop | Optional. Recommended for higher-fidelity parsing and baking of complex PSD content. |
| Output directory | The Prefab-adjacent `_Res` directory or another valid project-local `Assets/...` path. |

### 9.3 Current Limitations

- One task processes one PSD/PSB and one target Prefab.
- PSD2Prefab does not freely generate a complete Unity screen architecture from scratch.
- A single task does not merge multiple PSD files into one Prefab.
- Auto Match is an assisted implementation capability constrained by validation and user confirmation; it does not replace final visual review.
- Properties exposes only supported property edits and is not a full replacement for Photoshop inside Unity.
- Runtime mode does not guarantee pixel-identical rendering of complex Photoshop effects.
- Large screens require an appropriate Scope based on node count, visual complexity, and model budget.
- `LayoutGroup`, Nested Prefab, and project-specific components remain subject to Unity and project constraints.

## 10. Demo Video

**[Watch the complete PSD2Prefab demo →](assets/video/psd2prefab.mp4)**
