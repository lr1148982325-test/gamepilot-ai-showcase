# Environment Style Transfer to 3D Asset: From Concept Painting to Deliverable .glb on an Infinite Canvas

Environment concept art and deliverable 3D assets are separated by three gaps that have nothing to do with model quality. A concept painting is **perspectival** — it is composed, atmospheric, and lit for a single camera. A production asset must be **orthographic**, unambiguous, and single-subject. A concept painting shows a **settlement**; a DCC tool imports one **mesh**. A concept painting carries a **style intent**; a mesh carries **geometry facts**. Closing those gaps by hand — restyling the board, repainting turnarounds, modelling from scratch — is where the hours go.

This workflow closes them end to end: two uploaded images (one content board, one style reference) in, two textured `.glb` files out, along an eight-stage graph of 20 nodes.

| Project fact | Current evidence |
| --- | --- |
| Studio collaboration | Yongxing-Spirits — |
| Canvas | Inficanvas, reached through the GamePilot portal; workflow saved as `inficanvas-workflow` v1 |
| Graph size | 20 nodes — 16 Image (2 of them uploads), 2 Text, 2 3D Asset; 2 groups;  |
| Image models | `gpt-image-2` × 5, `gemini-3.1-flash-image` × 9 |
| 3D model | `tripo3d/v3.1-20260211`, `multiview-to-3d`; 60,000 and 40,000 faces; `meshQuality: ultra`, `textureQuality: ultra`, PBR on |

## 1. The production problem: three gaps, not one modelling step

The naive framing is "generate a 3D asset from a concept painting." Three independent failures hide inside that sentence:

1. **Projection.** A perspective board has converging edges and foreshortening. A multiview-to-3D model expects parallel projection. Feed it the raw painting and it reconstructs a building that leans.
2. **Subject scope.** A board depicts a place. A mesh must be one thing. The settlement has to be decomposed, and a single candidate must be isolated before any geometry is inferred.
3. **Style vs. structure.** Restyling a board usually rewrites its contents — a tower becomes a different tower. The restyled board is downstream of every geometry decision, so drift there corrupts everything after it.

The workflow addresses each gap with a dedicated stage rather than asking one generation step to solve all three.

<p align="center">
  <img src="./assets/images/enviro-style/graph-overview.png" alt="Full 20-node canvas graph from two uploads to two glb assets" width="960">
</p>

*The graph runs left to right: content and style uploads, a structured parsing layer, style transfer, kit-bash decomposition, two parallel single-asset extraction paths, orthographic correction, and two 3D generations.*

## 2. Showcase A — Restyling the board without rewriting the building

### Background and problem

The opening move is a style transfer: take a waterfront settlement concept and repaint it in the target art direction. The failure mode is well known — a restyling model that is free to interpret will "improve" the subject. Towers gain floors, bridges change span, the silhouette drifts. Because the restyled board is the input to every later stage, that drift is permanent.

### Iteration and optimization

The workflow separates the problem into two structured parsing nodes and one tightly constrained generation node.

Two **Text nodes** sit between the uploads and the transfer. They hold text, not generations, and consume no compute. Each carries a `textGenerationPrompt` that defines a strict output contract:

- **Text1 (content)** decomposes the board into six fixed dimensions — subject, scene, composition, viewpoint, geometry and line, key detail — and requires a final 60–120 character descriptive paragraph carrying **zero colour words, zero style words, zero medium words**.
- **Text2 (style)** decomposes the style reference into seven dimensions — medium, palette (with explicit hex values such as `#D96B5F`, `#2F6F73`), lighting language, brush and material, mood, signature elements, and a one-line style tag — and requires a 60–100 character paragraph carrying **zero concrete object nouns**.

The two contracts are mirror images: one describes what the scene *is* while forbidding style vocabulary; the other describes how it *looks* while forbidding object vocabulary. That opposition keeps content and style from contaminating each other before they are recombined.

The generation node itself carries a 72-character Chinese prompt, and the whole restyling strategy is in it:

> 保留参考原图的构图、主体身份、相机角度与空间布局；仅应用参考风格图的美术风格、配色、光影与质感。不要改变画面中出现的物体——只改变它们的呈现方式

> *Preserve the source image's composition, subject identity, camera angle and spatial layout; apply only the reference's art style, palette, lighting and material. Do not change the objects present in the frame — change only how they are presented.*

### Final effect

