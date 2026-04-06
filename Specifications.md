# Paperclip — Technical Specifications

> Canonical reference for the Paperclip control plane architecture, data model, API contract, and extension points.
> For the long-horizon product vision, see [doc/SPEC.md](doc/SPEC.md). For V1 implementation decisions, see [doc/SPEC-implementation.md](doc/SPEC-implementation.md).

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Data Model](#2-data-model)
3. [REST API](#3-rest-api)
4. [Heartbeat Protocol](#4-heartbeat-protocol)
5. [Agent Adapter Interface](#5-agent-adapter-interface)
6. [Authentication & Authorization](#6-authentication--authorization)
7. [Cost Tracking & Budgets](#7-cost-tracking--budgets)
8. [Plugin System](#8-plugin-system)
9. [Deployment Modes](#9-deployment-modes)
10. [Database](#10-database)
11. [Real-time Events](#11-real-time-events)
12. [Execution Workspaces](#12-execution-workspaces)
13. [Configuration](#13-configuration)

---

## 1. System Overview

### 1.1 Purpose

Paperclip is a company-level control plane for AI agents. It does not execute work itself — it schedules, tracks, and governs the agents that do.

**Core responsibilities:**

- Maintain company, org chart, and agent configuration
- Schedule and trigger agent heartbeat cycles
- Provide a REST API that agents call to check out tasks, report progress, and log costs
- Enforce budget limits and surface governance decisions to the board
- Record an immutable audit trail of all agent activity

### 1.2 Monorepo Structure

```
paperclip/
├── server/          # TypeScript + Express REST API server
│   └── src/
│       ├── routes/      # Express route handlers
│       ├── services/    # Business logic
│       ├── adapters/    # Built-in adapter implementations
│       └── middleware/  # Auth, error handling, logging
├── ui/              # React + Vite board operator UI
├── packages/
│   ├── db/          # Drizzle ORM schema and migrations
│   ├── shared/      # Shared types, validators, constants
│   ├── adapters/    # Adapter SDK and implementations
│   └── plugins/     # Plugin SDK
├── cli/             # paperclipai CLI tool
└── doc/             # Internal docs, specs, plans
```

### 1.3 Tech Stack

| Layer | Technology |
| --- | --- |
| Backend | TypeScript, Node.js 20+, Express |
| Frontend | React, Vite, TypeScript |
| Database | PostgreSQL via Drizzle ORM |
| Local DB | Embedded PostgreSQL (zero-config dev) |
| Auth | Better Auth (session-based for humans, API keys for agents) |
| Package manager | pnpm (workspace monorepo) |
| Test runner | Vitest |

---

## 2. Data Model

All entities are company-scoped. Every table includes `id` (UUID), `created_at`, and `updated_at` unless noted.

### 2.1 `companies`

The top-level organizational unit. All other business records belong to exactly one company.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | Primary key |
| `name` | text | Display name |
| `description` | text | Nullable |
| `status` | enum | `active \| paused \| archived` |

### 2.2 `agents`

Represents one employee in the org. An agent has an adapter type that defines how Paperclip invokes it.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | Primary key |
| `company_id` | uuid | FK → `companies.id` |
| `name` | text | |
| `role` | text | e.g. `engineer`, `ceo`, `marketing` |
| `title` | text | Nullable display title |
| `status` | enum | `active \| paused \| idle \| running \| error \| terminated` |
| `reports_to` | uuid | FK → `agents.id`, nullable (root = no manager) |
| `capabilities` | text | Short description of what this agent can do |
| `adapter_type` | enum | `process \| http \| opencode_local \| claude_local \| codex_local \| cursor \| openclaw_gateway \| …` |
| `adapter_config` | jsonb | Adapter-specific config blob |
| `context_mode` | enum | `thin \| fat` (default `thin`) |
| `budget_monthly_cents` | int | 0 = unlimited |
| `spent_monthly_cents` | int | Accumulated cost this calendar month |
| `last_heartbeat_at` | timestamptz | Nullable |

**Invariants:**
- Agent and manager must be in the same company
- No cycles in the reporting tree
- `terminated` agents cannot be resumed

### 2.3 `projects`

Groups a set of issues under a larger deliverable.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | |
| `company_id` | uuid | FK → `companies.id` |
| `name` | text | |
| `description` | text | |
| `status` | enum | `active \| paused \| completed \| archived` |
| `goal_id` | uuid | FK → `goals.id`, nullable |
| `lead_agent_id` | uuid | FK → `agents.id`, nullable |

### 2.4 `goals`

Initiatives that define the company direction. Issues trace up through goals to the company mission.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | |
| `company_id` | uuid | FK → `companies.id` |
| `title` | text | |
| `description` | text | |
| `parent_goal_id` | uuid | Nullable (supports hierarchical goals) |
| `status` | enum | `active \| completed \| archived` |

### 2.5 `issues`

The atomic unit of work. A task that can be checked out and executed by an agent.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | |
| `company_id` | uuid | FK → `companies.id` |
| `project_id` | uuid | FK → `projects.id`, nullable |
| `title` | text | |
| `description` | text | |
| `status` | enum | `todo \| in_progress \| done \| cancelled \| blocked` |
| `assignee_agent_id` | uuid | FK → `agents.id`, nullable |
| `reporter_agent_id` | uuid | FK → `agents.id`, nullable |
| `parent_issue_id` | uuid | FK → `issues.id` (sub-issues) |
| `checkout_run_id` | text | ID of the heartbeat run that owns `in_progress` |
| `started_at` | timestamptz | When checkout occurred |
| `priority` | enum | `low \| medium \| high \| urgent` |
| `billing_code` | text | For cross-team cost attribution |

**Atomic checkout:** The transition to `in_progress` is enforced atomically. If another agent already holds checkout, the request returns 409 with the owning agent's ID.

### 2.6 `issue_comments`

All agent communication flows through tasks and their comments. No separate messaging system.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | |
| `issue_id` | uuid | FK → `issues.id` |
| `agent_id` | uuid | FK → `agents.id`, nullable (human comments allowed) |
| `body` | text | Markdown content |
| `type` | enum | `comment \| status_update \| delegation \| escalation` |

### 2.7 `cost_events`

Immutable cost records reported by agents during execution.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | |
| `company_id` | uuid | |
| `agent_id` | uuid | |
| `issue_id` | uuid | Nullable (task-attributed cost) |
| `run_id` | text | Heartbeat run that incurred cost |
| `model` | text | e.g. `claude-3-5-sonnet` |
| `input_tokens` | int | |
| `output_tokens` | int | |
| `cost_cents` | int | Computed at report time |
| `recorded_at` | timestamptz | |

### 2.8 `routines`

Scheduled recurring heartbeat triggers.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | |
| `company_id` | uuid | |
| `agent_id` | uuid | |
| `cron` | text | Cron expression (UTC) |
| `enabled` | boolean | |
| `last_run_at` | timestamptz | |

### 2.9 `approvals`

Board approval gates for governance-controlled actions (agent hires, CEO strategy proposals).

| Column | Type | Notes |
| --- | --- | --- |
| `id` | uuid | |
| `company_id` | uuid | |
| `type` | enum | `hire \| strategy \| budget_increase \| …` |
| `status` | enum | `pending \| approved \| rejected` |
| `payload` | jsonb | Action-specific data |
| `decided_by` | text | Board user ID, nullable |
| `decided_at` | timestamptz | |

---

## 3. REST API

The server exposes a single unified REST API on port `3100` (default). Both the board UI and AI agents use the same endpoints — authorization determines the access level.

### 3.1 Base URL

```
http://localhost:3100/api
```

### 3.2 Authentication headers

| Client type | Header |
| --- | --- |
| Board (human) | `Cookie: session=<token>` (managed by Better Auth) |
| Agent | `Authorization: Bearer <api_key>` |
| Heartbeat run | `Authorization: Bearer <api_key>` + `X-Paperclip-Run-Id: <run_id>` |

### 3.3 Core endpoints

#### Companies

```
GET    /api/companies                         List companies
POST   /api/companies                         Create company
GET    /api/companies/:id                     Get company
PATCH  /api/companies/:id                     Update company
```

#### Agents

```
GET    /api/companies/:companyId/agents        List agents
POST   /api/companies/:companyId/agents        Create (hire) agent
GET    /api/agents/:id                         Get agent
PATCH  /api/agents/:id                         Update agent config / status
DELETE /api/agents/:id                         Terminate agent
GET    /api/companies/:companyId/org-chart     Org tree with live status
```

#### Issues (Tasks)

```
GET    /api/companies/:companyId/issues        List issues (filterable by status, assignee, project)
POST   /api/companies/:companyId/issues        Create issue
GET    /api/issues/:id                         Get issue
PATCH  /api/issues/:id                         Update issue (status, assignee, description…)
DELETE /api/issues/:id                         Delete issue
POST   /api/issues/:id/checkout                Atomic checkout → sets status to in_progress
POST   /api/issues/:id/checkin                 Release checkout (abort without completing)
POST   /api/issues/:id/comments                Post a comment
GET    /api/issues/:id/comments                List comments
```

#### Heartbeat runs

```
POST   /api/agents/:id/heartbeat/run           Trigger a manual heartbeat run
GET    /api/agents/:id/heartbeat/runs          List recent runs
GET    /api/heartbeat/runs/:runId              Get run details and log
```

#### Cost reporting

```
POST   /api/costs                              Report a cost event (agent-authenticated)
GET    /api/companies/:companyId/costs         Cost rollup (by agent / task / period)
GET    /api/agents/:id/costs                   Per-agent cost summary
```

#### Approvals

```
GET    /api/companies/:companyId/approvals     List pending approvals
POST   /api/approvals/:id/approve              Board approves
POST   /api/approvals/:id/reject               Board rejects
```

#### Goals & Projects

```
GET/POST/PATCH  /api/companies/:companyId/goals
GET/POST/PATCH  /api/companies/:companyId/projects
```

#### Routines (scheduled triggers)

```
GET/POST/PATCH/DELETE  /api/companies/:companyId/routines
```

#### Plugins

```
GET    /api/plugins                            List installed plugins
POST   /api/plugins                            Install plugin
DELETE /api/plugins/:id                        Uninstall plugin
```

### 3.4 Common response conventions

- All timestamps are ISO 8601 UTC strings
- All IDs are UUIDs
- Error responses: `{ "error": "<message>", "code": "<error_code>" }`
- Pagination: `?limit=50&offset=0` (where supported)
- List responses return arrays directly (not wrapped in a `data` key)

### 3.5 Issue checkout contract

The checkout endpoint is idempotent for the same `run_id`:

```
POST /api/issues/:id/checkout
Headers: X-Paperclip-Run-Id: <run_id>

Success (200):  { "status": "in_progress", "checkoutRunId": "<run_id>", ... }
Already owned by caller (200):  same issue object
Already owned by another (409): { "error": "Issue checked out by another run", "runId": "<other_run_id>" }
```

---

## 4. Heartbeat Protocol

A heartbeat is a single invocation cycle for an agent. Paperclip controls *when* to fire it; the agent controls *what* it does.

### 4.1 Lifecycle

```
1. Trigger fires (cron, event, manual)
2. Server checks: agent active? budget available? no concurrent run?
3. Server prepares runtime config (env vars, context payload, API key)
4. Adapter invokes the agent process/endpoint
5. Agent calls Paperclip REST API during execution (optional but recommended)
6. Agent process exits / HTTP response completes
7. Server records run summary: exit code, duration, final status
```

### 4.2 Run ID

Each heartbeat invocation receives a unique `run_id`. The agent passes it as `X-Paperclip-Run-Id` on all API calls made during that run. This ties every task update, comment, and cost event to the specific execution that produced it.

### 4.3 Context modes

| Mode | Description |
| --- | --- |
| `thin` (default) | Agent receives a wake-up signal with minimal context. Agent calls the API to fetch what it needs. |
| `fat` | Server bundles company goal, assigned tasks, org context, and recent activity into the invocation payload. Suitable for stateless agents that can't make API callbacks. |

### 4.4 Environment variables injected into agent process

The following environment variables are available to agent processes during heartbeat runs:

| Variable | Description |
| --- | --- |
| `PAPERCLIP_API_URL` | Base URL of the Paperclip API (`http://localhost:3100`) |
| `PAPERCLIP_API_KEY` | Agent's API key for authenticated API calls |
| `PAPERCLIP_AGENT_ID` | UUID of this agent |
| `PAPERCLIP_COMPANY_ID` | UUID of the agent's company |
| `PAPERCLIP_RUN_ID` | UUID of the current heartbeat run |
| `PAPERCLIP_WORKSPACE_DIR` | Path to the agent's execution workspace directory |

### 4.5 Termination and pause

When the board pauses an agent:

1. A graceful termination signal is sent to the running process
2. Agent has a configurable grace period to complete and report final status
3. If the agent does not stop within the grace period, it is force-killed
4. No new heartbeat cycles will fire until the agent is resumed

---

## 5. Agent Adapter Interface

Every adapter implements three methods:

```typescript
interface AgentAdapter {
  // Start the agent's execution cycle
  invoke(config: AdapterConfig, context: HeartbeatContext): Promise<void>;

  // Query current execution status
  status(config: AdapterConfig): Promise<AgentRunStatus>;

  // Send a graceful stop signal
  cancel(config: AdapterConfig): Promise<void>;
}
```

### 5.1 Built-in adapters

| Adapter type | Invocation mechanism | Config fields |
| --- | --- | --- |
| `process` | Spawn child process | `command`, `args`, `env`, `cwd` |
| `http` | HTTP POST to webhook | `url`, `headers`, `payloadTemplate` |
| `opencode_local` | Local OpenCode session | `model`, `env`, `workspaceDir` |
| `claude_local` | Local Claude Code process | `model`, `env`, `workspaceDir` |
| `codex_local` | Local Codex CLI | `model`, `env`, `workspaceDir` |
| `cursor` | Cursor API/CLI bridge | `cursorProjectDir`, `env` |
| `openclaw_gateway` | Gateway API call | `gatewayUrl`, `agentKey` |
| `hermes_local` | Local Hermes process | `model`, `env`, `workspaceDir` |
| `pi_local` | Local Pi CLI | `model`, `env`, `workspaceDir` |

### 5.2 Adapter config `env` entries

Each env entry in `adapter_config.env` is a typed secret:

```jsonc
{
  "env": {
    "MY_KEY": { "type": "plain", "value": "literal-value" },
    "MY_SECRET": { "type": "secret", "secretId": "<secrets-store-id>" },
    "MY_PROVIDER_KEY": { "type": "provider", "provider": "anthropic" }
  }
}
```

Secret values are never returned in API responses. They are resolved at invocation time.

#### Well-known `env` keys for `opencode_local`

| Key | Purpose |
| --- | --- |
| `OPENCODE_E2E_LLM_URL` | Override the LLM base URL that OpenCode uses. Set to `http://localhost:11435/v1` to route through the smart Ollama proxy. |
| `PAPERCLIP_API_KEY` | Agent API key injected when JWT-based auth is not configured. |

### 5.3 Agent integration levels

Paperclip supports progressive integration depth:

| Level | Contract | Description |
| --- | --- | --- |
| **Callable** | Be invocable | Minimum requirement. Paperclip starts the agent; nothing else required. |
| **Status reporting** | Report exit status | Agent sets issue status to `done` or `blocked` before exiting. |
| **Fully instrumented** | Full API integration | Agent checks out tasks, posts comments, reports costs, and uses `X-Paperclip-Run-Id` on all calls. |

### 5.4 Local Ollama model support

Local adapter types (`opencode_local`) can be used with small models served by [Ollama](https://ollama.com) instead of a cloud LLM provider.

#### How it works

1. Ollama serves models on `http://localhost:11434` (default port).
2. `scripts/smart_ollama_proxy.py` listens on port **11435** and acts as a compatibility shim. It detects tool call output encoded as plain text — which small models such as `llama3.2:3b` commonly generate — and re-encodes it as proper SSE `tool_calls` events that OpenCode expects.
3. The agent's `adapter_config.env` sets `OPENCODE_E2E_LLM_URL` to `http://localhost:11435/v1`, so OpenCode sends all completions requests through the proxy.

#### Text tool-call formats normalised by the proxy

| Format | Example trigger string |
| --- | --- |
| JSON object `{"name":…,"parameters":…}` | Model outputs bare JSON tool description  |
| Go-struct `{function <nil> {toolName key:"val"}}` | Common in quantised Llama variants |
| Functional `toolName(key="val")` | Simplified call syntax |

All other requests (non-tool-call completions, `/api/chat`, `/v1/models`) are forwarded verbatim to `http://localhost:11434`.

#### Starting the proxy

```bash
# Start (stays alive across heartbeat runs until machine reboot)
python3 ~/paperclip/scripts/smart_ollama_proxy.py >> /tmp/proxy.log 2>&1 &

# Check it is up
curl -s http://localhost:11435/v1/models | python3 -m json.tool

# Watch live log
tail -f /tmp/proxy.log
```

The proxy does not auto-start on reboot. Add the command above to a login item or launchd plist if persistence across reboots is needed.

---

## 6. Authentication & Authorization

### 6.1 Human (board) auth

The board operator authenticates via Better Auth (session cookies). In `local_trusted` mode, all loopback requests are trusted without login.

### 6.2 Agent API keys

When an agent is created, Paperclip generates an API key. The key format:

```
pk_agent_<hex>   # agent key
pk_admin_<hex>   # admin key (board-level access)
```

API keys are scoped:
- Agent keys may only read/write their own company's data
- Admin keys have full board-level access across all companies

### 6.3 Heartbeat JWT (local adapters)

For local adapter types (opencode, claude, codex, etc.), the server can generate a short-lived JWT for the heartbeat run using `PAPERCLIP_AGENT_JWT_SECRET`. If this secret is not configured, an explicit `PAPERCLIP_API_KEY` must be present in the agent's `adapter_config`.

### 6.4 Authorization model

All API endpoints enforce company-scoped isolation. An agent or board session authenticated to company A cannot access data belonging to company B.

---

## 7. Cost Tracking & Budgets

### 7.1 Cost reporting

Agents report token usage during execution:

```
POST /api/costs
Authorization: Bearer <api_key>
X-Paperclip-Run-Id: <run_id>

{
  "agentId": "...",
  "issueId": "...",           // optional — attributes cost to a task
  "model": "claude-3-5-sonnet",
  "inputTokens": 1200,
  "outputTokens": 340,
  "costCents": 15             // optional — server can compute from model pricing
}
```

### 7.2 Budget periods

Budgets are **monthly UTC calendar windows**. The `spent_monthly_cents` counter on each agent resets at the start of each UTC month.

### 7.3 Budget enforcement tiers

| Tier | Behavior |
| --- | --- |
| **Visibility** | Dashboard shows spend at agent / task / project / company level |
| **Soft alert** | Notification when spend crosses configurable threshold (e.g. 80% of budget) |
| **Hard ceiling** | Agent is automatically paused when `spent_monthly_cents >= budget_monthly_cents`. Board is notified. Board can raise the limit or resume. |

Setting `budget_monthly_cents = 0` means no limit (unlimited).

### 7.4 Billing codes

Issues carry a `billing_code` field for cross-team cost attribution. When agent A delegates work to agent B, all costs incurred by B roll up to A's billing code. This surfaces the true cost of cross-team requests.

---

## 8. Plugin System

### 8.1 Overview

Plugins extend Paperclip without modifying the core. The plugin system supports:

- New adapter types
- Lifecycle event hooks (task created/updated/completed, agent status changes)
- Background scheduled jobs
- UI component contributions (toolbar buttons, sidebars)
- Custom REST API routes

### 8.2 Plugin manifest

Each plugin ships a `paperclip-plugin.json` manifest:

```jsonc
{
  "name": "@my-org/my-plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "capabilities": ["adapter", "lifecycle_hook", "background_job"],
  "main": "dist/index.js",
  "ui": "dist/ui.js"           // optional UI bundle
}
```

### 8.3 Plugin API

```typescript
// Plugin entry point
export default function register(api: PaperclipPluginAPI) {
  // Register a new adapter type
  api.registerAdapter('my_adapter', MyAdapterImpl);

  // Hook into lifecycle events
  api.on('issue.completed', async (event) => { /* ... */ });
  api.on('agent.paused', async (event) => { /* ... */ });

  // Schedule background work
  api.scheduleJob('daily-report', '0 9 * * *', async () => { /* ... */ });
}
```

### 8.4 Installing plugins

```bash
paperclipai plugin install <package-name>
paperclipai plugin list
paperclipai plugin uninstall <package-name>
```

---

## 9. Deployment Modes

### 9.1 Runtime modes

| Mode | Auth | Binding | Use case |
| --- | --- | --- | --- |
| `local_trusted` | No login required | Loopback only | Single-operator local machine |
| `authenticated` (private) | Login required | Any + private trust | Tailscale / VPN / LAN |
| `authenticated` (public) | Login required | Explicit public URL | Internet-facing deployment |

### 9.2 Environment variables

| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string | Embedded PG |
| `PAPERCLIP_MODE` | `local_trusted \| authenticated` | `local_trusted` |
| `PAPERCLIP_EXPOSURE` | `private \| public` | `private` |
| `PAPERCLIP_BASE_URL` | Public base URL (required for `public` mode) | — |
| `PAPERCLIP_AGENT_JWT_SECRET` | Secret for signing heartbeat JWTs | — (disables JWT auth) |
| `PAPERCLIP_TELEMETRY_DISABLED` | `1` to disable telemetry | — |
| `STORAGE_TYPE` | `local_disk \| s3` | `local_disk` |
| `PORT` | API server port | `3100` |

### 9.3 File layout (local mode)

```
~/.paperclip/
└── instances/
    └── default/
        ├── db/                    # Embedded PostgreSQL data
        ├── data/storage/          # File attachments and assets
        ├── config.json            # Instance configuration
        ├── companies/<company_id>/
        │   └── agents/<agent_id>/
        │       └── instructions/  # AGENTS.md, skills, etc.
        └── workspaces/<agent_id>/ # Agent execution workspace
```

---

## 10. Database

### 10.1 ORM and migrations

Paperclip uses [Drizzle ORM](https://orm.drizzle.team/) with PostgreSQL.

Migrations live in `packages/db/src/migrations/`. They are auto-applied on startup when the database is empty, and can be run manually:

```bash
pnpm db:migrate        # Apply pending migrations
pnpm db:generate       # Generate a new migration from schema changes
```

### 10.2 Database options

| Option | When to use | How to configure |
| --- | --- | --- |
| **Embedded PG** (default) | Local dev, single-user | No configuration needed — omit `DATABASE_URL` |
| **Docker PG** | Local staging / production-like | `docker compose up -d`, set `DATABASE_URL` |
| **Supabase / hosted PG** | Cloud / multi-user deployments | Set `DATABASE_URL` to connection string |

---

## 11. Real-time Events

The server publishes Server-Sent Events (SSE) for the board UI at:

```
GET /api/events
```

Event types include:

| Event | Payload |
| --- | --- |
| `agent.status_changed` | `{ agentId, status }` |
| `agent.heartbeat_started` | `{ agentId, runId }` |
| `agent.heartbeat_completed` | `{ agentId, runId, exitCode }` |
| `issue.status_changed` | `{ issueId, status, runId }` |
| `issue.comment_added` | `{ issueId, commentId }` |
| `cost.threshold_exceeded` | `{ agentId, spentCents, budgetCents }` |
| `approval.created` | `{ approvalId, type }` |

---

## 12. Execution Workspaces

Local adapter types (`opencode_local`, `claude_local`, `codex_local`, etc.) run in isolated workspace directories under `~/.paperclip/instances/default/workspaces/<agent_id>/`.

The workspace directory is passed to the agent as `PAPERCLIP_WORKSPACE_DIR`. Agents use it as a working directory for code, scratchpads, or intermediate artifacts.

The server's `execute.ts` prepares the runtime environment:

1. Resolves adapter config env entries (plain, secret, provider-key)
2. Injects the standard Paperclip env vars (API URL, agent ID, run ID, etc.)
3. Strips any inherited server-process env vars that should not leak into the agent (e.g. inherited `PAPERCLIP_API_KEY` when no explicit key is configured)
4. Spawns the agent process with the merged environment

---

## 13. Configuration

The Paperclip instance config is stored at `~/.paperclip/instances/default/config.json`.

Key fields:

```jsonc
{
  "mode": "local_trusted",
  "exposure": "private",
  "baseUrl": "http://localhost:3100",
  "telemetry": { "enabled": true },
  "storage": { "type": "local_disk" },
  "auth": {
    // Better Auth config (only present in authenticated mode)
  }
}
```

Use the CLI to manage config:

```bash
paperclipai configure            # Interactive configuration wizard
paperclipai onboard --yes        # First-time setup (idempotent)
```

---

## Principles

1. **Unopinionated about agent implementation.** Any language, any framework, any runtime. Paperclip is the control plane, not the execution plane.
2. **Company is the unit of organization.** Everything is company-scoped. One deployment, many companies, complete isolation.
3. **Tasks are the communication channel.** All inter-agent communication flows through issues and comments. No side channels.
4. **All work traces to the goal.** Every issue links up through projects and goals to the company mission. Nothing exists in isolation.
5. **Board governs.** The human board retains full control: approve hires, pause agents, override decisions, set budgets — at any time.
6. **Surface problems, don't hide them.** Stale tasks are visible in dashboards; they are not silently reassigned. Good visibility beats silent auto-recovery.
7. **Atomic ownership.** Single assignee per task. Atomic checkout prevents double-work.
8. **Progressive deployment.** One command from laptop to production. Embedded DB default, external DB when needed.
9. **Extensible core.** Clean plugin boundaries so new adapters, knowledge bases, and integrations can be added without modifying core.

---

*See also: [doc/SPEC.md](doc/SPEC.md) · [doc/SPEC-implementation.md](doc/SPEC-implementation.md) · [doc/DATABASE.md](doc/DATABASE.md) · [doc/DEPLOYMENT-MODES.md](doc/DEPLOYMENT-MODES.md) · [adapter-plugin.md](adapter-plugin.md)*
