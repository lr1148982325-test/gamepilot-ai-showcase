# PSD2UMG: From Layer Organization and Asset Slicing to Unreal UMG

Once a UI design is complete, a substantial amount of implementation work still remains before it can be used in a project.

| Primary role | Work that remains after PSD handoff |
|---|---|
| UI designer | Organize layers, determine asset-slicing granularity, and handle text, states, and asset reuse |
| UE UI developer | Import assets, build the Widget Tree, and configure layout, styling, and paint order |

This pipeline does not mechanically convert every PSD layer into an `Image` or `CanvasPanel` node. The Agent considers the complete composition, layer structure, and runtime requirements to determine asset granularity, editable text, states, reuse relationships, and the appropriate UMG widget structure. MCP then validates those decisions and converts them into executable deliverables.

## 1. Repetitive Work the Pipeline Reduces

| Traditional workflow | Pipeline workflow |
|---|---|
| Inspect, regroup, and rename layers one by one | The Agent creates an organization plan from the complete composition and layer structure |
| Manually decide what to merge, separate, treat as a state, or reuse | Generate an asset plan based on runtime responsibilities |
| Export and import assets individually, then build the Widget Tree by hand | Generate finalized slices, a UMG layout, and a UE build script |
| Repeat the entire downstream workflow after every change | Reuse formal intermediate outputs to regenerate only the affected downstream results |

> The pipeline produces an initial Widget Blueprint implementation that can be connected to project data, events, animation, and interaction. It does not promise a production-ready interface with no human involvement.

## 2. Two AI Skills in the Pipeline

![Decision responsibilities of the two AI skills, shared MCP support, and formal outputs](assets/images/psd2umg/01-skill-contract.svg)

- `psd-organizer` guides the Agent in analyzing the PSD and deciding layer organization, English naming, slicing granularity, editable text, states, and asset reuse.
- `psd-to-umg` guides the Agent in using the organizer's formal facts to decide region relationships, widgets, containers, slots, sizing, styles, and nesting.

> `psd-to-umg` reads the organizer's formal outputs. It does not reorganize the PSD or slice the assets again.

## 3. `psd-organizer`: Organize PSD Layers and Generate Slices

![The psd-organizer loop for AI decisions, validation, and execution](assets/images/psd2umg/02-organizer-sequence.svg)

The organizer's core responsibility is not exporting every layer individually. It determines which visuals should be merged into one slice, which elements must remain separate, which text must stay editable, and how states and repeated instances should reuse assets. Guided by `psd-organizer`, the Agent makes these resource decisions. MCP supplies layer facts and execution constraints, validates the plan, and freezes an executable slicing contract.

After the contract is frozen, `save_plan` creates a review page for the current revision. A person can approve that plan or submit one batch of changes; feedback rebuilds the plan and opens a new revision for review. Photoshop reorganizes, saves, and renders native PNGs through Windows COM only after the current revision is approved. This is a pre-execution review of the organization and slicing plan, not a replacement for final visual validation in UE.

![The psd-organizer pre-execution review page](assets/images/psd2umg/06-organizer-review.png)

## 4. `psd-to-umg`: Build UMG from the Organized Results

![The psd-to-umg loop for AI region decisions, layout validation, and UE delivery](assets/images/psd2umg/03-umg-sequence.svg)

The UMG stage directly reads the PNGs, text, source positions, states, reuse relationships, and paint order delivered by the organizer. It does not reorganize the PSD or slice the assets again. MCP uses these facts to establish a fidelity base and propose a relationship-first layout. The Agent reviews the visual regions, chooses widgets, containers, nesting, slots, sizing, and styles, and revises only the regions that fail validation.

After the Delivery Gate passes, MCP generates the formal `layout.json`, `build_widget.py`, and runtime audit instructions. Project staff then run the script in UE Editor.

## 5. UE Widgets Currently Supported

![UE widget types currently supported for direct generation](assets/images/psd2umg/04-supported-ue-widgets.svg)

The current generation template provides native creation paths for 19 widget types:

| Category | Widgets |
|---|---|
| Basic display and interaction | `Image`, `TextBlock`, `Button`, `ProgressBar`, `Spacer` |
| Layout containers | `CanvasPanel`, `Overlay`, `HorizontalBox`, `VerticalBox`, `ScrollBox`, `GridPanel`, `UniformGridPanel`, `WrapBox` |
| Collections, state, and adaptation | `ListView`, `TileView`, `WidgetSwitcher`, `SizeBox`, `ScaleBox`, `SafeZone` |

For `ListView` and `TileView`, the pipeline can generate Entry Widget, orientation, size, spacing, and Designer preview configuration. The project must still integrate business data sources, field bindings, and interactions. `CheckBox`, `Slider`, `ComboBox`, `EditableText`, and `TreeView` are not currently included in the native direct-generation list.

Widget Catalog is an optional project-level enhancement. When configured and successfully matched, it can reuse a project's existing encapsulated widgets, such as buttons, text styles, pagination dots, or quantity selectors. If it is not configured or no suitable match exists, the pipeline still generates the base structure with native UMG widgets.

## 6. Case Study: Demo RPG

The following results come from a layered 2560 × 1440 character-status UI PSD, referred to here as Demo RPG.

The source PSD contains 128 source nodes, 37 groups, and 31 text layers. Following the formal plan, the organizer executed 91 PSD reorganization operations and 38 rendering tasks, producing 33 physical PNG files and 67 manifest facts. The number 38 represents production tasks, 33 represents physical files, and 67 also includes text, source instances, and asset-reuse facts: 7 composite slices, 33 independent assets, and 27 text entries.

During the UMG stage, the Agent selected the following structures for different regions based on visual relationships and source facts:

| Region | Actual UMG structure |
|---|---|
| Tabs | `Overlay → HorizontalBox → TextBlock + Spacer` |
| Attributes | `VerticalBox → HorizontalBox` |
| Buffs / Debuffs | `VerticalBox → Overlay → Image / TextBlock` |
| Avatars | `Overlay → HorizontalBox → local Overlay` |
| Action entry | `Button` |
| HP Fill | `Image` |

The formal layout uses eight widget types: `Button`, `CanvasPanel`, `HorizontalBox`, `Image`, `Overlay`, `Spacer`, `TextBlock`, and `VerticalBox`. The build report records that 119 out of 119 Widget nodes were created and saved. The fixed attribute rows use a `VerticalBox` with multiple `HorizontalBox` children rather than being wrapped in a business `ListView`; HP Fill is an `Image` in this case.

![Complete PSD source, real UE Designer view, and standalone render for Demo RPG](assets/images/psd2umg/05-demo-evidence.png)

The region outlined in red in UE Designer is shown at full size below.

## 7. Using the Pipeline in Codex and Other AI Agents

| 1. Prepare | 2. Organize the PSD | 3. Generate UMG |
| :--- | :--- | :--- |
| Enable the `psd-organizer` and `psd-to-umg` skills<br>Configure the `psd-pipeline` MCP<br>Open Photoshop<br />Use `GPT-5.5 / High` | `psd-organizer "D:\...\xxxx.psd"` | `psd-to-umg "D:\...\xxxx.psd"` |

> Run step 3 only after the organizer has completed successfully, and continue to pass the original PSD path. Project staff run the generated `build_widget.py` in UE Editor. 
>
> The current workflow has only been tested with `GPT-5.5 / High`.

## 8. What Project Staff Still Need to Complete

The pipeline handles the organization plan, slice-execution orchestration, UMG structure and layout, the UE build script, and build-result validation. Project staff still need to:

- Run and verify the generated script in the project's UE Editor;
- Integrate business data, events, and field bindings;
- Implement input, navigation, animation, and complex interactions;
- Check behavior across resolutions and apply project-specific rules;
- Complete final visual validation.

The pipeline automates the initial implementation. It does not replace business integration or final visual validation.

## 9. Demo Video

**[Watch the complete demo →](assets/video/psd2umg.mp4)**