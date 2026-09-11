# GamePilot R&D Knowledge Base + DeepWiki: Turning Project Context into Reusable AI Capability

Game development knowledge rarely lives in one place. Architecture is encoded in source repositories, setup instructions drift across wiki pages, design intent is split among documents and spreadsheets, and important decisions remain in tickets or chat. This fragmentation affects people and AI agents in the same way: both must reconstruct project context before they can do useful work.

GamePilot R&D Knowledge Base + DeepWiki turns that scattered context into a maintained, permission-aware knowledge supply chain. DeepWiki first converts a game codebase into a navigable technical wiki. The Knowledge Base then combines that code understanding with project documents and exposes grounded context to onboarding, coding, review, design, QA, and operations workflows.

This showcase focuses on the problems solved in real workflows, the reusable architecture, and what has been proven in studio projects.

## 1. Background: project knowledge existed, but could not be reused reliably

A game project produces a large volume of useful knowledge, but its form and ownership make reuse difficult.

| Where knowledge lived | Practical problem | Workflow impact |
| --- | --- | --- |
| Perforce, Git, and SVN repositories | Architecture and implementation intent had to be inferred from a large and fast-changing codebase. | New developers did not know which systems or files to read first; coding agents lacked project-specific context. |
| Confluence, iWiki and shared documents | Setup guides, specifications, design rules, tables, images, and formulas were separated by tool and organization. | People repeatedly searched multiple systems and reconciled conflicting versions manually. |
| Jira, TAPD and Slack | Decisions and ownership information were easy to lose in ticket history or conversations. | The reason behind an API, rule, or design constraint was often missing from the final implementation context. |

Connecting every source directly to an agent did not fully solve the problem. Independent keyword searches returned top-N fragments without a shared semantic model, consistent ranking, source hygiene, or project structure. The agent still had to assemble context, irrelevant chunks consumed its context window, and stale information could be treated as current guidance.

The target was therefore not a large document portal. It was a reusable engineering capability that could answer a narrower question: **how can a studio continuously turn native project data into trustworthy context for a specific development task?**

## 2. Reusable architecture

The reusable capability has two cooperating components:

- **GamePilot DeepWiki** transforms source repositories into structured technical knowledge and natural-language code navigation.
- **GamePilot Knowledge Base Service** ingests DeepWiki output and approved non-code sources, maintains searchable knowledge, and serves task-specific context to AI workflows.

![DeepWiki and Knowledge Base architecture](assets/images/deepwiki/deepwiki-architecture.svg)

This separation lets studios adopt the capability incrementally. A team can begin with code understanding through DeepWiki, add a few high-value project sources, and integrate the resulting knowledge into selected agent workflows before expanding coverage.

## 3. Showcase 1 — onboarding from an unfamiliar depot to a working mental model

### The actual problem

A new developer joining a large game project must understand architecture, configure a workstation, learn submission rules, decode project terminology, and find system owners. These answers may exist, but they are spread across source, setup pages, team documents, and prior troubleshooting records.

The expensive part is not reading one document. It is discovering the correct reading sequence and verifying that each instruction still matches the project.

### How the Knowledge Base changes the workflow

1. The developer asks DeepWiki for a high-level map of the relevant gameplay or engine system.
2. The answer identifies the relationship among major subsystems and links the developer to supporting code and assets.
3. The Knowledge Base retrieves the current workstation checklist, common build fixes, and submission rules from approved project sources.
4. A project glossary explains acronyms and internal tool names, while ownership knowledge identifies the team or person responsible for the subsystem.
5. Follow-up questions narrow the path, for example: “How does gameplay ability replication reach server authority, and which files should I read first?”

![DeepWiki presents a navigable architecture map together with repository-grounded Q&A](assets/images/deepwiki/deepwiki-architecture-query.png)

*DeepWiki combines a generated architecture map, source navigation, and repository-grounded answers in one view.*

### Result

The onboarding deliverable becomes a reproducible, evidence-backed path rather than a collection of bookmarks and personal explanations. The same capability supports different roles: a developer can trace runtime architecture, while a designer can ask for the configuration and ownership behind a gameplay feature.

## 4. Showcase 2 — project-aware coding and code review

### The actual problem

Generic coding agents can produce syntactically correct code while missing studio conventions, subsystem boundaries, telemetry requirements, API contracts, or earlier design decisions. Generic code review has the same weakness: without project context, it either overlooks a local rule or reports irrelevant best practices.

