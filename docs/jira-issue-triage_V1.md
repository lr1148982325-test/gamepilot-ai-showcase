# Jira Issue Triage with DevPilot: Declarative Agents for Recurring Dev Workflows

Every studio has a queue nobody wants: incoming bug reports that need a first pass. Someone must read each one, work out whether it is a duplicate of something filed last week, gather the obvious evidence, guess the likely owner, and write that down. It is unskilled relative to the people doing it, it is never urgent enough to schedule, and it silently sets the ceiling on how fast real bugs get fixed.

DevPilot automates that first pass. It is a **generic agent runtime** — a single process that turns webhooks and cron ticks into durable, sandboxed agent runs — and Jira triage is its most developed application. The design bet worth paying attention to: an agent is a **folder of YAML, Markdown, and JSON Schema**, not code. Adding a new automation means writing a playbook and an output contract, not shipping a TypeScript module.

## 1. Where the effort actually goes

| Triage task | What a human does today | What the agent does |
| --- | --- | --- |
| Duplicate detection | Half-remembers a similar ticket, searches, gives up under time pressure | Searches deliberately and reports candidate duplicates with reasoning |
| Evidence gathering | Opens the issue, reads comments, maybe downloads a log | Pulls the raw issue and comments, and inspects attachments when needed |
| First code look | Usually skipped | Optionally reads a read-only checkout for supporting context |
| Owner guess | Asks in chat, or leaves unassigned | Emits an owner hint based on evidence |
| Writing it down | Inconsistent, often not at all | One structured findings comment per issue |
| Proving it was done | Nothing, so work gets redone | A processing label that makes the loop idempotent |

The goal is not to close issues. It is to make sure that when a human opens a ticket, the boring work is already done and visible.

## 2. Runtime architecture

![DevPilot runtime architecture](assets/images/jira-issue-triage/devpilot-runtime.svg)

Three properties matter more than the box diagram:

**Intake only records; it never works.** A webhook or cron tick is normalized into a run request and written to a SQLite queue, which returns immediately. The dedupe key becomes the run id, and uniqueness is enforced in the database — so a redelivered webhook is a no-op rather than a second run. Interrupted runs are reclaimed by lease expiry instead of being lost. This is deliberately single-instance: the queue is a local durable log, not a distributed broker.

**Sandboxing is declared, not assumed.** A step gets no tools by default. Each pack opts into a tool profile — read-only, workspace, or sandboxed with `bash` — and the strongest profile *refuses to start* without an OS-level sandbox backend rather than quietly downgrading. This matters because a triage agent reads attacker-influenceable text: a bug report can contain instructions. Containment is enforced per filesystem call on the resolved real path, so a symlink cannot escape the workspace, and network egress is denied unless a pack names the hosts it may reach.

**Secrets are mounted, never prompted.** Credentials reach the sandbox as mounted files and environment variables. The model is told the variable *names* and never the values, and playbooks are instructed never to print them.

## 3. The triage flow

![Dispatcher fan-out to per-issue workers](assets/images/jira-issue-triage/triage-flow.svg)

The pattern is a **dispatcher and a worker** — two packs, one relationship.

The dispatcher runs on a weekday-morning cron, queries **one saved Jira filter**, and emits one work item per issue. Using a saved filter is the important design choice: the team controls triage scope in Jira, where they already manage queries, rather than in agent configuration.

Each emitted item becomes an **independently queued worker run**. That is what makes this robust — fifty issues are fifty runs, each separately retried, recorded, and auditable. One malformed ticket cannot fail the batch, and triage quality does not degrade the way it would if fifty tickets shared one prompt.

Inside a worker run: pull the raw issue as primary evidence, check for duplicates, optionally consult a read-only code checkout, then emit a verdict against a strict schema — status, risk, findings, recommended action, owner hint, evidence, and limitations.

Three details are where the engineering actually is:

- **Dedupe keys include the last-updated timestamp**, so a genuinely updated issue produces a new run instead of being deduped away forever.
- **An empty result must be honest.** If Jira returns an authorization or network error, discovery fails loudly. A broken credential can never present itself as "no issues to triage today."
- **The label is a finalization gate.** The processing label is applied only *after* the findings comment succeeds, then read back to verify. If either step fails, the run ends as needs-human. Comment and label cannot drift apart, which is what keeps the daily loop safely repeatable.

