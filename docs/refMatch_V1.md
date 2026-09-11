# RefMatch: Reference-Driven 2D Asset Region Registration & Stable Crop Workbench

In game 2D art pipelines, the hard part of cropping is never the cut itself — it is **alignment**. The same visual subject often exists in many forms at once: hundreds of skill-animation frames, risk artwork and compliant artwork versions, UI and character key-art variants across resolutions. Getting one business region from a reference asset onto those targets has traditionally meant per-copy, per-frame manual alignment and crop — slow, error-prone, and hard to scale.

RefMatch productizes that step: mark a region of interest (**ROI**) once on a reference image, then automatically register, stably crop, and score quality on another target image or an entire video / frame sequence — fully local, GPU-accelerated. It does not solve the semantic question “what is in the frame”; it solves the geometric registration question “where does this region correspond in another asset, and how do we crop it stably.”

## 1. Application scenarios: many assets of the same content still need one reproducible region correspondence

In production, RefMatch targets recurring crop workloads that share one registration and crop engine, differing mainly in input shape and entry point.

| Typical scenario | What must be done | Common failure modes |
| --- | --- | --- |
| Skill / VFX local crop (Skill Video Cut) | Mark the subject on a key frame; crop the same local content frame-by-frame across a video or image sequence. | Subject or camera motion (translation / scale / rotation) makes a fixed window drift, composition jitter, and output sizes misalign. |
| Risk artwork → compliant artwork correspondence crop | Mark a business region on risk artwork (review / mosaic / watermark / low-res); crop the same region from compliant artwork (approved HD master). | Different canvas, resolution, and margins make eye alignment costly and inconsistent — wrong crops and missed crops. |
| UI / HUD multi-version region alignment | Mark a control region on one UI build; crop the corresponding region on another resolution / regional build / skin. | Layout scale or offset; manual alignment cost grows linearly with page count. |
| Character key art / prop sheet compositional extract | Use a fixed avatar / bust / icon composition as reference; batch-extract standard-size crops from other version sheets of the same character. | Repeated passes produce inconsistent crop baselines and output specs. |

When assets update or are revised, the same work restarts: re-locate, re-align, re-crop, re-check. The bottleneck is not merely “cropping is slow,” but the lack of a reproducible engineering path that reuses the reference region, constrains the crop baseline, and unifies output specs.

## 2. Problem essence: no engineered region registration between the reference ROI and target assets

Traditional pipelines lack a stable, reproducible, scalable registration link between a **reference region** and many target assets of the same content. Operators act as a **manual registration layer**: eye-align per copy or frame, hand-crop, then absorb error through rework.

That step converts “looks the same” into **pixel-level correspondence**. It is the most operator-dense, expertise-heavy, and revision-sensitive part of crop delivery. In animation sequences and multi-version assets, pose and canvas usually differ; one revision can force a full re-align and re-crop batch.

![RefMatch registration gap and manual cost growth](assets/images/refmatch/refmatch-problem-model.svg)

| Core pain | Traditional behavior | How RefMatch responds |
| --- | --- | --- |
| Manual region registration | Per-copy / per-frame eye alignment; harder across canvas and resolution. | Feature matching + RANSAC transform estimation builds geometric correspondence from reference ROI to target. |
| Unstable across frames | Hand crops jitter; subject drifts out of frame; large empty margins. | Tracking + sub-pixel refinement keeps the region updated; output stays stable across frames. |
| Inconsistent output specs | Size, composition, and padding follow personal habit. | Resample onto the reference ROI grid into a locked-size output canvas. |
| No measurable quality | “Looks cropped,” but misalignment or empty crops are hard to catch. | Confidence, inlier ratio, reprojection error, and ZNCC content correlation quantify each result. |
| Limited throughput | Hundreds–thousands of frames / many versions processed one by one. | Async batch jobs + progress feedback + one-click export (sequence ZIP / video / still). |
| Low reuse across revisions | Asset updates force full redo. | Reference ROI and parameters are reusable; re-run after revision without rebuilding correspondence. |

## 3. Product positioning: a reference-ROI workbench for 2D asset registration and crop

![Workbench overview](assets/images/refmatch/cover.png)

> **Mark a region once on a reference image, then automatically align and stably crop it on another image or an entire sequence.**

RefMatch is a local, reference-driven visual registration and crop tool. It keeps the reference image, target asset, ROI, and match parameters in one context. The match pipeline performs feature correspondence, transform estimation, optional sub-pixel refinement, stable crop, and quality scoring, with per-frame tracking and batch export for video / sequences.

For two-image correspondence crops, run a single **Reference Align** or **Quick Match**. For video and sequences, run a batch tracking job and choose among **Reference Matching**, **Recursive Matching**, and **Fixed-Box Crop** — all sharing the same crop and output rules.

