# Figma2Unity: A Deterministic Figma-to-Unity UI Pipeline

In a game or app UI pipeline, the moment a design is "final" in Figma is rarely the moment it is "done" in the engine. The art side has finished the pages in Figma; the client side still has to turn those pages into editable Unity UI — hierarchy, layout, text, images, controls and wiring — before gameplay can use them. This translation step is traditionally the most operation-dense, token-gated and revision-prone part of the whole handoff.

Figma2Unity productizes that step into a deterministic pipeline: a token-free Figma Desktop plugin exports the selected pages or frames as a self-contained, versioned `.f2u.zip` packet; Unity validates the packet and materializes editable UGUI/TMP Prefabs or UI Toolkit documents, with explicit fidelity fallback and ownership-aware re-import. The problem it solves is not "what does this design mean" but "how to move a Figma design into Unity reproducibly, keep it editable, and update it safely when the design changes."

## 1. Where it is used: the design model is final, but editable Unity UI still has to be produced

In practice, Figma2Unity covers the recurring hand-off between "design finished" and "Unity UI usable". One pipeline, one contract, two renderers — the differences are where the input comes from and which Unity framework the output targets.

| Typical scenario | What actually has to happen | What tends to go wrong |
| --- | --- | --- |
| First implementation of a new screen | Export the finished Figma page / frames; materialize the full hierarchy, layout, text, images and controls into Unity. | Manual rebuild is slow; the larger the screen, the more node hunting, asset export and component wiring it takes. |
| Partial design revision | Locate the affected roots, re-export, and update only the affected generated objects. | A small change triggers a full rebuild, or overwrites components and wiring the user already owns. |
| Multi-framework delivery | Produce the same design for UGUI first and UI Toolkit later, or hand the same packet to another team. | Per-framework rebuilds diverge over time; assets and naming drift apart across renderers. |
| Joint visual + functional acceptance | Cross-check positions, ordering, text and fidelity between the Unity result and the Figma source. | Context is split across Figma, Unity, exported assets and reports; mismatches are hard to trace. |

When the design changes, all of this fires again: re-export, re-import, re-verify. The problem is not just "export is slow" — it is the lack of a reproducible, versioned, secure engineering path that reuses source identity, constrains write scope and unifies output rules.

## 2. Problem essence: no token-free engineering bridge between the Figma design model and Unity runtime UI

Neither Figma nor Unity lacks capability on its own; what is missing is the bridge between them. Three traditional approaches each fail differently:

- **Manual rebuild** turns the implementer into a human adapter: read the design, rebuild it layer by layer in Unity, then absorb drift through rework. Slow, error-prone, and the output can never be cleanly re-synced.
- **REST-only conversion** depends on API tokens most Figma users cannot get, is limited by what the account can read, and cannot recover plugin-API-exclusive evidence such as original image bytes, full style ranges, variable / component relations and prototype data.
- **Black-box design-to-code** regenerates a merely "similar-looking" page that is usually not editable, hard to maintain, has no stable identity for re-import, and cannot safely preserve existing user work.

Figma2Unity replaces the manual / black-box adapter with a **versioned semantic packet** as the architectural boundary: no Figma-specific objects leak into Unity rendering code, and no Unity serialization details leak into the exporter. Both input paths — the token-free Desktop plugin and the optionally authorized Figma URL — converge on the same validated packet before Unity writes anything.

![Figma2Unity problem model: the manual adapter gap between finished design and the Unity runtime](assets/images/figma2unity/figma2unity-problem-model.svg)

*Each traditional approach fails differently; the root cause is a missing token-free, reproducible, safely re-importable engineering bridge.*

