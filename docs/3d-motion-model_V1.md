# Studio-Specific 3D Motion Generation: The GST Armed-Aim Showcase

Generic text-to-motion models can produce plausible movement, but a game studio needs something narrower and harder: motions must preserve a character’s skeleton contract, match a specific armed stance and gesture sequence, use the requested clip length, keep planted feet stable, and return as FBX or Unreal animation assets that can be reviewed and reused.

The GST collaboration adapted Kimodo to 16 standing rifle/AIM actions. Three fine-tuning rounds moved the project from a working conversion chain to semantically aligned motions and then to explicitly optimized foot stability.

| Project fact | Current evidence |
| --- | --- |
| Studio collaboration | GST |
| Base motion model | Kimodo-SOMA-RP with the SOMA77 intermediate skeleton |
| Specialized dataset | 16 standing rifle/AIM gestures |
| Training iterations | 0714 baseline chain → 0716 semantic and duration alignment → 0720 foot-stability optimization |
| Final comparison contract | All 16 final motions generated with the corresponding GT clip duration |
| Representative physical result | Contact-foot horizontal drift proxy reduced by 50–74% on four reported actions |
| Deliverable path | Target-character animation → SOMA77 training data → fine-tuned generation → target-character FBX/Unreal animation |

## 1. The practical gap: model output is not yet a studio animation

There were four independent production problems to solve:

1. **Skeleton mismatch.** Existing AdamAll or target-character animations could not be used directly by a SOMA77-based model.
2. **Weak motion semantics.** Short labels such as “stop signal” did not specify which arm moves, what the rifle does, or how the character returns to the ready pose.
3. **Invalid comparisons.** A generated clip with a different duration from its reference could look better or worse simply because the timing was different.
4. **Foot skating.** Improving the upper-body gesture could still make a nominally planted foot drift across the ground.

The solution connects retargeting, verified format conversion, fine-tuning, controlled generation, and engine-side review rather than treating the prompt as the whole product.

<p align="center">
  <img src="./assets/images/3d-motion/motion-production-workflow.png" alt="Four-phase 3D motion production workflow" width="960">
</p>

The character-integration phase is performed once for a new skeleton. After the retarget pose, root, hand, and foot chains are calibrated, the remaining phases can be repeated in batches for new motions.

<p align="center">
  <img src="./assets/images/3d-motion/ik-retarget-preview.png" alt="Unreal IK Retargeter synchronous source and SOMA77 preview" width="960">
</p>

*The Unreal IK Retargeter preview is the human checkpoint for skeleton mapping, scale, root behavior, and critical hand/foot chains before motions enter training.*

## 2. Showcase A — Show_AssaultAim: from a generic stance to a specific armed gesture

### Background and problem

The desired action was not simply “an assault motion.” The reviewed description was:

> A person holds a rifle and makes a short aggressive assault-ready motion, swinging the rifle upward twice, then raising the left hand forward before returning to aiming.

The base model produced a plausible armed stance, but it did not reliably reproduce this ordered gesture. A comparison was also unreliable until generation used the same duration as the GT clip.

### Iteration

- **0714:** establish the complete NPZ → SOMA77 FBX → Unreal preview chain and generate first-pass results for all 16 actions.
- **0716:** replace rough action names with observable English body-motion descriptions and generate every action with its corresponding GT duration.
- **0720:** preserve the upper-body gesture while adding repaired foot-contact supervision, stronger root/foot weighting, and an explicit anti-skating objective.

<p align="center">
  <img src="./assets/images/3d-motion/motion-iteration-timeline.png" alt="Three motion fine-tuning iterations" width="960">
</p>

### Final visual comparison

<table>
  <tr><th>Kimodo base</th><th>Ground truth</th><th>0720 fine-tuned result</th></tr>
  <tr>
    <td><img src="./assets/images/3d-motion/assault-base.gif" alt="Base Show AssaultAim motion" width="300"></td>
    <td><img src="./assets/images/3d-motion/assault-ground-truth.gif" alt="Ground-truth Show AssaultAim motion" width="300"></td>
    <td><img src="./assets/images/3d-motion/assault-0720-final.gif" alt="0720 fine-tuned Show AssaultAim motion" width="300"></td>
  </tr>
</table>

The final clip is evaluated against a same-duration GT reference and keeps the requested rifle/hand sequence visible. For this action, the reported contact-foot drift proxy changed from **0.00398 to 0.00174 m/frame**, a **56%** reduction from the 0716 result.

## 3. Showcase B — TacticalSign_CTMAim: diagnosing and correcting foot skating

### What went wrong after the semantic update

The 0716 round improved motion descriptions and timing, but foot skating became more visible. The issue was not solved by simply increasing a foot-position loss. Retargeted GT clips contained small floating and jitter, so the original contact thresholds produced fragmented supervision:

- Base-model outputs for these 16 local prompts had a mean foot-contact ratio of approximately **0.960**.
- The original saved GT contacts averaged approximately **0.273**.

The base figure is not a statistic from Kimodo’s original training set. It is the base model’s output distribution for this specific 16-prompt armed-motion set, used as a local planted-foot prior.

### Optimization key points

