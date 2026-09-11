# Code Review Agent: Multi-Perspective AI Code Review for Game Studios

Most AI code review produces one generalist opinion about a diff. That opinion is usually shallow in a predictable way: it notices a missing null check, misses the replication desync, and suggests renaming a variable. A single reviewer with a single prompt has a single bar, and everything gets flattened to it.

This agent reviews every change from **four independent perspectives at once** — logic, security, quality, and performance. Each is a separate subagent with its own focus, its own confidence bar, and its own explicit list of things it refuses to report. They run in parallel and their findings are merged, so a bug that is both a crash and an exploit is reported once with the higher severity, and a style nitpick is reported by nobody.

## 1. Where it fits

The service is the orchestration layer; the review logic lives in the GamePilot CLI. The agent detects a change, decides whether it is in scope, invokes the CLI's `/review` skill, and posts the results back where the team already works.

![Deployment architecture](assets/images/code-review-agent/cr-agent-architecture.svg)

| Component | Responsibility |
| --- | --- |
| Perforce / Git | Source of truth. Read-only. |
| Swarm + AI CR plugin | Emits a review event on a changelist. GitLab and Gongfeng webhooks serve the same role. |
| Code Review Agent | Queue, scope filters, CLI invocation, comment posting, notification. No review judgement. |
| GamePilot CLI (`/review`) | Resolves targets and runs the four reviewer subagents. This is where the analysis happens. |
| AI Backend Service | Knowledge retrieval and per-studio configuration. |
| Elasticsearch | Studio rule index, queried per diff. |
| Langfuse + Postgres | Tracing, evaluation, and run state. |
| LLM | The only component outside the studio boundary. Self-hosted or cloud-managed. |

Everything except inference runs inside the studio network.

> **Note on the codebase.** The review service also contains an older in-process review engine. That path is legacy. The current version delegates to the GamePilot CLI, which means review behaviour is versioned with the same toolchain engineers run locally — so the reviewers that comment on a merge request are the reviewers an engineer can run before committing.

## 2. Four perspectives, one diff

![Four reviewer perspectives on the same diff](assets/images/code-review-agent/cr-agent-review-tracks.svg)

Each track asks a different question. The separation is not cosmetic — each subagent has a distinct method, and each explicitly hands off concerns that belong to a sibling.

| Track | Question | Method | Refuses to report |
| --- | --- | --- | --- |
| **Logic** | Is it correct? | Intent-first and contract-first. Identifies who owns the behaviour, what defines correctness, and traces the data path through the change. | Style, missing tests, subjective design, anything a linter catches. |
| **Security** | Is it exploitable? | Source-to-sink. Traces attacker-controlled input across a trust boundary to a privileged sink and locates the missing guard. | Generic hardening, "best practice" advice, anything without a constructible exploit path. |
| **Quality** | Will it crash? | Twelve engine-native detection categories over the changed scope. | Formatting, naming, pure performance issues, pure security issues. |
| **Performance** | Is it fast enough where it matters? | Placement and scale. Flags wasted work the diff adds to a reachable hot path and names the cheaper alternative. | Micro-optimizations, anything needing a profiler to confirm, anything trading correctness for speed. |

### What each track actually looks for

**Logic** — branch and boundary errors, loop termination, state and serialization bugs, event ordering and async lifecycle problems, contract mismatches that break existing callers, and symptom patches that leave another reachable path broken. For game code it pays specific attention to tick loops, cooldowns, ability rules, save/load state, client/server authority, prediction, and multiplayer desync.

**Security** — injection, path traversal, unsafe deserialization, authorization and ownership bypass, secret exposure, unsafe cryptography. In game terms: server-authority violations, RPC abuse, economy and save tampering, and anti-cheat bypass. The bar is deliberately harsh — the presence of a `UFUNCTION(Server, ...)` or a `[ServerRpc]` is not a finding. It only reports when it can name the attacker-controlled source, the boundary crossed, the missing guard, and the privileged effect.

**Quality** — this is the most engine-specific reviewer, covering Unreal C++, Unity C#, and UE gameplay scripting in Lua or TypeScript. Its twelve categories are: lifetime and dangling references; use-after-free and use-after-move; null and invalid object dereference; uninitialized state; numeric correctness; division by zero; always-true/always-false conditions; resource leaks; concurrency and races; container and engine API misuse; dead code; and crash-facilitating maintainability risks. The evidence it looks for is genuinely engine-aware — raw `UObject*` members invisible to GC, unchecked `TWeakObjectPtr`, access after pending-kill, container element references used after a reallocation, script-side proxies outliving their UObject, Unity references surviving a scene reload.