### How the Knowledge Base changes the workflow

During planning and generation, the agent retrieves project-specific examples and constraints such as:

- the approved studio SDK path for telemetry;
- established subsystem responsibilities;
- preferred API and error-handling patterns;
- relevant design decisions and implementation history;
- repository review guidance and source-control rules.

During review, specialized logic, quality, security, and performance reviewers use the same knowledge foundation before commenting on a change. Stable instructions can be synchronized into repository-local guidance, while the Knowledge Base provides deeper evidence only when the change requires it.

![An agent reviews a task plan using retrieved project knowledge and repository evidence](assets/images/deepwiki/knowledge-backed-review-output.png)

*The review agent retrieves project knowledge, inspects the relevant implementation, and returns concrete required changes and validation guidance.*

### Key optimization

The most effective improvement was not increasing prompt size. It was improving source hygiene and controlling what entered the task context. Default DeepWiki structure provides a useful starting point, but studio-specific knowledge structures, curated local maps, and retrieval rules make the output fit the actual engineering workflow.

### Result

Code generation and review can reference the project’s own standards, contracts, and examples. The workflow remains reviewable because retrieved context is tied to project evidence, and humans remain the authority that accepts the generated code or review finding.

## 5. Showcase 3 — a custom business wiki for studio-specific workflows

### The actual problem

Each studio has its own business vocabulary, content structure, configuration model, and daily workflows. For designers and content teams, the useful entry point is rarely a repository module or a generic document tree. They need to navigate concepts such as gameplay features, arenas, characters, combat configurations, story content, and related assets—and understand how information from different systems belongs together.

A generic code wiki cannot provide that experience by changing its table of contents alone. The business model, page templates, source mappings, relationships, and question boundaries all need to reflect how the customer actually works.

### How the Knowledge Base changes the workflow

The team works with the customer to identify the concrete tasks the wiki must support, then designs and implements a business-oriented knowledge experience around those requirements:

1. **Model the customer’s domain.** Define the navigation, terminology, entities, and relationships used by the studio—for example, feature modules, arena rules, character records, configurations, story content, and assets.
2. **Design scenario-specific pages.** Build page structures for the information users need together. A character page can combine profile data, combat and configuration details, story context, resources, and source references instead of exposing them as disconnected files.
3. **Map and transform project data.** Connect the relevant approved sources and transform their native structures into the business model, preserving identifiers and source relationships required for verification.
4. **Add contextual Q&A.** Let users ask questions within the current business page or across the customized wiki, with answers grounded in the assembled project knowledge.
5. **Validate with customer workflows.** Review the information structure and query behavior against real tasks, then refine the page templates and data mappings where the generic model does not fit.

![A customized business wiki combining character data, configurations, story resources, and contextual Q&A](assets/images/deepwiki/custom_wiki.png)

*This customized character page brings business data and related knowledge into one customer-specific structure, with contextual Q&A available alongside the page.*

### Result

The customer receives a purpose-built business wiki rather than a generic code wiki with renamed sections. Designers and content teams can navigate knowledge in their own domain language, inspect related information in one place, and ask questions in the context of the current business entity. The same customization approach can be reused for other studio domains, but the information model and delivery are shaped by each customer’s actual requirements.

## 6. Scope, boundaries, and rollout guidance

### Current capability

- Structured wiki generation and natural-language Q&A for P4, Git, and SVN codebases.
- Multi-source ingestion for engineering, design, art, QA, and operational knowledge.
- Query APIs for GamePilot AI workflows.
- Customized business wikis based on studio-specific requirements, domain models, page templates, and source mappings.
- Self-hosted deployment and role-based content access.

### Current boundaries

- Retrieval quality depends on source quality, freshness, permissions, and the knowledge structure chosen by the studio.
- Chat and ticket history can contain outdated or informal decisions; ingestion does not turn every statement into authoritative guidance.
- A generated answer must expose enough evidence for a user to verify it; the Knowledge Base does not replace code owners, designers, or reviewers.

### Recommended adoption path

Start with one project and two high-value scenarios: onboarding plus one daily development workflow. Generate the initial DeepWiki from the codebase, work with the studio to define the required business structure and source mappings, connect only the project sources required by those scenarios, and measure retrieval quality against real questions. Expand to more sources and roles after ownership, permissions, freshness, and evidence quality are working reliably.