| Change | Why it mattered |
| --- | --- |
| Recompute contact labels with `velocity=0.75 m/s`, `foot height=0.16 m`, `toe height=0.10 m`, and one-frame gap filling | Recovered coherent planted-foot intervals without using the statistically closest but physically too-permissive threshold |
| Increase foot joint loss weights from 0.5 to 3.0 | Restored direct geometric control after repairing the labels |
| Increase root-position weight from 1.0 to 3.0 and root-heading weight from 0.5 to 1.0 | Reduced root/hips drift that otherwise moved the feet even when local foot joints were stable |
| Add a contact-conditioned foot-skating loss with weight 4.0 | Penalized predicted horizontal foot/toe velocity only across consecutive repaired GT contact frames |
| Keep upper-body weights higher than foot weights | Avoided copying retarget noise at the expense of the rifle and command gesture |

<table>
  <tr><th>0716 result</th><th>0720 result</th></tr>
  <tr>
    <td><img src="./assets/images/3d-motion/tactical-ctm-0716.gif" alt="0716 TacticalSign CTMAim motion" width="440"></td>
    <td><img src="./assets/images/3d-motion/tactical-ctm-0720.gif" alt="0720 TacticalSign CTMAim motion" width="440"></td>
  </tr>
</table>

### Final measured effect

The metric is the average horizontal foot/toe drift during consecutive repaired-GT contact frames; lower is better.

| Action | 0716 | 0720 | Relative reduction |
| --- | ---: | ---: | ---: |
| `Show_AssaultAim` | 0.00398 m/frame | 0.00174 m/frame | 56% |
| `Show_JammedAim` | 0.00433 m/frame | 0.00214 m/frame | 51% |
| `TacticalSign_CTMAim` | 0.00388 m/frame | 0.00099 m/frame | 74% |
| `TacticalSign_StopAim` | 0.00271 m/frame | 0.00078 m/frame | 71% |

These are four representative actions, not an aggregate result for all 16 clips. The metric is a contact-frame proxy and does not replace animation review in the target character and gameplay context.

<p align="center">
  <img src="./assets/images/3d-motion/0720-training-focus.png" alt="0720 total, contact, skating, and foot-joint training trends" width="960">
</p>

*The 0720 objectives converge stably after foot constraints are introduced. Absolute total-loss values should not be compared directly with 0716 because the objective and weights changed.*

## 4. Showcase C — making generated motion survive the FBX/Unreal delivery path

Fine-tuning success would not matter if conversion or retargeting changed the animation. The production path therefore uses Unreal for the semantic retarget and Blender for deterministic FBX/NPZ conversion:

1. Batch-retarget AdamAll or target-character animation to SOMA77 in Unreal.
2. Export SOMA77 animation FBX.
3. Convert SOMA77 FBX to Kimodo NPZ while retaining 77 joints, root/hips motion, frame rate, and clip length.
4. Generate SOMA77 motion with the fine-tuned model.
5. Convert NPZ back to SOMA77 FBX and batch-retarget it to the target character.
6. Review the target-character animation in Unreal and package FBX/UE assets with the mapping and scripts.

A sampled roundtrip validation covered three FBX clips and three NPZ clips in both directions. All six passed the 5 mm position and foot thresholds, retained 77 NPZ joints and at least 78 FBX bones including `Root`, and preserved frame counts. The largest reported position deviation in that sample was **0.010 mm**.

One concrete delivery bug also surfaced during the 0716 iteration: long animation-only FBXs could collapse when Unreal interpreted redundant top-level armature transform curves. The exporter fix removed the constant object-level curves with a very small simplification threshold while preserving every pose-bone key and the full action range. This is why the capability includes conversion validation and engine preview, not only training loss.

## 5. What the three rounds proved

| Round | Production problem | Change | Evidence after the round |
| --- | --- | --- | --- |
| 0714 | No reusable end-to-end path | Built retarget, conversion, generation, Unreal preview, and base/GT/final comparison | 16 first-pass armed-AIM outputs and a repeatable review loop |
| 0716 | Prompts and durations were not aligned with the reference motion | Added detailed observable descriptions and GT-matched generation lengths | All 16 actions became directly comparable; foot skating emerged as the next dominant defect |
| 0720 | Contact feet drifted during otherwise clear upper-body gestures | Repaired contact labels, added skating loss, and raised foot/root weights | Four reported actions showed 50–74% lower contact-foot drift proxy while retaining the armed gesture |

The evidence supports a specialized motion-generation workflow for the current standing rifle/AIM domain. It does not yet establish broad generalization to locomotion, crouching, prone movement, cover interactions, or arbitrary characters.

## 6. Reusable studio deliverables

The capability can be transferred to another character or studio as a package rather than a one-off checkpoint:

- fine-tuned Kimodo model;
- bidirectional Unreal IK Rig and IK Retargeter assets;
- skeleton mapping and retarget-pose configuration;
- batch scripts for source → SOMA77 and SOMA77 → target conversion;
- verified FBX ↔ Kimodo NPZ converters;
- prompt-description table and duration controls;
- target-character FBX or Unreal animation assets;
- visual comparison and foot-drift evaluation workflow.

## 7. Next pilot: expand coverage without losing the current controls

The next dataset should add locomotion, turns, crouching, prone motion, cover peeks, hit reactions, and compound gestures such as walking while signaling stop or advance. Each clip should keep a short observable English description—ideally beginning with “A person…” and describing prop, posture, limb trajectory, order, and return pose rather than only intent.

Pilot acceptance should combine semantic correctness, timing, foot stability, retarget quality, animation-edit burden, and in-engine review. The current 16-action result is a focused proof that targeted fine-tuning can solve a studio-specific motion family; broader action and character coverage remains the next validation step.
