# P4 Merge Workflow: A Staged, Spec-Driven Capability for Million-File Perforce Merges

Live-service game studios that keep a customized downstream branch of a Unity title periodically need to absorb an upstream dump. The dump may be a vendor snapshot, a localization fork, or another team’s mainline. The downstream branch already carries version numbers, hot-update endpoints, shop and billing rules, platform SDKs, and years of local gameplay. A single `p4 integrate` of that tree into the live branch is not a merge — it is an operational incident waiting to happen.

P4 Merge Workflow turns that incident into a repeatable GamePilot skill: detect the real stream topology, sync the dump by content digest instead of a full reconcile, inherit the live branch onto a temporary merge stream, split the remainder into path-disjoint pending changelists, and resolve each wave through specs, an agent, and a human who still owns every submit.

This showcase focuses on the problems the conventional Perforce path cannot absorb, the reusable architecture, and what has been proven on a million-file Unity depot.

## 1. Background: the merge is necessary, but the conventional path does not scale

A Unity live-ops depot is large, binary-heavy, and semantically split. Upstream and downstream are usually **sibling development streams** under the same mainline — they have no parent/child integrate credit — so the change cannot be merged “along the stream graph.” It has to be staged.

| Where the work lived | Practical problem | Workflow impact |
| --- | --- | --- |
| A million-file upstream snapshot | `p4 reconcile` stats every workspace file against the server. | A sync that should take hours stretches into days; interruptions force a restart. |
| Live downstream (`Staging-launch` and equivalents) | Release config, CDN / patch hosts, shop, CI, and platform endpoints are downstream-only. | A naïve accept-theirs points the build at the wrong servers or drops billing rules. |
| Stream topology | `base/sync` and the live branch are siblings, not parent and child. | Direct integrate into live is both unsafe and historically credit-confused. |
| Conflict surface | Code, Prefabs, `.meta`, asmdefs, tables, and art all conflict at once. | One giant pending CL cannot be reviewed, compiled, or handed to a second person. |
| Agent / engineer context | `p4 integrate -n` and `p4 resolve -n` emit tens of thousands of lines. | A model that reads the raw output spends its window on noise and still cannot submit safely. |

Connecting an agent to `p4` without a workflow does not solve this. The agent will either freeze on command output, auto-merge files that must stay downstream, or open overlapping paths that Perforce refuses to hold in two pending changelists. The target was therefore not “an LLM that runs Perforce.” It was a reusable engineering capability that answers a narrower question: **how can a studio continuously absorb an upstream dump into a customized live branch without losing downstream meaning, and without forcing one person to resolve a million files in one sitting?**

## 2. Reusable architecture

The capability is a GamePilot skill plus a small set of local, deterministic helpers. The skill is the orchestration layer. The scripts never submit. The LLM never writes the depot. Humans remain the accepting authority.

![P4 Merge Workflow architecture](assets/images/p4-merge-workflow/p4-merge-architecture.svg)

| Component | Responsibility |
| --- | --- |
| Perforce streams | Source of truth. Upstream snapshot, `sync` mirror, temporary merge branch, live target. |
| GamePilot skill | Detects topology, sequences the five stages, compresses command output, applies specs, records audit. |
| `sync-from-upstream.py` | Digest-based add/edit/delete plan against a local dump. Cached, resumable, no submit. |
| `analyze_asmdef_topology.py` | Read-only Unity assembly graph used to order waves. |
| `summarize_diff_for_batching.py` | Collapses `p4 diff -se` into module / type / directory counts the agent can actually use. |
| Three-layer merge specs | Core red lines, this-merge runtime rules, and studio-specific module policy. |
| `.p4-merge/` audit | Compact `state-summary.md` for recovery, append-only per-CL logs, human-readable CL map. |
| Human | Confirms undecidable files and submits every changelist. |
| LLM | Planning and per-file judgement only. Self-hosted or cloud-managed; outside the depot write path. |

This split lets a studio adopt the capability incrementally. A team can start with digest sync of one dump into `sync`, add a temporary merge branch for the next import, then turn on wave planning and spec-driven resolve once the conflict surface is too large for a single owner.

## 3. Showcase 1 — digest sync instead of a full-tree reconcile

### The actual problem

Stage two is “make the downstream `sync` stream identical to this upstream snapshot.” The conventional Perforce answer is `p4 reconcile` over the client. On a million-file Unity tree that means a server round-trip per file, no useful resume, and a workspace that looks dirty for the entire run. Studios either wait, or they cherry-pick and slowly drift from upstream.

### How the workflow changes it

1. The agent binds a dedicated `sync` client and records `p4 info` / `p4 opened` before any mutating command.
2. `sync-from-upstream.py` batches `p4 files` / `p4 fstat` into a local digest cache, scans the snapshot for MD5, and writes a plan of add / edit / delete.
3. Only files whose digest actually changed are opened. Unchanged files are skipped entirely.
4. Caches are keyed by server, user, depot root, and head changelist. An interrupted run continues from the last completed batch.
5. The script stops at opened files. A human reviews `p4 opened` / `p4 diff -se` and submits.

The measured effect on a million-file depot is about an order of magnitude faster than reconcile, because the expensive work moves from per-file server stat to local digest comparison.

### Result

`sync` becomes a faithful, auditable mirror of the dump without a multi-day reconcile window. The live branch is still untouched. That is the point: **import and merge are different jobs**, and mixing them is how downstream endpoints get overwritten.

## 4. Showcase 2 — wave planning and a four-layer resolve funnel

### The actual problem

After `sync` is current, the remaining work is to combine it with the live branch. Doing that as one integrate produces a pending CL that no one can compile, review, or recover from. Unity makes the ordering worse: Prefabs that land before their scripts show missing components; assemblies that land before their dependencies do not compile; `.meta` that split from their main file become unsubmitable.