| Item | Product contract |
| --- | --- |
| Input | One reference image + one ROI, plus one target image, or one video / frame-sequence directory. |
| Output | Stable crops of the corresponding region on the target (still or per-frame sequence), plus optional compare / overlay / difference views. |
| Unified entry | Asset prep, ROI selection, match run, and results/export collaborate in one local workbench. |
| Engine duties | Feature matching, RANSAC transform estimation, ECC sub-pixel refinement, ZNCC quality arbitration, and stable crop on the reference grid. |
| Runtime principle | The reference ROI pixel grid is the output baseline; ordinary preview / inspect actions do not modify source assets. |
| Scope | One-shot registration for an image pair, or batch per-frame tracking and export for video / sequences. |

Product boundary is the **region registration and crop** step: RefMatch does not do semantic recognition (e.g. “find all enemies”), and does not replace art creation or final human review. It targets correspondence crops where two images / many frames share content and differ mainly in position, scale, or mild perspective.

![Runtime collaboration](assets/images/refmatch/runtime.png)

## 4. Unified workbench experience

The frontend organizes observe → configure → run → accept as a four-step flow, with a resizable right-hand parameter and quality sidebar, so one registration task stays on a single page.

| Area | Primary information and actions |
| --- | --- |
| Step bar | Asset Prep → Select Reference ROI → Run Match → Results & Export; sliding underline shows progress; explicit Previous / Next navigation. |
| Asset prep | Upload reference and target images; in Sequence Tracking, upload a video or enter / pick a local sequence directory or glob and probe it. |
| ROI canvas | Drag a rectangle on the reference image; move, resize, or reset to full image; in Reference Crop mode, reference and target are shown side by side for comparison. |
| Param panel | Matcher, transform model, tracking mode, confidence and RANSAC thresholds, output crop, plus folded advanced settings. |
| Result views | Reference Crop: crop / reference compare / overlay / difference; Sequence Tracking: crop results / match detail / source sequence. |
| Match quality & logs | Quality score ring, inlier ratio, reprojection error, content correlation, device info, and run logs. |

Observe-only actions (zoom, pan, visibility, view switch) are independent of processing: they update display state only, and neither change match inputs nor write back to source assets.

## 5. Core workflow

![RefMatch core workflow and match pipeline](assets/images/refmatch/refmatch-core-workflow.svg)

### 5.1 Three run entries

One engine powers two modes and three entries; they differ by input shape and output scale.

| Entry | Mode | Best for | Backend capability |
| --- | --- | --- | --- |
| Reference Align | Reference Crop | Risk ↔ compliant artwork, cross-version UI two-image crops. | Single image-pair registration; returns crop and compare views. |
| Quick Match Test | Sequence Tracking | Validate ROI and match quality on one frame before a batch. | Single image-pair match; fast parameter check. |
| Batch Sequence Processing | Sequence Tracking | Full skill video / animation sequences with stable per-frame crops. | Async per-frame tracking + progress + batch export. |

### 5.2 Match pipeline

Every run executes the same deterministic pipeline:

1. **Feature correspondence** — Build pixel-level matches between the reference ROI and the target with the selected matcher. Default deep matcher is RoMa (more stable on stylized animation and weak texture); also LoFTR, SIFT, ECC, and optical flow.
2. **Transform estimation** — Robustly estimate geometry from correspondences with RANSAC; models from translation through homography, with optional auto escalation from simplest to richer models.
3. **Sub-pixel refinement** — Optional ECC photometric alignment fine-tunes the feature estimate at sub-pixel level to reduce residual offset.
4. **Stable crop** — Resample the reference ROI pixel grid onto the target via `warp_to_reference_grid`, keeping content correspondence strict and output size locked to avoid black borders and misalignment.
5. **Quality scoring** — Weighted score from confidence, inlier ratio, reprojection error, and spatial coverage; ZNCC content correlation arbitrates candidate transforms and corrects the score.

### 5.3 Transform models and crop options

| Category | Options | Notes |
| --- | --- | --- |
| Transform model | Translation / upright rectangle (default) / upright with independent scale / similarity / affine / homography / auto | Upright keeps the ROI axis-aligned with no rotation DOF — best for UI and animation elements; auto escalates from simplest models. |
| Crop mode | Reference ROI grid (default) / tight match AABB / perspective unwrap | Reference grid resamples to ROI size with strict two-side correspondence; tight takes the AABB; unwrap rectifies the mapped quad. |
| Padding | Black (default) / edge extend / mirror / solid color | Fill strategy for out-of-bounds samples after warp. |
| Output size | Width / height (0 = native reference ROI size) | Both set → exact size; one set → preserve aspect ratio. |

### 5.4 Three tracking modes (Sequence Tracking)

For video / sequences, three tracking modes trade stability vs. speed by motion characteristics.

![RefMatch three tracking modes](assets/images/refmatch/refmatch-tracking-modes.svg)

| Mode | Match against | Best for | Traits |
| --- | --- | --- | --- |
| Reference Matching (default) | Original reference every frame | Skill animation with clear subject / camera motion | Resists cumulative drift; most stable; match cost every frame. |
| Recursive Matching | First frame vs. reference; then each frame vs. previous crop | Long sequences that drift slowly away from the reference | Relay-style tracking; avoids dumping accumulated difference onto one frame. |
| Fixed-Box Crop | Match once on the first frame; reuse the same transform | Locked camera, nearly static subject | Fastest: later frames are decode + resample only. |

