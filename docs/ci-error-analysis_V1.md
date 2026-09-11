# CI Error Analysis Service

> A reusable CI failure analysis capability for Studios: when Jenkins or BK-CI builds fail, the service pulls build logs, analyzes them with an Agent, and only reads Git / Perforce source context when the log evidence points to a source-code issue.

## Summary

CI Error Analysis Service productizes a recurring Agent loop for CI failure triage:

1. A CI system sends a failed-build webhook.
2. The service validates, normalizes, and queues the failed build event.
3. The Agent pulls build logs and build metadata from the CI server.
4. The Agent first analyzes the build log to identify the primary failure cause.
5. Only when the log evidence points to a source-code issue, the Agent reads relevant Git / Perforce context such as commits, changelists, files, or blame.
6. The service generates a concise root-cause report and sends it to a pluggable notification sink such as WeCom, Slack, or another team workflow.

This is designed as a reusable Studios capability. It is not a one-off pipeline script; it is a repeatable pattern for failed-event intake, Agent analysis, evidence-gated context retrieval, and notification.

## Why

CI failure triage has recurring operational cost:

- Failure evidence is split across Jenkins / BK-CI, raw build logs, source changes, and team chat.
- Engineers repeatedly open build links, scan logs, find failed steps, and decide whether the failure is code-related.
- Common errors and project-specific knowledge are mixed together, making lessons hard to reuse.
- Multiple Studios need similar CI/SCM/notification integrations but often rebuild them independently.

CI Error Analysis Service turns that work into a stable loop: receive the event, collect bounded evidence, run Agent analysis, and send a short actionable report back to the team workflow.

## Core Loop

```text
failed build webhook
  -> normalize failed event
  -> enqueue analysis task
  -> pull build log from CI server
  -> analyze build log with Agent
  -> optionally pull source context when log evidence points to a source-code issue
  -> generate root-cause report
  -> notify configured sink
```

Design principles:

- **Log first**: analyze raw CI logs before touching source repositories.
- **Evidence-gated SCM**: read source context only when logs contain evidence such as stack traces, file paths, compiler errors, test failures, commits, or changelists.
- **Read-only context**: SCM access is for evidence collection only; the service does not modify code.
- **Small report**: notifications should be short, actionable, and traceable.
- **Pluggable delivery**: reports can be delivered through team-native sinks such as WeCom, Slack, or future integrations.

## Architecture

![CI Error Analysis Service - High Level Architecture](assets/images/ci-error-analysis-high-level.jpg)

Main components:

| Component | Role |
| --- | --- |
| CI Systems | Jenkins / BK-CI failed-build event sources. |
| Webhook API | Receives failed-build webhooks, parses provider payloads, and normalizes events. |
| Inbound Event Queue | Stores failed events awaiting analysis, with dedupe, retry, and async processing. |
| Analysis Worker | Pulls build logs and runs Agent-based failure analysis. |
| Source Control Repositories | Git / Perforce source context, used only when needed. |
| Outbound Notification Queue | Stores reports awaiting delivery so analysis and notification are decoupled. |
| Notification Worker | Sends reports through pluggable notification sinks such as WeCom, Slack, or future integrations. |

## Runtime Flow

![CI Error Analysis Service - Runtime Flow](assets/images/ci-error-analysis-flow.jpg)

Flow:

1. **CI Server -> Error Analysis Server**  
   Jenkins / BK-CI sends a failed-build webhook with build id, job / pipeline, build URL, branch, commit, and related metadata.

2. **Validate and enqueue**  
   The service validates the failed event, normalizes fields, deduplicates repeated deliveries, and writes the task to the inbound queue.

3. **Pull build log from CI server**  
   The Agent uses provider configuration and build metadata to pull the console log, failed step, and build context.

4. **Analyze build log with Agent**  
   The Agent first classifies the failure from logs: environment issue, dependency issue, compiler error, test failure, toolchain issue, resource issue, or another category.

5. **Only pull source code when necessary**  
   If log evidence points to a source-code issue, such as a source file, stack frame, compiler error, test assertion, commit, or changelist, the Agent reads the relevant Git / Perforce context.