Sibling-stream history adds a second trap. A previous aborted merge can leave **stale integration credit**, so a plain `p4 integrate` reports “all revision(s) already integrated” while `p4 diff2` still shows a real delta.

### How the workflow changes it

The skill never integrates into live. It first copies live onto a temporary merge branch so downstream-only work is the baseline, then integrates `sync` into that temp branch in waves.

![Staged merge pipeline and resolve funnel](assets/images/p4-merge-workflow/p4-merge-core-workflow.svg)

**Stage 4A (plan once).** The agent uses asmdef topology, directory structure, GUID references, config pairing, and the project spec to draft waves. Each wave gets its own numbered pending changelist via `p4 integrate -c`. Paths are required to be disjoint. File-count and churn budgets are checked with `integrate -n` **before** files are opened, so an oversized code wave is split in planning rather than during resolve. Stale credit is probed with and without `-f`; deletions are covered with `-Ds`; leftover files are swept into a targeted cleanup CL, never a full-branch `-f`.

**Stage 4B (execute one CL).** The owner of a wave runs a funnel:

1. `p4 resolve -am` for non-overlapping edits.
2. Three-layer specs batch-accept theirs or yours (`-at` / `-ay`).
3. The agent reads diffs of remaining text files at or under ~500 lines.
4. Binaries, huge diffs, and undecidable files go to a human with an excerpt and a recommendation.

Core spec red lines are not negotiable: downstream version / channel / hot-update / CDN / shop / CI stay on the target side unless a human explicitly overrides them. Coordinated upstream refactors are taken as a set. An `.asmdef` that gained upstream references but also holds a downstream-only assembly is union-merged, not blindly taken.

Every decision is appended to that wave’s CL log. The global `state-summary.md` is the only file the agent rewrites in place, so a crashed session recovers by reading tens of lines rather than a giant transcript.

### Result

A million-file integrate becomes a list of reviewable changelists with known owners, known path ranges, and a compile story that matches Unity’s real dependency order. Intermediate compile failure after a single code wave is treated as normal, not as a reason to revert the whole merge.

## 5. Showcase 3 — one pipeline for 1..N people, via shelve handoff

### The actual problem

The merge is too large for one programmer and too coupled for “everyone integrate their own folder.” Perforce numbered pending changelists are bound to the client that created them; they cannot be reassigned. Sharing one workspace is worse: machines are not co-located, and opened files collide.

### How the workflow changes it

There is only one pipeline. Headcount changes who executes stage 4B, not how waves are planned.

- **One person:** the coordinator is the only executor. Resolve and submit happen on the coordinator client. Shelve is unused.
- **N people:** stage 4A still builds every pending CL on the coordinator client, then `p4 shelve`s each wave. Assignees `unshelve` onto their own clients, resolve locally, and shelve back. The coordinator unshelves the returns and is the only submitter.

Roster comes from a project developer list plus a manual override, so art waves can go to art, table waves to design, and code waves to programming, without inventing a second workflow. Because 4A already made path ranges disjoint, parallel resolve is file-safe without a locking protocol.

The human-readable `cl-dependencies.html` viewer is a static copy of the template; only a small `cl-dependencies-data.js` is rewritten when status changes. People can open the map in a browser without a local server.

### Result

The expensive intellectual work — “which files belong in this wave, and do they overlap?” — is done once. Execution can fan out across machines without forking the plan, without sharing a client, and without anyone but the coordinator submitting to the temp branch.

## 6. Scope, boundaries, and rollout guidance

### Current capability

- Topology-first preparation: live vs frozen streams are detected with `p4 streams` / latest CL date, not copied from a stale example.
- Digest-based snapshot import onto a `sync` stream, resumable, no automatic submit.
- Temporary merge branch that inherits live before absorbing `sync`.
- Module-first wave planning with Unity asmdef order, CL size budgets, deletion coverage, and stale-credit handling.
- Four-layer resolve guided by core, runtime, and project specs.
- Compact audit that supports interrupt-resume and multi-person append-only CL logs.
- Shelve handoff when more than one client must execute waves.
- Proven on the NIKKE `a2-frontend` depot: upstream `//unity/qa-*` snapshots into `//a2-frontend/base/sync`, then through a temp branch toward `//a2-frontend/version/Staging-launch`.

### Current boundaries

- The skill **does not auto-submit**. Preparation, check, and record are automatic; submit is a human action unless the user explicitly orders it.
- It **does not merge upstream into the live branch**. That path is the failure mode the workflow exists to prevent.
- Wide `p4 reconcile` on a large client is out of policy. Digest sync is the import tool.
- Retrieval and resolve quality depend on spec quality. A missing project spec will still keep core red lines, but studio-specific modules (for example “shop is entirely downstream”) must be written down.
- The agent sees compressed command output by design. It will not read a 20,000-line `resolve -n` dump.
- `p4 obliterate` is forbidden. Bad waves are reverted or undone with a reverse CL.
- Commands assume a Windows Perforce workspace and PowerShell. The skill is not a cross-OS p4 wrapper.

### Recommended adoption path

Start with one dump and two jobs: (1) digest-sync it onto a dedicated `sync` stream, (2) run a dry-run 4A on a throwaway temp branch until wave budgets and leftover coverage are honest. Write the first runtime spec from the first ten confirmed resolve decisions. Add a project spec only for modules that repeatedly violate generic rules. Expand to multi-person shelve after a single owner has submitted a few waves cleanly — the coordination cost is real, and it only pays once the plan is stable.

The reusable core is the staged topology, the digest import, the path-disjoint wave, the spec funnel, and the compact audit. The NIKKE file lists are a project pack, not the product.