**Performance** — new cost in per-frame, tick, render, physics, AI, or replication paths; allocations, string formatting, and reflection in hot loops; accidentally quadratic scans and full-scene searches; synchronous asset or shader loading on gameplay paths; unbounded caches and leaked subscriptions; per-frame reliable RPCs and per-client work that scales badly with player count.

### Why the separation holds up

Three properties make this more than four prompts in a trench coat:

**Deliberate deferral.** The quality reviewer will not report a pure performance issue or a pure exploit — it hands those to its siblings. This is what stops each track from drifting into a generalist. A reviewer that can report anything reports everything.

**Per-track verification.** Before emitting anything, each reviewer classifies its own candidates as `CONFIRMED`, `PLAUSIBLE`, or `REFUTED`. Confirming requires naming the trigger — the input, state, or timing that reaches the bug — and quoting the modified line that causes it. Refuting requires quoting the guard that makes it a non-issue. At the default effort level only confirmed findings are emitted; security stays precision-biased at every level.

**Agreement raises confidence, not volume.** At merge, overlapping findings are deduplicated by file, line range, root cause, and suggested fix. When two tracks agree, the finding keeps both labels and the higher severity. Output is capped per effort tier, most severe first.

## 3. Controlling scope and depth

Reviews are tunable in two dimensions, which matters because a pre-commit check and a release-branch audit are not the same job.

| Dimension | Options | Effect |
| --- | --- | --- |
| Track selection | `--scope all` / `logic` / `security` / `quality` / `performance` | Which reviewers run. A studio can enable only what it trusts. |
| Depth | `--effort low` / `medium` / `high` | `low` is a fast hunk-only pass with no verification. `medium` is precision-biased. `high` broadens search, adds a gap sweep, and becomes recall-biased — surfacing plausible findings with their uncertainty disclosed. |

Findings carry `file_path`, `track`, `line_range`, `severity`, `issue`, `why`, `failure_scenario`, and `suggestion`. The `failure_scenario` field is the useful one in practice: it forces a concrete trigger rather than a vague warning.

## 4. Studio standards as versioned artifacts

Generic reviewers miss what is specific to a studio. Teams commit their conventions into the repo and the reviewers honour them.

- **`REVIEW.md`** under `.gamepilot/`, `.gpc/`, or `.rdec/` calibrates severity, sets nit limits, adds repository-specific checks, and can select which reviewer tracks run. A studio can disable the performance track by default, or restrict quality findings to high severity and above.
- **Rule files and `AGENTS.md`** are synced into the rule index on push and retrieved per diff. Deleting the file retracts the rule, so standards cannot silently rot out of sync with the codebase.
- Retrieved rules are treated as authority over the model's generic priors, with private studio rules ranked above public defaults.

This is the mechanism that converts a generic reviewer into *this studio's* reviewer, and in practice it moves precision more than any model choice.

## 5. Scope and boundaries

| Area | Coverage |
| --- | --- |
| Languages | C/C++, C#, Lua, Python, TypeScript/JavaScript, Java, Go, and other common source types. |
| Engines | Unreal (C++, Blueprint inspection, gameplay scripting) and Unity (C#). |
| SCM | Perforce, Git, GitLab, Gongfeng. |
| Excluded by default | Deleted files, binaries, generated artifacts, tests and mocks, lockfiles, config, minified bundles, documentation. Blueprint assets are reviewed only when explicitly named. |

Honest limits:

- Findings must anchor to a modified line. This is the right trade-off but it means the agent will not flag a pre-existing bug the change merely sits next to.
- It reviews a **bounded change**, not a system. It will not tell you the architecture is wrong.
- Severity is reported and used for ranking. It is not a merge gate — gating policy belongs to the team.
- Review quality depends on retrievable context. Perforce studios must sync source into the service; without it, reviewers lose the cross-file evidence the confirmation bar depends on.
- Ticket text from Jira / TAPD is treated as untrusted input, since it is attacker-influenceable in some workflows.
- Human review remains the accepting authority.

## 6. FAQ

**Why four reviewers instead of one good prompt?**
Because a single reviewer has a single bar. Splitting the work lets each track set a bar appropriate to its domain — security demands a constructible exploit, performance demands a proven hot path — and lets each refuse the categories that make AI review noisy.

**Does this triple the review cost?**
Tracks run in parallel, and track selection is configurable. A studio can run logic and quality only, or use `--effort low` for fast pre-commit passes and reserve the full set for release branches.

**Can it modify code?**
No. All source access is read-only. Fixes are proposed in the `suggestion` field.

**What runs where?**
The service orchestrates; the CLI reviews. The same reviewer definitions run in an engineer's terminal and in the server-side review, so pre-commit and post-push feedback agree.

**Where should a studio start?**
One repo, advisory comments, two tracks. Then write down the conventions your seniors repeat in review — that step improves precision more than anything else.