## 6. System architecture and responsibility boundaries

RefMatch layers a frontend workbench, backend API, core engine, and runtime support. Constrained data contracts keep uploads, runtime previews, final exports, and job state in separate boundaries.

![RefMatch system architecture](assets/images/refmatch/refmatch-architecture.svg)

- **Frontend workbench (Next.js)** — Asset prep, ROI selection, parameters, and result visualization; talks to the backend via REST and SSE progress only; performs no image compute.
- **Backend API (FastAPI)** — Project-scoped assets and results; image-pair match / reference align, video batch jobs, models, and health/status.
- **Core engine** — Matchers (RoMa / LoFTR / SIFT / ECC / optical flow), geometry (transform estimation and grid crop), alignment (ECC refine and ZNCC arbitration), quality scoring, and trajectory smoothing — the only layer that runs image compute.
- **Runtime support** — Async jobs (daemon thread + SSE + disk persistence), device selection (CUDA / CPU auto-detect), and project storage.
- **Data boundary** — Uploads, previews, exports, and per-frame results live under the project directory; job state is persisted separately and can be restored or marked interrupted after service restart.

## 7. Runtime collaboration

A batch sequence-tracking job is submitted with inputs and parameters; the backend starts an async worker thread that per-frame matches or reuses a transform, stably crops, and writes to disk, streaming progress over SSE. Optional trajectory smoothing re-renders at locked size after all frames finish; then frame results are available for preview and export.

![RefMatch runtime collaboration sequence](assets/images/refmatch/refmatch-runtime-sequence.svg)

## 8. Quality, safety, and runtime boundaries

### 8.1 Quality metrics

| Metric | Meaning |
| --- | --- |
| Quality score | Weighted blend of confidence, inlier ratio, reprojection error, and spatial coverage — overall reliability. |
| Inlier ratio / count | Share and count of geometrically consistent correspondences under RANSAC — match robustness. |
| Reprojection error | Mean residual of inliers under the estimated transform — lower is more precise. |
| Content correlation (ZNCC) | Zero-mean normalized cross-correlation between reference ROI and crop; robust to lighting and repetitive texture; used to arbitrate candidates and correct scores. |

The workbench quality ring gives readable advice: high scores can export directly; medium scores suggest checking the overlay view; low scores prompt ROI and asset review.

### 8.2 Preview isolation from source assets

- Zoom, pan, visibility, and view switching update display state only; they do not change match inputs or modify source assets.
- Result previews and crop exports write to separate locations under the project directory and never overwrite originals.

### 8.3 Device and run status

- Device selection: auto / CUDA / CPU. Auto probes CUDA availability and falls back to CPU on failure.
- Status reports device, GPU model, VRAM use, and compatibility warnings; low VRAM is surfaced explicitly.
- Deep-matcher weights load on first use in-process and are reused for later tasks; jobs run on daemon threads with poll and SSE progress, and can be cancelled at any time.

## 9. Capability scope and requirements

### 9.1 Current capabilities

| Capability | Behavior |
| --- | --- |
| Two-image region registration | Mark ROI on the reference; auto-locate and crop on the target; includes compare / overlay / difference views. |
| Sequence / video per-frame tracking | Match and stably crop each frame of a video or sequence directory; unified size and frame-to-frame stability. |
| Three tracking modes | Reference / Recursive / Fixed-Box — trade stability vs. speed by motion characteristics. |
| Multiple matchers and transforms | Deep matchers (RoMa / LoFTR) and classical methods (SIFT / ECC / optical flow) with multiple geometric models. |
| Quality scoring | Confidence, inlier ratio, reprojection error, and ZNCC content correlation per result. |
| Batch jobs and export | Async jobs + progress; still, sequence ZIP, and video export. |
| Local execution | Assets and compute stay local; GPU acceleration with CUDA / CPU auto-select. |

### 9.2 Environment and dependencies

| Item | Requirement |
| --- | --- |
| Deployment | Local: FastAPI backend + Next.js workbench. |
| Compute | CUDA GPU accelerates deep matchers; CPU fallback without GPU. |
| Model weights | Deep matchers (RoMa / LoFTR / XFeat) weights under the local model directory. |
| Inputs | Common image formats and video; sequences include png / jpg / webp / bmp / tif / tga / exr / ppm, etc. |

### 9.3 Current boundaries

- Region registration for “same content, different position / scale / mild perspective” only — not semantic recognition or object detection;
- One reference and one target asset per task (one target image or one sequence / video);
- Fully different content, large deformation, heavy occlusion, or near-textureless flats may fail or need human review;
- Quality score is assistive; critical assets should still be accepted via overlay / difference views;
- Fixed-Box Crop fits locked camera and nearly static subjects only; use Reference or Recursive Matching when motion or scale change is clear.

## 10. Demo recording

[RefMatch walkthrough (video)](assets/video/refmatch.mp4)
