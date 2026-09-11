# Image-to-3D Mesh Generation: A Showcase-Driven Production Pipeline

The Funcom collaboration started from a practical production problem: concept boards are not clean 3D specifications, and a single image-to-3D inference is too unpredictable to hand directly to an artist. Boards may contain people, multiple views, several object instances, floors, or occluded geometry. Even when a generator reconstructs the right object, the mesh may still contain excessive polygons, fragments, holes, non-manifold edges, or incorrect proportions.

The resulting capability is therefore not positioned as “one image in, one final asset out.” It is a guarded, human-in-the-loop pipeline that cleans the input, generates multiple shape hypotheses, selects among them, repairs the chosen mesh, and validates the actual packaged result.

| Project fact | Current evidence |
| --- | --- |
| Studio collaboration | Funcom |
| Primary generation baseline | Hunyuan3D 2.1, with Hunyuan 3.1 and unlabeled multi-view methods evaluated for routing decisions |
| Data basis | 85 raw concept boards curated into 90 model-aligned target images |
| Frozen end-to-end evaluation | 26 unseen cleaned assets; 26/26 completed and 25/26 passed the current post-repair automated QA rules |
| Strongest isolated intervention | On 25 paired assets, splitting multi-object meshes reduced mean normalized Chamfer by 56.6% |
| Current product decision | Proceed with a controlled pilot; artist hours per accepted asset remain the primary business KPI |

## 1. The production problem: every ambiguous input multiplies downstream review

A generator must guess object identity, instance count, hidden surfaces, camera roles, and background boundaries from the pixels it receives. If those decisions are left implicit, the pipeline spends compute producing several versions of the wrong thing and then asks artists to diagnose the failure at the most expensive point.

The raw-data audit made this cost visible:

- 70 of the 90 target objects required cropping, background removal, or both before generation.
- Five multi-subject boards had to be separated into 12 independent targets.
- An early raw run produced 473 saved candidates from 85 boards before selection or repair. Common failures included people or scenery baked into geometry, fused object instances, and hallucinated support planes.
- Incorrect Front/Back labels could be worse than no labels: two real oblique views forced into fixed camera slots produced asymmetric or distorted geometry.

The optimization strategy was therefore to move uncertainty forward: reject weak inputs early, compare geometry before spending on texture, and preserve a human decision point for semantic correctness.

<p align="center">
  <img src="./assets/images/3d-mesh/multi-step-image-to-3d-workflow.png" alt="Multi-step image-to-3D workflow controlling cost and quality risk" width="960">
</p>

*The production workflow rejects weak inputs early, compares geometry before paying for texture, and validates the actual textured delivery.*

<p align="center">
  <img src="./assets/images/3d-mesh/atre-drawer-complete-workflow.png" alt="Atre Drawer traced through source isolation, candidate generation, selection, cleanup, material generation, and validation" width="960">
</p>

*Atre Drawer is a concrete end-to-end example: the trained ranker changed the rule-based choice, face count fell by 94.7%, and the packaged result passed scripted final validation.*

## 2. Showcase A — Atre Chair: tracing one asset through the complete pipeline

### Background and initial problem

The source sheet contains a character and two views of the same chair. Sending the full sheet directly to a generator does not merely create theoretical ambiguity: a real raw-generation run reconstructed the person and both chair instances together as three separate bodies. The input must therefore be isolated before candidate generation.

<table>
  <tr><th>Raw source sheet</th><th>Raw GLB screenshot — 3 bodies</th><th>Isolated production input</th></tr>
  <tr>
    <td><img src="./assets/images/3d-mesh/atre-chair-source-sheet.png" alt="Atre Chair source sheet with a person and two chair views" width="310"></td>
    <td><img src="./assets/images/3d-mesh/atre-chair-direct-raw-generation.png" alt="Unedited screenshot of the raw GLB containing one person and two chair bodies" width="310"></td>
    <td><img src="./assets/images/3d-mesh/atre-chair-isolated-input.png" alt="Isolated single-chair production input" width="310"></td>
  </tr>
</table>

*Unannotated screenshot of the original Hunyuan3D 3.1 raw-run GLB: the unisolated board produced one person plus two chair bodies in the same 3D result. The model geometry and materials are unchanged; only the camera and lighting are used to make the complete GLB visible. Isolation removes those competing subjects before candidate ranking, cleanup, or texture.*

### Iteration and optimization

The cleaned input was used to generate four geometry proposals. The learned selector changed the rule-based choice and selected candidate B; texturing was deferred until after selection.

