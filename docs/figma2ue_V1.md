# Figma2UE: Closing the Implementation Gap Between Figma Designs and Unreal UMG

When a game UI reaches implementation in an Unreal Engine project, the design side is usually finished: frames, auto layout, components, variants, and prototype links are all defined in Figma. The remaining work is a dense production step — translating that visual semantics into real UMG assets: Widget Blueprints, panel hierarchies, anchors and slots, textures, materials, fonts, and Blueprint bindings that a team can keep developing, reviewing, and re-importing.

## 1. The Real-World Scenario: The Design Is Done, but the Engine Side Starts from Zero

In production, UI design and engine integration run in different tools with different organizing principles:

- Designers use Figma frames, auto layout, constraints, components/variants, image fills, and prototype navigation to define what the interface looks like and how screens connect.
- Developers use UMG `CanvasPanel`/`HorizontalBox`/`VerticalBox`/`WrapBox`, anchors, slots, `UImage`/`UTextBlock`/`UButton`, materials, fonts, and Widget Blueprint bindings to define how the interface behaves at runtime.
- During implementation these two models must converge: every frame becomes a widget tree, every fill becomes a texture or material, every text layer needs a real font, and navigation must end up as compiled Blueprint logic.

A design file cannot simply be "imported." Figma organizes by visual composition; UMG organizes by runtime responsibility. A single Figma component may expand into a Widget Blueprint with a switcher, several panels, images, and text blocks; an auto-layout frame must become box slots with padding and size rules; an image fill needs bytes, a texture asset, and correct UV behavior. The implementer must understand both structures before deciding how each node should materialize.

| Typical scenario | Required work | Common risk |
| --- | --- | --- |
| First import of a full UI file | Recreate the complete frame/component hierarchy as widget trees, produce every texture/material/font asset, and wire prototype navigation. | Hundreds of nodes of manual reconstruction; naming and layout conventions drift between screens. |
| Design revision on a shipped screen | Re-translate the changed frames and regenerate the affected assets. | Without stable identity, a re-import overwrites or duplicates assets; hand-edited Blueprint content is lost. |
| Component-library-driven UI | Map Figma Components, Component Sets, Variants, and Instance Swaps to reusable Widget Blueprints. | Remote library components cannot be resolved; instances silently degrade to flat images. |
| Cross-resolution layout | Keep Figma constraints meaningful after import so panels behave under different sizes. | Absolute snapshots bake one resolution; anchors must be rebuilt by hand. |
| Team handoff and review | Compare the generated widget tree, assets, and bindings against the design repeatedly. | Context is fragmented across Figma, file exports, and the Unreal Editor. |

Every design revision re-triggers the same chain: re-read the layers, re-slice the images, re-configure the widgets, and re-verify the result. The bottleneck is not merely slow slicing — the pipeline lacks a continuous engineering path that preserves semantics, constrains asset rules, and supports safe re-import.

## 2. The Core Problem: No Engineering Path from Design Semantics to Runtime Semantics

Neither Figma nor Unreal Engine is missing its own core capability. The gap lies between them: there is no production path designed to carry a Figma document into UMG with its structure, layout rules, components, and interactions intact. The implementer effectively becomes a manual adapter — reading one hierarchy, rebuilding it in the other, exporting assets by hand, and absorbing errors through rework.

![Figma2UE problem model: the manual translation gap](assets/images/figma2ue/figma2ue-problem-model.svg)

| Core pain point | Manifestation in the conventional workflow | Required engineering capability |
| --- | --- | --- |
| Cross-structure translation | Figma is organized by visual composition; UMG by widget responsibility. Granularity and hierarchy rarely align one-to-one. | A typed parser that preserves the official REST document semantics and maps them onto UMG panels, slots, and properties deterministically. |
| Asset semantics get lost | Image fills, gradients, strokes, vector art, and fonts each need different asset treatment. | Per-kind asset builders with explicit identity, fill-mode UV mapping, gradient/border materials, and raster fallback for complex vectors. |
| Layout intent is dropped | Auto layout, constraints, and sizing rules are flattened into one static snapshot. | H/V/Wrap box mapping, HUG/FILL sizing, absolute-positioning exceptions, and constraints-to-anchors translation on real canvas slots. |
| Components cannot round-trip | Library components, variants, and instance swaps have no UMG counterpart by default. | Cross-file reference repair, per-axis variant state with WidgetSwitcher, and instance-swap resolution against stable keys. |
| Re-import is destructive | Re-running an import overwrites hand edits or leaves orphaned assets behind. | Stable node-ID identity plus an ownership manifest that classifies Added/Updated/Unchanged/Orphaned before anything is deleted. |
| Credentials and safety | Tokens, oversized images, and recompressed archives corrupt pipelines or leak secrets. | Session-scoped credentials, container preflight before any build, and byte budgets enforced before pixel decode. |

