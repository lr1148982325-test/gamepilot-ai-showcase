# 3D Retopology & Decimation: A Tool-Level Exploration on Bad-Topology Game Assets

The Yongxing (Nikke) collaboration surfaced a recurring content-production need: game assets arrive as high-poly meshes with poor topology, and before they can be reused, they must be retopologized, decimated, and given clean, symmetric UVs. This is a classically expensive hand task, so the team explored whether commercial image-to-3D models and open-source remeshing tools could close the gap.

The result is not yet a production capability. This document records what was tried, what each tool objectively produced, and where the gap remains.

| Project fact             | Current evidence                                                                                                    |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| Studio collaboration     | Yongxing (Nikke)                                                                                                    |
| Input asset              | High-poly test piece — 15,830 vertices / 31,488 triangles, zero quads (pure triangle soup)                          |
| Target requirement       | Retopology + decimation, plus left-right symmetric UV                                                               |
| Tools evaluated          | Tripo, Meshy, Hunyuan3D, Quad Remesher (open source)                                                                |
| Best objective reduction | Quad Remesher + Tripo: 15,830 → 1,159 vertices (−92.7%)                                                             |
| Current decision         | Exploration only — Tripo ranks first on art review, but none reached production quality on topology and UV together |

## 1. The production problem: bad topology is the real blocker, not just face count

A high-poly asset that is "hard to reuse" usually fails on three fronts at once: it has too many faces, its edge flow is triangle soup rather than clean quads, and its UV layout cannot be mirrored. Decimation alone removes faces but does not fix topology or UV, and any downstream pipeline that needs clean quads (skinning, subdivision, animation, texture mirroring) will reject a decimated-but-messy mesh.

The test asset made the problem concrete. The input high-poly asset — a "bad-topology" test piece — is byte-identical to the original asset, which means the "bad wiring" is not a separate defect: it is the original asset itself, 31,488 triangles and zero quadrilaterals.

![Input high-poly asset with bad topology — pure triangle soup, 31,488 triangles, zero quads](assets/images/3d-remesh/3d-remesh-input-highpoly.jpg)

*Input high-poly asset rendered with its wireframe overlay. The orange lines show the raw edge flow: irregular, asymmetric, and made entirely of triangles — there are no clean quads to skin or animate.*

## 2. What was measured

Every input and output mesh was parsed directly from its file (glTF binary for `.glb`, FBX binary for `.fbx`) to extract vertex count, polygon count, and triangle count. The triangle-to-polygon ratio is the objective signal for topology type: a ratio of 1.0 means pure triangles, and a ratio of 2.0 means all quads.

| Asset                          | Vertices | Triangles | Topology                      |
| ------------------------------ | -------: | --------: | ----------------------------- |
| Input high-poly (bad topology) |   15,830 |    31,488 | 0 quads — triangle soup       |
| Quad Remesher                  |    7,304 |    14,432 | all quads                     |
| Meshy                          |    2,419 |     2,880 | unverified (triangulated GLB) |
| Tripo low-poly                 |    1,326 |     2,584 | mixed tri + quad              |
| Quad Remesher + Tripo          |    1,159 |     2,262 | mixed tri + quad              |

![Face count by tool, colored by topology type](assets/images/3d-remesh/3d-remesh-facecount.svg)

*Face count after each pipeline, colored by topology type. Aggressive reduction and clean quad topology never coincide in the current tool outputs.*

## 3. Tool-by-tool results

### Tripo (commercial)

A Tripo low-poly run reached 2,584 triangles, but its topology became a mix of triangles and quads.

![Tripo low-poly output — 2,584 triangles, mixed tri + quad topology](assets/images/3d-remesh/3d-remesh-tool-tripo-lowpoly.png)

*Tripo low-poly output. The face count is low, but the edge flow is still asymmetric and the surface is a mix of quads and leftover triangles.*

### Meshy (commercial)

Meshy's output (2,880 triangles) is the most aggressively reduced single-model result. However, the retained artifact is a triangulated GLB, so its quad structure cannot be verified from the file, and no UV-symmetry guarantee is present.

![Meshy output — 2,880 triangles, triangulated GLB, no UV-symmetry guarantee](assets/images/3d-remesh/3d-remesh-tool-meshy.png)