<table>
  <tr><th>Candidate A</th><th>Candidate B — selected</th><th>Candidate C</th><th>Candidate D</th></tr>
  <tr>
    <td><img src="./assets/images/3d-mesh/atre-chair-candidate-a.png" alt="Atre Chair candidate A" width="235"></td>
    <td><img src="./assets/images/3d-mesh/atre-chair-candidate-b.png" alt="Atre Chair candidate B" width="235"></td>
    <td><img src="./assets/images/3d-mesh/atre-chair-candidate-c.png" alt="Atre Chair candidate C" width="235"></td>
    <td><img src="./assets/images/3d-mesh/atre-chair-candidate-d.png" alt="Atre Chair candidate D" width="235"></td>
  </tr>
</table>

The selected mesh then went through deterministic cleanup and packaging:

1. Reduce approximately 934,000 faces to 5,800 faces.
2. Repair non-manifold and degenerate geometry.
3. Filter small disconnected components.
4. Normalize scale, center, and orientation.
5. Generate material only for the surviving candidate.
6. Validate the packaged mesh and compare it with the reference mesh offline.

The reference preview below is rendered from the current canonical GLB after its two Unreal `UCX_` collision-helper nodes were detached. Those helpers are engine collision data, not visible chair geometry, and are intentionally excluded from the comparison.

<table>
  <tr><th>Selected geometry</th><th>Textured pipeline delivery</th><th>Corrected reference mesh<br>(UCX helpers excluded)</th></tr>
  <tr>
    <td><img src="./assets/images/3d-mesh/atre-chair-selected-geometry.png" alt="Atre Chair selected geometry" width="310"></td>
    <td><img src="./assets/images/3d-mesh/atre-chair-textured-delivery.png" alt="Atre Chair textured delivery" width="310"></td>
    <td><img src="./assets/images/3d-mesh/atre-chair-reference-mesh.png" alt="Corrected Atre Chair reference mesh without Unreal collision helpers" width="310"></td>
  </tr>
</table>

### Final effect

- Normalized Chamfer: **0.0015**.
- Offline symmetry consistency versus the reference: **97.4%**.
- Post-repair automated QA: **passed**.
- Practical value: the artist receives one repaired starting mesh rather than four textured candidates and a triage task.

This is a representative held-out cleaned-evaluation result. It demonstrates the value of the complete workflow, not a guarantee that every concept board will reach the same fidelity.

## 3. Showcase B — Atre OfficeTable: why a candidate selector is necessary

### Background and failure mode

Simple mesh-health rules can reward the wrong object. In this case, a flat support plane was technically clean enough to obtain a high rule score, even though it did not reconstruct the table.

<table>
  <tr><th>Input concept</th><th>Rule-based pick</th><th>Learned pick</th></tr>
  <tr>
    <td><img src="./assets/images/3d-mesh/office-table-input.png" alt="Atre OfficeTable input" width="310"></td>
    <td><img src="./assets/images/3d-mesh/office-table-rule-pick.png" alt="Rule-based flat-mesh selection" width="310"></td>
    <td><img src="./assets/images/3d-mesh/office-table-learned-pick.png" alt="Learned OfficeTable selection" width="310"></td>
  </tr>
</table>

### Optimization key point

An XGBoost regressor ranks candidates using 590 runtime-computable features without access to the target ground-truth mesh:

| Feature group | Count | What it contributes |
| --- | ---: | --- |
| Mesh statistics | 20 | Face and vertex counts, components, bounding-box ratios, area, volume, and distribution statistics |
| Automated validator | 17 | Holes, non-manifold edges, degenerate faces, duplicates, fragments, normals, self-intersection, and compliance signals |
| Symmetry | 26 | Mirror and C2/C3/C4 signatures, plus differences from retrieved neighboring assets |
| Rendered visual semantics | 512 | Mean CLIP embedding over six fixed rendered views |
| Retrieval differences | 15 | Shape, scale, component, and similarity differences from related reference assets |

The regressor predicts a continuous quality loss for each candidate and selects the lowest score. It does not generate or repair geometry.

### Final effect

- Rule pick normalized Chamfer: **0.024248**.
- Learned pick normalized Chamfer: **0.000741**.
- Case-level reduction: **96.9%**.
- Across 64 development assets in asset-level five-fold cross-validation, the learned selector achieved **0.0237** mean selected Chamfer versus **0.0374** for the rule baseline, a **36.7%** lower mean.

The 64-asset result is development cross-validation, not an untouched customer holdout comparison. Feature-group ablations were exploratory: their confidence intervals crossed zero, so they should not be interpreted as causal attribution.

## 4. Showcase C — Hark Shelves: split the generated mesh before scoring it

### Background and failure mode