## 3. Product Positioning: Two First-Class Inputs, One Shared UMG Build Chain

> **Acquire a Figma document through either of two official entries, then run one shared Parser/Builder pipeline that produces real, re-importable UMG assets.**

Figma2UE pairs a Figma Desktop exporter with a source-level Unreal Engine 5.7 editor plugin. The **Token REST** entry and the **Plugin ZIP** entry are both first-class: they differ only in how they obtain the canonical REST-compatible document and asset bytes. After acquisition, both converge on the same `PrepareCanonicalFile` → `FixReferences` → Asset/Widget Builders → Blueprint compile/reload/bind/save chain. There is no second document model, parser, or ZIP-specific build semantics.

| Item | Product contract |
| --- | --- |
| Input A — Token REST | Personal Access Token + File Key, optional node-ID subset (`Ids`) and Library File Keys downloaded automatically; image URLs fetched in configurable batches with `NodeImageScale`. |
| Input B — Plugin ZIP | One main archive plus zero or more manually picked Library archives, each produced per file by the same Figma Desktop exporter. No token; no Figma network access during import. |
| Canonical contract | Both entries produce the official `JSON_REST_V1` document shape plus asset bytes; archive v1 records the real `documentKey`, scope (`FILE` / `NODE_IDS`), and raster scale. |
| Output | Widget Blueprints, textures, materials, and font references under `ContentRootFolder` (`Components/`, `Menu/`, `Textures/`, `InstanceTextures/`, `Material/`), ready for normal UMG use. |
| Shared build options | One `URequestParams` model drives both entries: prototype flow, frame-to-button, missing-image policy, widget overrides, Google Fonts, content root, and save-at-end. |
| Structural principle | Acquisition is the only place the two entries may differ. Everything after the canonical document — reference repair, builders, compilation, binding, saving — is shared. |
| Re-import | Same entry, same path: stable node-ID identity updates generated assets, applies Figma-side deletions/reorders, preserves user-authored Blueprint content, and reports orphans. |

The product boundary is the design-to-UMG implementation step. Figma2UE does not author designs, does not invent interaction logic beyond what the prototype data expresses, and does not replace final human review of the generated widgets. The importer runs in the editor only; packaged games consume the generated assets without it.

## 4. The Unified Importer: One Entry, Two Symmetric Paths

A single Content Browser entry — **Add New → Import Figma...** — opens one branded panel. A segmented tab bar switches between the REST API and ZIP Package sub-pages in place; the two sub-pages share the same live status bar, primary action, and validation behavior.

![Figma2UE unified importer panel anatomy](assets/images/figma2ue/figma2ue-importer-panel.svg)

*The panel shows the running plugin version, locks the tab bar while either import is in flight, disables the action until inputs are valid, and keeps the terminal message visible after success, failure, or cancellation.*

| Area | Information and operations |
| --- | --- |
| Brand header | Plugin title with the real version read from the `.uplugin` descriptor, a one-line tagline, and the `FIGMA → UMG` badge over an accent divider. |
| Segmented tabs | `SSegmentedControl` switches REST API / ZIP Package sub-pages hosted in an `SWidgetSwitcher`; tabs lock while either page is importing. |
| REST sub-page | The full 14-field `URequestParams` details view, with **Get Token**, **Find File Key**, and **Get API Key** buttons that open the official Figma/Google documentation in the system browser. |
| ZIP sub-page | In-page **Browse...** for exactly one main archive, **Choose Libraries...** for optional library archives, and the 8 shared build fields; the 6 REST-only acquisition fields are hidden. |
| Status bar | A four-state dot (idle / working / success / error) with a persistent message line. |
| Action row | A primary button that shows a busy throbber and `Importing…` while running, and stays disabled until inputs validate. |