| Core pain point | How it shows up traditionally | How Figma2Unity answers it |
| --- | --- | --- |
| Token gate | Conversion needs REST tokens or manual rebuild. | The token-free Desktop plugin reads only files the signed-in user can see and exports a local packet. |
| Broken cross-tool chain | Design lives in Figma; hierarchy, assets and acceptance live in Unity; context travels by hand. | One versioned packet carries hierarchy, layout, text, images, components, variables, styles and reports. |
| Uneditable output | A generated "similar" page is hard to edit, maintain and extend. | Native-first UGUI/TMP Prefabs and UI Toolkit documents remain ordinary editable Unity UI. |
| Unstable identity | Naming is the only sync key; one rename breaks the chain. | Stable Figma IDs, source metadata and ownership indexes drive re-import. |
| Silent approximation | Unsupported visuals get guessed or dropped. | Explicit `NATIVE` / `SVG` / `RASTER` / `CONTAINER` representation with recorded fallback reasons. |
| Unsafe re-import | Re-import overwrites user work or lands at unpredictable paths. | Ownership-aware sync updates source-owned fields while preserving user-owned components. |

## 3. Product positioning: a deterministic, packet-bounded Figma-to-Unity pipeline

> **Export once in Figma, and materialize editable Unity UI deterministically — token-free, with explicit fidelity fallback and safe re-import.**

Figma2Unity is a team-facing deterministic Figma-to-Unity pipeline producing editable Unity UI, explicit fidelity fallback and safe re-import. The token-free Figma Desktop plugin exports selected pages or frames as a self-contained, versioned `.f2u.zip` packet; Unity validates the packet and generates UGUI/TMP Prefabs or UI Toolkit documents. An explicitly authorized Figma URL is an optional second input path.

A normal hand-off only needs the Desktop plugin to export one packet; in Unity, create a scene Converter, pick the packet, one output folder and exactly one renderer, then import the selected roots. The Desktop ZIP and authorized URL paths share the same validator, import plan, decision flow and renderer boundaries.

| Item | Product contract |
| --- | --- |
| Input | A token-free `.f2u.zip` packet from the Figma Desktop plugin, or an explicitly authorized Figma URL (PAT or OAuth). |
| Output | Editable UGUI/TMP Prefabs (default) or UI Toolkit UXML/USS documents, plus images, vectors, fonts, localization assets, design tokens, source maps, prototype-flow assets and diagnostic reports. |
| Unified entry | Export, packet validation, renderer selection, import planning and review cooperate through one pipeline and one versioned contract. |
| Engine responsibility | Extract hierarchy / layout / text / assets / design-system evidence; validate; assign each node an explicit representation; import assets; synchronize Prefabs; audit geometry and pixels. |
| Operating principle | The validated packet is the architectural boundary; generated objects carry stable source IDs and content hashes so re-import is deterministic. |
| Processing scope | One packet per import; exactly one production renderer (`UGUI` or `UI Toolkit`); Nova is retired. |

The product boundary is the hand-off step itself: Figma2Unity does not replace design authoring, gameplay logic, interaction scripting or final human acceptance. It produces a native, editable, re-importable Unity UI projection — not a pixel-level screenshot of every Figma effect. When Unity cannot express a visual losslessly, the importer records an explicit fallback instead of silently approximating it.

This positioning differs from generic design-to-code tools. Figma2Unity does not aim to generate "similar" pages from prompts or flattened images; it carries the full Figma document model across a versioned contract and projects it onto ordinary Unity components, so the result stays developable, centrally verifiable and safely re-importable.

## 4. The unified workbench experience

Figma2Unity spans two workbenches — one on each side of the packet — organized around the same observe → configure → export / import → verify loop.

### 4.1 Figma Desktop exporter

The plugin runs inside Figma Desktop, reads only the files and nodes the signed-in user can access, and writes a local packet. The production manifest declares no allowed external network domains.