6. **Generate and deliver report**  
   The service generates a compact root-cause report and sends it through the configured notification sink.

## What The Agent Should Report

Recommended report shape:

```text
Conclusion: <one-sentence most likely root cause>

Evidence:
- <key error from logs>
- <failed step / job / build link>
- <optional: relevant commit / changelist / file evidence>

Recommendation:
- <next debugging or fix action>

Ownership signal:
- Trigger User: <build trigger user>
- Candidate Change Author: <only when SCM evidence supports it>
```

Avoid:

- Assigning blame to a change author without source evidence.
- Pasting large log blocks without a conclusion.
- Reading whole repositories or syncing large Perforce workspaces prematurely.
- Including secrets, tokens, webhook keys, or credentials in reports.

## Capability Contract

| Area | Contract |
| --- | --- |
| Input | Jenkins / BK-CI failed-build webhook. |
| Output | Compact root-cause report for the configured team workflow. |
| CI access | Pull only the logs and metadata for the current failed build. |
| SCM access | Disabled by default; when enabled, read source context only when log evidence requires it. |
| Notification | Pluggable sink model for team workflows such as WeCom, Slack, or future channels. |
| SCM integration | Supports modern SCM systems such as Git and Perforce through flexible Agent skills and read-only evidence collection. |
| State | SQLite inbound / outbound queues with dedupe, retry, and retention cleanup. |
| Safety | Agent policy should keep CI and SCM inspection read-only. |

## Integration Surface

### Jenkins

For Jenkins Pipeline and multibranch Pipeline jobs, the recommended integration is a shared library. Jenkinsfiles only need a failure post hook:

```groovy
post {
  failure {
    ciErrorAnalysisNotify()
  }
}
```

For freestyle jobs, the Jenkins Notification Plugin can be used instead.

### BK-CI

BK-CI sends build-end events. The service accepts only failed builds:

```text
event = BUILD_END
data.status = FAILED
```

### Pluggable Notification Sinks

Analysis results are delivered through a sink abstraction rather than being tied to one chat system. WeCom is supported today, and the same pattern can support Slack or other Studio-native workflows.

### Modern SCM Integration

SCM-assisted analysis is optional and skill-driven. The service can integrate with modern SCM systems such as Git and Perforce, while keeping source access read-only and evidence-gated: the Agent reads source context only when build logs point to a source-code issue.

## Reusable Pattern For Studios Of All Sizes

This service can be generalized into a reusable Agent Loop template for all sizes of gaming studios, from AAA teams with complex build farms to small startups with lean CI pipelines:

| Pattern | Reusable Design |
| --- | --- |
| Trigger | External system emits an event, such as CI failure, crash spike, asset import failure, or build farm alarm. |
| Normalize | Convert heterogeneous provider payloads into a unified task model. |
| Scope | Keep evidence collection bounded to the failed build and only expand to source context when logs justify it. |
| Evidence collection | Pull the most direct evidence first, then read heavier context only when evidence requires it. |
| Agent analysis | Use fixed prompts and policy boundaries to produce actionable conclusions. |
| Notification | Send compact reports into Studio-native workflows through pluggable sinks. |
| Feedback loop | Later add user feedback, confidence scoring, similar-case retrieval, and knowledge-base capture. |

## FAQ

### Does the service pull source code for every failure?

No. The default flow is log-first analysis. Git / Perforce context is read only when log evidence points to a source-code issue.

### Can the Agent automatically fix code?

Not in this service's current scope. The service is for automated analysis and reporting. Policy and prompts should keep CI and SCM access read-only.

### What notification channels can it support?

The service uses a pluggable notification-sink model. WeCom is supported today, and the same interface can be extended to Slack or other internal team workflows.

### How does it work with source control?

SCM support is skill-driven. The Agent can work with systems such as Git and Perforce, but source access stays read-only and is used only when build-log evidence indicates that source context is relevant.

### Which teams should start with it?

Start with pipelines that fail often, have repetitive triage paths, expose enough log evidence, and have teams willing to give feedback on report quality. Keep the first phase log-only, then enable SCM-assisted analysis where it clearly improves root-cause quality.