The constraint is clean and reusable: it grants style authority over *presentation* and denies it over *existence*. For a pipeline whose later stages measure geometry, that distinction is the entire point.

<p align="center">
  <img src="./assets/images/enviro-style/style-transfer-pair.png" alt="Content board and style reference beside the restyled output" width="960">
</p>

*Content board and style reference on the left, restyled board on the right. Composition, camera angle and building count are carried over; only palette, lighting and surface treatment change.*

## 3. Showcase B — Decomposing a settlement into extractable single assets

### Background and problem

The restyled board is still a scene. Before any geometry can be inferred, something in it has to be chosen. Doing this by eye and cropping by hand is the traditional route, and it usually means several rounds of guessing which elements will reconstruct cleanly.

### Iteration and optimization

The workflow makes decomposition an explicit generation stage. **Image1** (2K) applies a kit-bash / breakout-sheet prompt that explodes the board into isolated asset elements on a neutral studio background, and requires the layout to be organised into three labelled groups:

- **Core structure** — the main building broken into modular wall segments or shells.
- **Modular props** — smaller functional details: windows, doors, mechanical parts, hard-surface components.
- **Environment / vegetation** — organic elements, ground scatter, rock, background dressing, separated into individual asset nodes.

The prompt also requires each asset to inherit the source's exact textures, PBR properties, roughness and weathering, which is what keeps the breakdown usable as a modelling reference rather than a pure illustration.

Two extraction nodes then pull single subjects out of that sheet, running **in parallel off the same parent**:

- **Image2** extracts an architectural unit. Its prompt is dominated by nine negative constraints — do not combine multiple assets, do not splice parts from different buildings, do not add floors, roofs, platforms, railings or ornament that are absent from the input, do not generate a group of objects.
- **Image4** extracts a non-building structure — bridge, platform, boardwalk, railing — with a parallel set of prohibitions.

Both prompts state the intent in the same words: *this is "extract an existing unit", not redesign it.* Both specify the deliverable format as well: one unit, complete, centred, surrounded by whitespace, three-quarter view, light background, natural contact shadow.

### Final effect

Extracting one architectural unit and one non-building structure gives the next stage two independent candidates, each with silhouette statistics suited to its own reconstruction conditions.

One usage rule matters here: **multi-view sheets intended for 3D input carry no text labels and no scale cube.** The prompts for the sheets that feed 3D generation end explicitly with 生成结果不要有任何文字和3D 立方体 ("no text and no 3D cubes in the result") — annotations interfere with reconstruction.

<p align="center">
  <img src="./assets/images/enviro-style/kitbash-breakout.png" alt="Kit-bash breakout sheet with core structure, modular props and environment groups" width="960">
</p>

*The breakout sheet turns one scene into a catalogue. Grouping by structure / props / environment is what makes the next extraction step a selection rather than a search.*

## 4. Showcase C — Orthographic correction, slicing, and 3D generation

### Background and problem

The extracted unit is still a three-quarter perspective render. Multiview-to-3D expects parallel projection. The correction has to happen before generation, and it must preserve material continuity — a turnaround that changes the brick pattern between views produces a mesh with mismatched texture.

### Iteration and optimization

Two orthographic sheets are generated, one per extraction branch:

- **Image3** (from Image2, the architectural unit) specifies a horizontal grid of three views: front, left side, back.
- **Image5** (from Image4, the structure) specifies a 2×2 grid and lists four views: front, left, back, top.

Both prompts open with the same requirement — the input's oblique perspective **must** be corrected to distortion-free parallel projection suitable for 3D modelling — and both require per-view PBR consistency, identical textures, and preservation of the specific weathering, moss or rust detail visible in the source.

The sheets are then split into individual views. Slicing is a **manual step performed outside the canvas**: each view is cropped and uploaded back as its own node. View roles are not attached to the images themselves — they are assigned on the 3D node, in a `threeDReferenceViews` dictionary that binds each slice to a camera role (`front`, `left`, `back`, `right`, `top`). Producing a multi-view sheet and labelling its views are therefore decoupled operations: a slice can be re-cropped or replaced without touching any prompt.

Both 3D nodes run `tripo3d/v3.1-20260211` in `multiview-to-3d` mode with `meshQuality: ultra`, `textureQuality: ultra`, PBR enabled and part generation disabled.

### Final effect

Two `.glb` files are produced:

| Asset | Input slices | Faces | Output |
| --- | --- | --- | --- |
| Asset3D1 | 3 (9:16, group `3x1`) | 60,000 | `model_1787123072061_s3dia0836.glb` |
| Asset3D2 | 4 (16:9, group `2x2`) | 40,000 | `model_1787123138060_k3ph94pl1.glb` |

Face counts are set per asset rather than inherited from a global default — the architectural unit was given 50% more budget than the bridge structure.

<p align="center">
  <img src="./assets/images/enviro-style/ortho-to-glb.png" alt="Orthographic sheet split into slices and consumed by the 3D node with view roles" width="960">
</p>

*The sheet is produced without view labels, split into individual views, and annotated with camera roles on the 3D node. The graph edge carries the image; a separate field on the 3D node carries its meaning.*

## 5. What it solves — and what it does not

**What it solves.** The three gaps in §1 each get a dedicated stage, and the run reaches a real deliverable. Style is transferred without structural drift. A scene is decomposed into a catalogue, then into single assets. Perspective is corrected to parallel projection before geometry is inferred. The output is a textured PBR `.glb` at a specified face budget — a file that opens in a DCC tool.

Two design choices generalise beyond this run:

- **Content and style are parsed under opposed constraints** before being recombined. The contracts forbid the other side's vocabulary, which is cheaper than filtering it out afterwards.
- **View roles are consumer-side metadata.** Slice images stay interchangeable, and re-labelling a view costs nothing.

**What it does not solve.**

- **The pipeline is not fully automated.** Slicing is a manual crop-and-upload of each view; there is no node that splits a grid.
- **Nothing is validated.** The 3D nodes report `success`. There is no topology check, no watertightness gate, no scale check, no UV check, and no comparison between the mesh and the source silhouette. A technically valid mesh can still be the wrong building — review the `.glb` in a DCC tool before acceptance.
- **Face counts are inputs, not measurements.** 60,000 and 40,000 are requested budgets; verify actual mesh density on import.
- **Single-run evidence.** The results shown come from one concept board. Acceptance rate and artist-hour savings against a manual baseline are not yet measured.

## 6. End-to-end flow at a glance

| Stage | Input | Operation | Output |
| --- | --- | --- | --- |
| 1. Style-aware parsing | Content board + style reference | Two text contracts decompose content (6 dimensions) and style (7 dimensions) under opposed vocabulary rules | Structured content and style descriptions |
| 2. Style transfer | Parsed descriptions + boards | Constrained regeneration: preserve composition, subject identity, camera angle; change only presentation | Restyled board |
| 3. Kit-bash decomposition | Restyled board | Breakout sheet in three labelled groups (structure / props / environment) | Asset catalogue |
| 4. Single-asset extraction | Breakout sheet | Two parallel extractions under strict negative constraints | One architectural unit, one non-building structure |
| 5. Orthographic correction | Extracted units | Perspective → parallel projection with per-view material continuity | 3-view and 4-view orthographic sheets |
| 6. View slicing and role assignment | Orthographic sheets | Manual crop and upload; camera roles bound on the 3D node via `threeDReferenceViews` | Labelled individual views |
| 7. Multiview-to-3D | Labelled views | `tripo3d` multiview-to-3d, ultra mesh/texture quality, PBR on | Two textured `.glb` assets |

## 7. Reusable capability and how to run it

The reusable capability is not any single model. It is the staged decomposition of an under-specified input:

1. Structured content and style parsing under **opposed vocabulary constraints**.
2. Style transfer bounded by an explicit preserve / change split.
3. Scene → kit-bash catalogue → single-asset extraction.
4. Perspective → orthographic correction with per-view material continuity.
5. Consumer-side view-role assignment feeding multiview-to-3D.
6. Per-asset face budget and PBR/texture quality as explicit parameters.

To run it on a new concept board:

1. Upload the content board and the style reference; keep the two parsing contracts and the preserve/change transfer prompt as-is.
2. Run the kit-bash breakout, then pick the two extraction branches that match your subject types; adjust the negative constraints only if your subject is neither architecture nor a structure.
3. Generate the orthographic sheets, crop each view, upload the slices, and bind camera roles on the 3D node.
4. Set the face budget per asset, run multiview-to-3D, and review the `.glb` in a DCC tool before acceptance.

The current evidence justifies running a controlled studio pilot — measured as artist hours from concept board to accepted asset against the manual restyle-and-model baseline. It does not yet demonstrate a cost reduction, because it records a single run with no baseline and no measured output.