| Area | Key information and actions |
| --- | --- |
| Frame selection | Discover visible top-level frames on the current page; search, select or batch-select roots by stable Figma node ID; output in page order. |
| Export options | Throughput-oriented defaults (PNG-only vectors, no text raster, no root preview), plus on-demand Advanced options: SVG+PNG fallback, text raster evidence, root previews, raster scale and hidden layers. |
| Result summary | Production-level blockers abort the download; quality advisories and fidelity notes are reported separately and never disguised as success. |

### 4.2 Unity Editor workbench

In Unity, a scene Converter owns the import. Its **Settings** workbench organizes pages by task; framework-specific pages appear only when the corresponding renderer is active.

| Area | Key information and actions |
| --- | --- |
| Main Settings | Source, output folder, renderer, naming, review, backup and fidelity defaults. |
| Figma Auth | OAuth / PAT account and tenant settings for the authorized-URL path. |
| Images & Sprites | Raster, SVG, Sprite importer, PPU, compression and atlas policy. |
| Text & Fonts | Font sources and mapping, Google Fonts, text backend and generation policy. |
| Buttons / Shadows / Prefab Creator | UGUI-only component and transition, shadow and reusable-Prefab settings. |
| UI Toolkit | UI Toolkit-only UXML / USS / template / linker / `UIDocument` settings. |
| Localization / Script Generator | Logical-string output and CSV settings; typed semantic-binding generation. |
| Import Events / MCP Server / Debug | Source-read / download / import callbacks; restricted local MCP; reports, validation, cache and backup. |

**Import Review** is not a permanent settings page. It replaces normal navigation only when an active import pauses for layout, sprite or typography decisions, and returns to normal settings once decisions resolve. Plain observation and configuration never write assets; only an explicit import (or explicitly initiated settings) changes generated outputs.

## 5. Core workflow

![Figma2Unity core workflow: two entries converge on one packet; five deterministic stages produce editable Unity UI](assets/images/figma2unity/figma2unity-core-workflow.svg)

*The Desktop plugin and the authorized URL share the same Contract 2.2.0 packet; validation, shared-asset materialization, renderer projection and audit all run deterministically.*

### 5.1 Token-free export (primary path)

1. Open the Figma page containing the frames to deliver; the plugin works on the current page.
2. Search and select the visible top-level roots to export; output follows page order.
3. Keep the throughput defaults; enable Advanced options only when a delivery or visual-acceptance flow needs them.
4. Choose **Export .f2u.zip** and wait for validation and asset rendering to finish.
5. Review the summary — production-level blockers abort the download; hand the raw ZIP to Unity without unzipping or repacking it.

### 5.2 Unity import (ZIP path)

1. Choose **Tools → Figma2Unity → Create Converter** and select the Converter GameObject.
2. Set **Import mode** to **Desktop Plugin ZIP**, then drag in or browse to the `.f2u.zip`.
3. Pick an **Output folder** under `Assets/` and exactly one **UI framework** (`UGUI` or `UI Toolkit`).
4. Choose **Read ZIP project**, inspect the Page/Frame tree and select the frames to import.
5. Choose **Import n selected frame(s)**. If the import pauses, complete the focused **Import Review**, or stop without accepting.

### 5.3 Authorized Figma URL path (optional)

The URL path is optional and never replaces the token-free workflow. It fetches only what the configured account can read, prepares a bounded local `.f2u.zip` under `Library/Figma2Unity/FigmaApi`, then runs the same validator, planner and renderer boundaries as the ZIP path. Compared with a Desktop ZIP, it may lack plugin-API-exclusive evidence.

### 5.4 Deterministic re-import

Keep the existing Converter, output folder, generated assets, source sidecars and `.meta` files. Export a fresh packet and re-import through the same Converter. Stable source IDs let Unity update accepted source-owned fields while preserving registered user-owned components and children. Only successfully imported roots advance their saved snapshots; unselected changes stay pending.

### 5.5 Fidelity policy

Every node gets an explicit `representation`:

1. **NATIVE** — hierarchy and visuals are losslessly expressible by supported Unity components.
2. **SVG** — the vector source is authoritative; a PNG preview may ship alongside.
3. **RASTER** — the rendered node image is authoritative, usually for a leaf or a flattened subtree.
4. **CONTAINER** — hierarchy / layout only, with no graphic of its own.

The exporter records the reason for every fallback; the importer never guesses that a fallback is native-equivalent. Unsupported masks, effects, paint composition, typography or transforms get an explicit SVG / raster / static-preview owner, or a blocking diagnostic.

![Figma2Unity fidelity policy: four explicit representations positioned by editability and pixel fidelity](assets/images/figma2unity/figma2unity-fidelity-policy.svg)

*The same source node is classified into one of four representations by the support matrix; every fallback records a reason, and unknown or future types fail closed.*

## 6. System architecture and responsibility boundaries

Figma2Unity layers extraction, transport, validation and materialization. A constrained data contract keeps the Figma model, the packet, the shared asset store and the generated output in separate boundaries.

![Figma2Unity system architecture: two local processes meet only at the versioned packet](assets/images/figma2unity/figma2unity-architecture.svg)

*The packet is the architectural boundary; no Figma-specific objects leak into Unity rendering code, and no Unity serialization details leak into the exporter.*

- **Figma Desktop plugin (exporter)** — discovers visible roots, extracts hierarchy / layout / transforms / text ranges / design-system evidence / interactions / images / vectors / previews, assigns explicit representations, and writes deterministic packet entries, hashes, diagnostics and quality reports. It never fetches arbitrary files, bypasses permissions, imports into Unity or writes back to Figma.
- **Versioned semantic packet** — the architectural boundary. Contains `manifest.json`, `project.json`, per-root `nodes/*.json`, `images/`, `vectors/`, `previews/` and `reports/`. Importers reject unsupported major versions and tolerate additive minor fields; ZIP extraction is path-safe and bounded.
- **Validation & migration** — validates contract, hashes, paths, sizes and graph before any write; migrates historical `1.x` packets to the current contract.
- **Shared assets / fonts / tokens** — an output-independent store under `Assets/Figma2Unity/Shared/` with ownership indexes keyed by blob/profile and GUID (`SharedAssetIndex`, `SharedFontIndex`). Reuse requires ownership, profile, bytes and GUID to all match.
- **Renderer output** — exactly one production renderer: UGUI/TMP (or Unity UI Text) Prefabs, or UI Toolkit UXML/USS/source maps. The choice is Unity-consumer policy and is never written into the packet.
- **Audit** — after each root is saved, the importer instantiates it in an isolated preview scene and measures geometry against the contract; the visual pipeline captures per-renderer pixel evidence for diffing.

Optional integrations (Unity Vector Graphics, Unity Localization) hold all third-party types in separate adapter assemblies; their absence cannot break base-package compilation.

## 7. Runtime collaboration

A normal import is one coordinated flow across the packet boundary. The Desktop plugin (or the authorized URL adapter) prepares a validated packet; the Unity importer validates and migrates it, builds an import plan, materializes shared assets / fonts / tokens, projects the chosen renderer, and finally runs geometry and pixel audits. Reviewable decisions — layout, sprite reuse and typography — may pause the import for explicit choices instead of silent guesses.

![Figma2Unity runtime collaboration: four phases from export through validate & plan, materialize & project, to audit & deliver](assets/images/figma2unity/figma2unity-runtime-collaboration.svg)

*The optional Import Review pause is drawn dashed: the import continues only after decisions resolve; audit diagnostics and diff evidence land in the reports.*

## 8. Quality, security and operating boundaries

### 8.1 Fidelity policy

- Native-first: whenever the source can be expressed losslessly, Unity components win.
- Explicit fallback: unsupported visuals get a recorded SVG / raster owner or a blocking diagnostic — never a silent approximation.
- Source vs render separation: original PNG/JPEG bytes (`purpose: SOURCE`) are stored under `Assets/Sources/` but must never fill a Prefab Image; only render-fidelity channels may.
- "Native or exact" is a deliberate policy: a successful import promises neither that every node stays editable nor that every native projection is pixel-equal.