Preflight validation runs before any request is issued: a missing token or file key on REST, an unselected or deleted main archive, or a missing library archive each produce an immediate modal error with actionable guidance instead of a doomed import. Terminal states are surfaced three ways at once — status bar, editor notification (with a completion icon on success), and the `Figma2UE` output log.

## 5. Core Workflow

![Figma2UE core workflow: two entries, one shared build chain](assets/images/figma2ue/figma2ue-core-workflow.svg)

### 5.1 Two First-Class Inputs

**Token REST** keeps the reference workflow: token + file key fetch the full file or an `Ids` subset; library file keys are downloaded automatically; rendered-image URLs are requested in configurable batches (`MaxURLImageRequest`, default 20) at the chosen `NodeImageScale`. HTTP 408/429/502/503/504 responses go through UE's bounded retry manager with native `Retry-After` support; an oversized rendered-image batch that times out or is rejected is bisected down to single IDs for that recovery set only, and the user's configured batch size is restored afterwards.

**Plugin ZIP** moves acquisition into Figma Desktop. The exporter loads each page (`loadAsync()`) and calls the official `page.exportAsync({ format: 'JSON_REST_V1' })` — it does not maintain a hand-written field-level serializer. Two scopes are offered: `Entire file` exports all pages; `Current selection` records the raw selection as `NODE_IDS`, keeps every canvas shell plus the ancestor branches of the selection, and closes over local Component/ComponentSet definitions and actual interaction/transition targets — a canvas `prototypeStartNodeID` alone never pulls an unrelated screen into the archive. The exporter reads the real `figma.fileKey` (private plugin API) and writes it as the archive `documentKey`, collects image-fill bytes by `imageRef`, renders complex vectors and unresolved instances as PNG node rasters at the chosen scale, and fails explicitly when a required asset is unreadable, not decodable PNG/JPEG, or over the pixel budget. The UI iframe assembles `manifest.json + assets/*` into a deterministic STORE ZIP (fflate, level 0) with `networkAccess: none`.

Remote libraries use the same exporter: open each library source file, export one ZIP per file, then pick them manually in the import options. The Figma Plugin API cannot read another file's full document without a token, so per-file export and manual selection are the product flow, not a shortcut.

### 5.2 The Shared Deterministic Pipeline

Both entries converge before parsing. The pipeline is a serial state machine on `UFigmaImporter`:

1. **PrepareCanonicalFile** — each document (REST main, REST libraries, ZIP main, ZIP libraries) goes through the same `DeserializeReflectionFields → PostSerialize → SetImporter`; ZIP runs the whole batch through container and identity preflight first, so any failure happens before a single builder starts.
2. **FixReferences** — local and remote Component/ComponentSet references are repaired per document namespace (`FileKey` on REST, `documentKey` on ZIP); when prototype flow is enabled, navigation destinations are prepared for separate Widget Blueprints.
3. **Asset builders** — textures (`imageRef` originals or `node-raster` fallbacks), fill/gradient/border materials, image-paint materials for FIT/TILE/axis-aligned STRETCH, fonts, and Widget Blueprint shells; every asset request is keyed by `(documentKey, kind, sourceId)`.
4. **Widget builders** — Canvas/HorizontalBox/VerticalBox/WrapBox panels, SizeBox, Image, TextBlock, Button, Border, and WidgetSwitcher assemble the UMG tree; Figma constraints become UMG anchors on real canvas slots, `HUG`/`FILL`/`layoutGrow` map to Slate size rules, and absolutely-positioned children exit the auto-layout flow.
5. **Compile, bind, save** — two compile/reload passes, then binding and property patches, then `SaveAllAtEnd`; the ownership manifest is finalized only after a fully successful save.

Layout and paint follow explicit source rules rather than heuristics: `absoluteBoundingBox` drives layout while `absoluteRenderBounds` expresses paint overflow through a paint-only render transform; simple FILL image paints become a texture with center-crop UVs; complex or rotated paints get an explicit unsupported diagnostic instead of silent degradation; newer node types (`TEXT_PATH`, `TRANSFORM_GROUP`) reuse the vector raster fallback; `EMOJI` and `VIDEO` paints log a warning and are skipped.

### 5.3 Stable Re-import and Ownership

Re-import is a build step that modifies project content, and it is engineered as one:

- Package identity is anchored to the real `documentKey`, manifest name, Figma node IDs, and `ContentRootFolder` — renaming the ZIP does not rewrite identity.
- The importer writes an ownership manifest (`Saved/Figma2UE/Ownership`) plus matching package metadata, then classifies the previous run as Added / Updated / Unchanged / Orphaned.
- Deletion is opt-in and report-only by default; even when enabled, orphaned assets are deleted only after build, both compiles, reload, binding, and save all succeed, and only when the current package metadata double-matches the recorded ownership.
- Automation verifies the contract: a repeated import keeps a user-authored Blueprint variable alive, applies Figma-side child deletions and reorders, and a separate cold-start editor process reloads all generated assets plus the user Blueprint from disk.

## 6. System Architecture and Responsibility Boundaries

Figma2UE spans two desktop applications that never run at the same time in each other's process: the Figma Desktop exporter (main sandbox + iframe UI) and the UE 5.7 editor plugin (panel, importer state machine, parser, builders). The archive-v1 ZIP is the offline handoff; the Figma cloud is touched only by the REST entry.

![Figma2UE system architecture and responsibility boundaries](assets/images/figma2ue/figma2ue-architecture.svg)

The key architectural boundaries are:

- **Acquisition boundary:** the two entries may differ only in how canonical JSON and asset bytes are obtained. The REST entry talks to `api.figma.com`; the ZIP path performs zero Figma network requests during import.
- **Sandbox boundary:** the exporter's `code.js` runs in the Figma main sandbox and only reads the open document; the iframe assembles the ZIP with `networkAccess: ["none"]` and embeds the locked fflate build at bundle time.
- **Preflight boundary:** the UE adapter validates the central directory, rejects non-STORE/ZIP64/encrypted/multi-disk/data-descriptor archives, and enforces aggregate budgets and identity uniqueness before any parsing or building begins.
- **Thread boundary:** background threads handle only bounded bytes and plain JSON; reflection, `PostSerialize`, node `NewObject`, and reference repair run on the game thread.
- **Pipeline boundary:** one parser, one set of asset/widget builders, one compile/bind/save chain. There is no ZIP-specific post-processing and no second document model.
- **Storage boundary:** canonical ZIPs are the handoff; runtime ownership state lives under `Saved/Figma2UE/Ownership`; generated assets live under the configured `ContentRootFolder` as ordinary project content.

## 7. Runtime Collaboration

One import runs as a serial state machine with four phases. The panel submits parameters; the importer acquires the canonical payload (REST batches with retry, or ZIP bytes after batch preflight), prepares each document, repairs references, builds assets and widgets, then compiles, binds, and saves. A cooperative cancellation channel is polled at every safe boundary, and exactly one terminal state — Success, Error, or Cancelled — closes the run.

![Figma2UE import runtime collaboration](assets/images/figma2ue/figma2ue-runtime-sequence.svg)

Cancellation is deliberately non-destructive: the current retry/HTTP, image, or font request is asked to stop, later phases never start, but already-created in-memory assets are not torn down. Blueprint compile and save are single UE calls that cannot be interrupted from inside; a late cancel takes effect at the next safe boundary and is reported honestly in the log.

## 8. Safety, Quality, and Runtime Boundaries

### 8.1 ZIP Container Preflight and Budgets

| Stage | Protection |
| --- | --- |
| Container | Central-directory and local-header preflight before any member is read; only deterministic STORE ZIP32 from the matching exporter is accepted. |
| Batch budgets | Up to 64 documents per import; 512 MiB total ZIP bytes, 16 MiB manifests, 4096 assets, 64 MiB per asset, 512 MiB asset payload. |
| Image safety | PNG/JPEG only, extension must match decoded content; each side ≤ 16384 px and ≤ 64M total pixels, checked before full pixel decode on both the exporter and the UE side. |
| Identity | Duplicate `documentKey`, duplicate local Component/ComponentSet stable keys, and same-`sourceId` cross-kind ambiguity all fail the whole batch; assets are isolated per `(documentKey, kind, sourceId)`. |
| Missing bytes | Assets omitted by the exporter are adjudicated by the shared `ProgressOnFailToDownloadImage` policy; illegal bytes that do arrive are a hard failure. |

### 8.2 Credentials and Network