## 4. Scope discipline

Jira access is read-only apart from exactly two writes: **one findings comment and one processing label.** The agent cannot transition, reassign, reprioritize, close, or edit other fields.

This is a deliberate trust boundary. Triage earns adoption by being reversible — a wrong comment is cheap to ignore, whereas a wrong transition disrupts someone's sprint. Supporting constraints in the same spirit: attachments are gated on size and type with a filename treated as untrusted, the comment is posted from a file so Markdown is never mangled by shell quoting, and a mounted code checkout is a throwaway copy whose edits are discarded.

## 5. Why declarative packs

A pack is a directory: `agent.yaml` for the trigger, config, and pipeline; Markdown playbooks for instructions; JSON Schema for the output contract; optional reusable skills. Packs are validated at startup — duplicate ids, missing playbooks, invalid schemas, and mismatched skills all fail fast rather than at 9am on a Monday.

| Step kind | Purpose |
| --- | --- |
| `agent` | Run a playbook through the model, validate output against a schema. |
| `dispatch` | Same, but fan each emitted item out as a child run. |
| `checkout` | Shallow git clone for code context. |
| `publish` | Render declared sinks and write a receipt. |
| `hitl` | Human-in-the-loop placeholder. |
| `refresh` | Re-probe facts that may have gone stale. |

The payoff is that the Jira triage story generalizes. The same runtime already carries a Jenkins build-failure analyzer, and the dispatcher/worker shape fits any "scan a queue, fan out, act per item" problem — flaky tests, crash clusters, dependency alerts, stale review requests.

## 6. Honest implementation status

This is a working system in active development, not a finished product. Stated plainly:

| Capability | Status |
| --- | --- |
| Trigger → durable queue → sandboxed agent → schema-validated JSON | Real, working end to end |
| Dispatcher fan-out into child runs | Real |
| Jira reads, findings comment, triage label | Real — performed by the agent through the Jira CLI inside the sandbox |
| Cron scheduling, dedupe, retries, lease recovery | Real |
| `publish` sinks | **Local stub.** Renders and writes a receipt file; calls no external system. |
| `hitl` human approval | **Local stub.** Writes a pending file and returns; does not block on a human. |
| `refresh` | Partial. Runs probes but does not act on contradictions. |
| Token budgets | Declared and reported, but only the wall-clock limit is enforced. |

Two clarifications that are easy to get wrong. First, the real Jira writes happen **inside the agent step** via the Jira CLI — not through the publish sink, which is still a stub. Second, **TAPD is not implemented.** The current integrations are Jira and Jenkins. TAPD is a natural next target because the pack model isolates the change to a new playbook plus a CLI or API surface, but nothing ships for it today.

## 7. Boundaries

- Triage produces a recommendation, not a decision. Routing and prioritization stay human.
- Duplicate detection is a candidate list with reasoning, not an authoritative merge.
- Code context is supporting evidence; the issue's own data remains the primary source of fact.
- The external CLI must be installed and configured on the host — the agent will not install it, and reports the missing dependency instead of guessing.
- Single active instance, on a persistent local volume. Not an active-active queue.
- Delivery is at-least-once, so any future external sink must be idempotent.

## 8. FAQ

**Why cron rather than a Jira webhook?**
A morning batch matches how triage is actually consumed, and one dispatcher run over a saved filter is cheaper and easier to reason about than reacting to every field change. Webhook triggers exist in the runtime if per-event triage is wanted.

**What stops it re-triaging the same issue forever?**
The processing label, checked at discovery. It doubles as the idempotency key, which is why the label write is gated on the comment write succeeding.

**What if the model returns something malformed?**
The step fails validation and retries per its policy. A run never publishes unvalidated output.

**Can it fix the bug it triaged?**
The runtime supports delegating to a coding agent, and the pack model makes that a pipeline step rather than a rewrite. Today the triage pack stops at findings — which is the right place to stop while trust is being established.

**How would TAPD be added?**
A new dispatcher playbook for TAPD's query surface and a worker playbook for its comment and label operations, reusing the same queue, sandbox, fan-out, and schema-validation machinery. The runtime is not Jira-specific; only the two playbooks are.