### 8.2 Safe import boundary

- Bounded ZIP extraction: 10,000 entries, 256 MiB per entry, 1 GiB total; absolute paths, `..` traversal, oversized entries, duplicate IDs and illegal hashes all fail closed.
- Unsupported contract majors, unsafe archives, ownership drift and unavailable renderers all fail closed.
- Figma packets with blockers are never downloaded; required asset / export / contract / graph failures remain production errors.

### 8.3 Ownership-aware re-import

- Generated objects carry stable source node IDs and content hashes; Figma names are public labels, not sync keys.
- Re-import updates accepted source-owned fields and preserves user components, persistent UnityEvents and explicitly user-owned children.
- Removed source nodes are reported and require an explicit cleanup policy; source metadata is a local re-import link, not two-way Unity-to-Figma sync.

### 8.4 Network and credential boundary

- The plugin runtime declares `allowedDomains: ["none"]`; the primary path sends no design data to external services.
- The optional URL path is quota-passive: network work happens only after an explicit fetch, and it never bypasses Figma permissions.
- Secrets live in the current user's Unity `EditorPrefs` (or CI environment variables) — never in project settings, the packet, reports or Git.

### 8.5 Verification gates

Every change must pass the required gates: Node tests and a production build for the Figma exporter, .NET contract tests, and Python offline packet inspection; when a Unity Editor is available, the EditMode suite plus a screenshot diff against the matching Figma preview. The executed release baseline is Windows + Unity `2021.3.36f1c1` + Built-in Render Pipeline; pixel evidence requires a real graphics device, and `-nographics` output is not valid visual proof.

## 9. Capability scope and requirements

### 9.1 Current capabilities

| Capability | Current behavior |
| --- | --- |
| Token-free export | The Desktop plugin exports selected pages / frames as a self-contained `.f2u.zip`; no REST token, no external network. |
| Authorized URL import | The optional PAT/OAuth path prepares the same packet; account permissions and tenant boundaries are enforced. |
| Two production renderers | Editable UGUI/TMP (or Unity UI Text) Prefabs, or UI Toolkit UXML/USS/source maps; Nova is retired. |
| Deterministic re-import | Stable Figma IDs, source metadata, predictable paths, shared-asset indexes and ownership-aware sync. |
| Explicit fidelity policy | Native-first + SVG/raster fallback + blocking diagnostics; source and render assets stay separate. |
| Rich design evidence | Components, variants, variables, styles, localization, prototype actions, font requirements, accessibility metadata and diagnostics. |
| Reviewable import | Layout, sprite-reuse and typography decisions may pause import for explicit choices. |
| Safe local tooling | Bounded, path-safe ZIP extraction; the optional local MCP is read-only for evidence, gates writes behind explicit confirmation, and never writes back to Figma. |

### 9.2 Environment and dependencies

| Item | Requirement |
| --- | --- |
| Figma | Figma Desktop for the token-free exporter; the plugin loads via a local `manifest.json`. |
| Unity | Unity `2021.3` or newer; executed release baseline `2021.3.36f1c1` (Windows / Built-in). |
| Package dependencies | Newtonsoft JSON `2.0.2`, 2D Sprite `1.0.0`, TextMeshPro `3.0.6` (UGUI/TMP output needs TMP Essential Resources). |
| Optional integrations | Unity Vector Graphics `[2.0.0-preview.24, 2.1.0)`; Unity Localization `[1.0.0, 2.0.0)`. |
| Python | `3.10+` only for the optional local MCP server (scripts ship with the package). |
| Node.js | `22+` only for the source-development build path. |

## 10. Demo Video

**[Watch the complete Figma2Unity demo →](assets/video/figma2unity.mp4)**