- The Figma token and the Google Fonts API key are session-scoped password fields; they are never written to project settings, the ZIP, or logs.
- The help buttons only open the official Figma token page, file-key documentation, and Google Fonts key section in the system browser; nothing reads the clipboard or browser state.
- The ZIP path never calls Figma REST. Google Fonts is contacted on either path only when downloading is enabled and a non-empty session key exists; otherwise text resolves against fonts already present in the project/engine via a deterministic family/style/weight mapping with explicit unresolved diagnostics.
- The exporter requires `enablePrivatePluginApi` to read the real `figma.fileKey`, so it ships as a Development or organization Private plugin, not a public Community plugin.

### 8.3 Failure and Cancellation Semantics

- Terminal state is emitted exactly once; late HTTP completions after a cancel cannot advance the pipeline.
- Compile/save failures propagate as failures — a broken build never reports success.
- Cancel does not roll back created assets; the log states precisely where the run stopped, and the ownership report keeps the next run honest.

### 8.4 Verification Gates

Every change must pass the four mandated gates: the Figma exporter's Node test suite and production build, deterministic smoke-ZIP fixture generation, and the UE 5.7 harness running the editor smoke suite plus a separate cold-start persistence process. At the current `v0.8.0` baseline this is 39/39 Node tests, 16 generated ZIP fixtures, 31/31 editor smoke tests (0 warnings, 0 failures), and 1/1 persistence. A dedicated parity test imports the same canonical fixtures through a simulated REST seam and through real STORE ZIP bytes into isolated content roots, then compares normalized semantic snapshots — asset sets, widget trees, slots, brushes, bindings, function/event graphs, and texture fingerprints — which must be identical.

## 9. Capability Scope and Operating Requirements

### 9.1 Current Capabilities

| Capability | Current behavior |
| --- | --- |
| Dual ingress | Token REST (full file or `Ids` subset, automatic library downloads) and Plugin ZIP (1 main + N manually picked library archives), converging on one pipeline. |
| Layout | Canvas/absolute positioning, Horizontal/Vertical/Wrap auto layout, padding, spacing, alignment, `FIXED`/`HUG`/`FILL`, absolute-positioned children, GRID degradation to resolved-geometry canvas, and constraints → UMG anchors. |
| Visuals | Solid fills, image fills with FILL center-crop UVs, FIT/TILE/axis-aligned STRETCH via a shared UI material, gradients, strokes, corner radius, and PNG raster fallback for vectors and complex nodes. |
| Components | Component, Instance, Component Set, single-axis Variant with WidgetSwitcher, multi-axis per-axis stable state with deterministic fallback, and `TEXT`/`BOOLEAN`/`INSTANCE_SWAP` properties. |
| Prototype | Verified same-file `NAVIGATE` plus `OVERLAY`/`SWAP`/`CLOSE` wiring and the frame-to-button rule; `BACK`/`SCROLL_TO`/`CHANGE_TO` keep structured data with precise diagnostics. |
| Text & fonts | Real UMG text with local family/style/weight font mapping; optional Google Fonts download on both entries. |
| Naming | Designer hierarchy shows original Figma layer names; internal `--nodeId` suffixes keep identity stable for duplicates, references, and re-import. |
| Re-import | Stable identity update, Figma deletion/reorder application, user content preservation, and Added/Updated/Unchanged/Orphaned reporting with opt-in cleanup. |
| Operations | Serial acquisition with bounded retry and batch recovery, cooperative cancellation, preflight validation, and terminal notifications. |

### 9.2 Environment and Dependencies

| Item | Requirement |
| --- | --- |
| Figma | Figma Desktop; the exporter runs as a Development plugin or organization Private plugin. |
| Node.js | `22+` for the exporter's test suite and the `dist/` production build. |
| Unreal Engine | `5.7`; project-local source plugin compiled with a matching C++ toolchain. |
| Operating system | Windows/Win64 is the validated and descriptor-allow-listed target; macOS/Linux are not verified. |
| Figma network | Only for the REST entry; the ZIP entry is fully offline toward Figma. Google Fonts is optional on both. |
| Runtime | The importer is editor-only; packaged games use the generated assets directly. |

## 10. Demo Video

**[Watch the complete Figma2UE demo →](assets/video/figma2ue.mp4)**