The source concept shows two dark, low-contrast views of the shelf. To make the object identity reviewable, the two prepared views are separated, lightly exposure-corrected, and shown against white rather than compressed into the original dark concept board. The generator then retained both views as separate bodies in one mesh, so scoring the full mesh measured both the target and the fused artifact. The intended shelf could not compete fairly until each connected object was exposed as its own candidate.

<p align="center">
  <img src="./assets/images/3d-mesh/hark-shelves-raw-board.png" alt="Two prepared Hark Shelves concept views on a white background" width="960">
</p>
<p align="center"><em>Prepared concept views: the dark shelf details are exposure-corrected and separated from the original grey board for a readable identity check.</em></p>

<table>
  <tr><th>Generated source mesh — both bodies retained</th><th>Split and selected object</th></tr>
  <tr>
    <td><img src="./assets/images/3d-mesh/hark-shelves-source-full.png" alt="High-contrast clay render of the Hark Shelves multi-body source mesh" width="470"></td>
    <td><img src="./assets/images/3d-mesh/hark-shelves-split-selected.png" alt="High-contrast clay render of the selected Hark Shelves split object" width="470"></td>
  </tr>
</table>

*The mesh renders use the same camera, clay material, and lighting. This makes the isolated change—two generated bodies versus one selected body—visible without texture or dark-background interference.*

### Iteration and final effect

The experiment held the selected source candidate fixed and changed only whether it was split into objects before selection:

- Hark Shelves normalized Chamfer: **0.03741 → 0.000857**, a **97.7%** reduction.
- Hark Shelves surface IoU: **0.0325 → 0.3749**.
- Across the frozen 25-asset paired evaluation, mean Chamfer changed from **0.0373 to 0.0162** (**−56.6%**); 20 assets improved and five regressed.
- F-score at 5% increased **53.6%**, and surface IoU increased **82.1%**.
- Watertight source candidates increased from **10/25 to 25/25** after splitting and capping, before deterministic repair.

Because five assets regressed, production keeps the original whole-mesh candidate in the pool and falls back to it when split-object confidence is low.

## 5. What repair solves — and what it does not

The frozen 26-asset run completed end to end, but **0/26** assets passed the first pre-repair validation. Repair was not an optional polish stage; every asset triggered at least one action. Across the run, the most frequent triggers were excessive face count, degenerate faces, small components, and non-manifold edges.

After repair, **25/26** assets passed the current automated final-QA rules. However, seam welding showed that only **19/26** were fully watertight; seven retained real openings or non-manifold regions. This exposed a rule gap: watertightness must become an explicit hard gate where the downstream use case requires it.

More importantly, a closed and technically valid mesh can still depict the wrong object. The production acceptance path therefore has two independent gates:

1. **Technical integrity** — topology, boundaries, fragments, normals, self-intersection, complexity, scale, and packaging.
2. **Content correctness** — the delivered geometry represents the intended object and satisfies the studio’s visual bar.

## 6. Evidence summary and interpretation boundaries

| Evidence set | Result | What it supports | What it does not support |
| --- | --- | --- | --- |
| 85-board raw audit | 473 saved candidates; recurring background, multi-instance, and floor failures | Input preprocessing and QC are necessary | A controlled comparison of cleanup models |
| 26-asset frozen cleaned evaluation | 26/26 completed; 25/26 passed current automated post-repair QA | The full pipeline can produce review-ready starting geometry | Customer art acceptance or artist-hour savings |
| 64-asset development cross-validation | Learned selector mean Chamfer 0.0237 vs 0.0374 for rules | Learned ranking is promising and better than the current rule baseline on this development set | Untouched customer-holdout lift or causal feature importance |
| 25-asset paired split test | Mean Chamfer −56.6%; 20/25 improved | Object splitting has a strong isolated geometry benefit | Guaranteed improvement on every asset or a visual-texture benefit |

All reference-mesh geometry metrics use independently centered and normalized meshes whose longest bounding-box side equals one. They measure shape agreement, not real-world physical scale. Automated QA is also not a substitute for artist acceptance.

## 7. Reusable capability and controlled-pilot contract

The reusable capability is the orchestration around generation:

- auditable single-subject image preparation and view-label checks;
- routing between single-view, trusted fixed-view, and unlabeled multi-view generation modes;
- multi-candidate generation before texture spend;
- runtime candidate ranking without target GT;
- object splitting, deterministic mesh repair, normalization, and packaging;
- technical QA plus explicit human review for semantic correctness.

For the next studio pilot, success should be decided by **artist hours to an accepted asset**, supported by edit burden, acceptance rate, automated technical QA, compute cost, and failure category. The current studies justify that pilot; they do not yet prove production cost reduction.