*Meshy output. The mesh is dense and the silhouette is softer than the input; the GLB is fully triangulated, so its underlying quad structure cannot be recovered from the file.*

### Hunyuan3D (open)

Hunyuan3D was evaluated during the exploration but left no retained output artifact in the result folder, so it is recorded here as "evaluated, not measured" rather than given a face-count number.

### Quad Remesher (open source)

Quad Remesher is the one path that cleanly converts the triangle soup into 100% quadrilaterals (14,432 triangles from 7,216 polygons, exactly 2.0 ratio). The weakness is reduction: it removes only ~54% of the input triangle count, leaving 14,432 triangles. Chaining it with Tripo collapses the count to 2,262 triangles — the best objective reduction measured — but the final topology is again mixed.

![Quad Remesher output — 14,432 triangles, 100% quads](assets/images/3d-remesh/3d-remesh-tool-quad-remesher.png)

*Quad Remesher output. Every polygon is a clean quad, but the reduction is mild (~54%) and the edge flow still runs asymmetrically.*

![Quad Remesher + Tripo output — 2,262 triangles, mixed tri + quad](assets/images/3d-remesh/3d-remesh-tool-quad-remesher-tripo.png)

*Quad Remesher + Tripo output. Chaining Tripo after Quad Remesher collapses the count to the lowest measured (2,262 triangles), but reintroduces mixed topology and adds a small rotation offset.*

![Retopology and decimation exploration workflow](assets/images/3d-remesh/3d-remesh-exploration-workflow.svg)

*The four tool paths and the central finding: every path trades decimation against topology, and none enforces UV left-right symmetry.*

## 4. Studio art review: qualitative verdicts

The studio's art team reviewed the outputs and ranked them subjectively. These judgments complement the objective face counts above:

- **Tripo** — ranked first overall, with three areas to improve: the edge flow is not left-right symmetric, the mesh contains broken faces, and too many triangles remain.
- **Meshy** — the wiring is messy and almost entirely triangles; more seriously, the silhouette is not preserved — the eyes and nose have lost their form.
- **Quad Remesher + Tripo** — the silhouette is blurred much like Meshy's, though less severe; the edge flow is even slightly better than Tripo's, but the topology is still asymmetric, the model has a significant placement/rotation offset, and wires pile up in concave regions.

Overall ranking: **Tripo > Quad Remesher + Tripo > Meshy**.

## 5. Why the results are "mediocre" — the trade-offs

Combining the objective measurements with the art review, no tool satisfies every requirement at once:

1. **Aggressive reduction** is achieved by Tripo low-poly, Meshy, and Quad Remesher + Tripo — but only by producing mixed (partially triangular) topology.
2. **Clean quad topology** is achieved by Quad Remesher — but only at weak reduction, and the art review notes the edge flow is still asymmetric and piles up in concave regions.
3. **Silhouette preservation** (keeping the model's overall shape, eyes, and nose) fails on Meshy and degrades on Quad Remesher + Tripo; only Tripo keeps the shape recognizable.
4. **UV left-right symmetry** is achieved by none of the tools; it remains a hand step in every path.

This is the concrete meaning of "mediocre": the tools solve the easy part (removing faces) and leave the hard part (symmetric topology, intact silhouette, and UV symmetry) unresolved.

## 6. Evidence summary and interpretation boundaries

| Evidence set         | Result                                                 | What it supports                                               | What it does not support                                        |
| -------------------- | ------------------------------------------------------ | -------------------------------------------------------------- | --------------------------------------------------------------- |
| Input mesh parse     | 31,488 triangles, 0 quads                              | The input is genuinely triangle soup, not an exaggeration      | Visual quality of the original asset                            |
| Per-tool face counts | 2,262 – 14,432 triangles depending on pipeline         | Objective reduction and topology-type differences across tools | Art-direction quality or UV correctness                         |
| Quad Remesher ratio  | 7,216 polygons → 14,432 triangles (2.0)                | The tool produces a genuine all-quad remesh                    | Whether that quad flow is animation-ready                       |
| UV requirement       | No tool output carries a symmetry guarantee            | UV symmetry is an unresolved gap                               | That a specific tool "failed" UV — it was not measured per-tool |
| Studio art review    | Tripo first; silhouette/edge-flow issues on the others | A qualitative ranking aligned with the objective numbers       | A per-pixel or metric-grounded visual verdict                   |
