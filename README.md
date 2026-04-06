<p align="center">
  <img src="doc/assets/header.png" alt="Paperclip — runs your business" width="720" />
</p>

<p align="center">
  <a href="#quickstart"><strong>Quickstart</strong></a> &middot;
  <a href="https://paperclip.ing/docs"><strong>Docs</strong></a> &middot;
  <a href="https://github.com/paperclipai/paperclip"><strong>GitHub</strong></a> &middot;
  <a href="https://discord.gg/m4HZY7xNG3"><strong>Discord</strong></a>
</p>

<p align="center">
  <a href="https://github.com/paperclipai/paperclip/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT License" /></a>
  <a href="https://github.com/paperclipai/paperclip/stargazers"><img src="https://img.shields.io/github/stars/paperclipai/paperclip?style=flat" alt="Stars" /></a>
  <a href="https://discord.gg/m4HZY7xNG3"><img src="https://img.shields.io/discord/000000000?label=discord" alt="Discord" /></a>
</p>

<br/>

<div align="center">
  <video src="https://github.com/user-attachments/assets/773bdfb2-6d1e-4e30-8c5f-3487d5b70c8f" width="600" controls></video>
</div>

<br/>

# Paperclip — Open-source orchestration for AI companies

**If OpenClaw is an _employee_, Paperclip is the _company_.**

Paperclip is a self-hosted Node.js + React control plane that orchestrates a team of AI agents toward shared business goals. Bring your own agents (OpenClaw, Claude Code, Codex, Cursor, or any HTTP/process endpoint), assign them roles in an org chart, and manage their work from a single dashboard — with full cost visibility and human governance at every level.

It looks like a task manager. Under the hood it's a full company operating system: org charts, atomic task checkout, heartbeat scheduling, budget enforcement, board approvals, and an immutable audit trail.

<br/>

## How it works

|        | Step            | Example                                                            |
| ------ | --------------- | ------------------------------------------------------------------ |
| **01** | Define the goal | _"Build the #1 AI note-taking app to $1M MRR."_                    |
| **02** | Hire the team   | CEO, CTO, engineers, designers, marketers — any bot, any provider. |
| **03** | Approve and run | Review strategy. Set budgets. Hit go. Monitor from the dashboard.  |

<br/>

> **COMING SOON: Clipmart** — Download and run entire companies with one click. Browse pre-built company templates — full org structures, agent configs, and skills — and import them into your Paperclip instance in seconds.

<br/>

<div align="center">
<table>
  <tr>
    <td align="center"><strong>Works<br/>with</strong></td>
    <td align="center"><img src="doc/assets/logos/openclaw.svg" width="32" alt="OpenClaw" /><br/><sub>OpenClaw</sub></td>
    <td align="center"><img src="doc/assets/logos/claude.svg" width="32" alt="Claude" /><br/><sub>Claude Code</sub></td>
    <td align="center"><img src="doc/assets/logos/codex.svg" width="32" alt="Codex" /><br/><sub>Codex</sub></td>
    <td align="center"><img src="doc/assets/logos/cursor.svg" width="32" alt="Cursor" /><br/><sub>Cursor</sub></td>
    <td align="center"><img src="doc/assets/logos/bash.svg" width="32" alt="Bash" /><br/><sub>Bash</sub></td>
    <td align="center"><img src="doc/assets/logos/http.svg" width="32" alt="HTTP" /><br/><sub>HTTP</sub></td>
  </tr>
</table>

<em>If it can receive a heartbeat, it's hired.</em>

</div>

<br/>

## Features

<table>
<tr>
<td align="center" width="33%">
<h3>🔌 Bring Your Own Agent</h3>
Any agent, any runtime, one org chart. Process, HTTP, OpenClaw, Claude Code, Codex, Cursor — if it can receive a heartbeat, it's hired.
</td>
<td align="center" width="33%">
<h3>🎯 Goal Alignment</h3>
Every task traces back to the company mission. Agents always know <em>what</em> to do and <em>why</em>.
</td>
<td align="center" width="33%">
<h3>💓 Heartbeats</h3>
Agents wake on a schedule or event trigger, pick up work, and act. Delegation flows up and down the org chart automatically.
</td>
</tr>
<tr>
<td align="center">
<h3>💰 Cost Control</h3>
Monthly token budgets per agent. Hard ceiling auto-pauses an agent when the limit is hit. No runaway costs.
</td>
<td align="center">
<h3>🏢 Multi-Company</h3>
One deployment, many companies. Complete data isolation. One control plane for your entire portfolio.
</td>
<td align="center">
<h3>🎫 Audit Trail</h3>
Every tool call traced. Every decision recorded. Immutable activity log across all agents and tasks.
</td>
</tr>
<tr>
<td align="center">
<h3>🛡️ Board Governance</h3>
You're the board. Approve hires, override strategy, pause or terminate any agent — at any time, from any view.
</td>
<td align="center">
<h3>📊 Org Chart</h3>
Hierarchies, roles, reporting lines. Your agents have a boss, a title, and a job description.
</td>
<td align="center">
<h3>🧩 Plugin System</h3>
Extend the core with new adapter types, knowledge bases, custom tracing, and UI components — no core changes needed.
</td>
</tr>
</table>

<br/>

## Problems Paperclip solves

| Without Paperclip | With Paperclip |
| --- | --- |
| ❌ 20 Claude Code tabs open — you can't track which one does what. On reboot you lose everything. | ✅ Tasks are ticket-based, conversations are threaded, sessions persist across reboots. |
| ❌ You manually gather context from several places to remind your bot what you're actually building. | ✅ Context flows from the task up through the project and company goals — agents always know what to do and why. |
| ❌ Agent configs are disorganized and you're reinventing task management, coordination, and communication from scratch. | ✅ Org charts, ticketing, delegation, and governance out of the box — run a company, not a pile of scripts. |
| ❌ Runaway loops waste hundreds of dollars before you notice. | ✅ Cost tracking and hard budget ceilings throttle agents automatically. |
| ❌ Recurring jobs require manual kicks: support, social, reports. | ✅ Scheduled heartbeats handle regular work, with management supervision. |
| ❌ You have an idea but need to find your repo, fire up Claude Code, and babysit it. | ✅ Add a task in Paperclip — your coding agent works it autonomously until it's done. |

<br/>

## Quickstart

Open source. Self-hosted. No account required.

```bash
npx paperclipai onboard --yes
```

This runs the interactive setup wizard, creates a local config, and starts the server. If you already have Paperclip configured, rerunning `onboard` preserves your existing config. Use `paperclipai configure` to change settings.

**Or clone and run:**

```bash
git clone https://github.com/paperclipai/paperclip.git
cd paperclip
pnpm install
pnpm dev
```

API server starts at `http://localhost:3100`. An embedded PostgreSQL instance is created automatically — no database setup required.

> **Requirements:** Node.js 20+, pnpm 9.15+

<br/>

## Architecture overview

```
┌─────────────────────────────────────────────────────┐
│                   Paperclip Server                  │
│  (TypeScript + Express, REST API on :3100)          │
│                                                     │
│   Companies → Agents → Issues → Heartbeats          │
│   Org chart · Budgets · Approvals · Activity log    │
└────────────────────┬────────────────────────────────┘
                     │ REST API
        ┌────────────┴─────────────┐
        │                          │
┌───────▼───────┐         ┌────────▼────────┐
│  Board UI     │         │   AI Agents     │
│  (React/Vite) │         │  (any adapter)  │
│  :5173 dev    │         │  OpenClaw,      │
│               │         │  Claude Code,   │
└───────────────┘         │  Codex, HTTP…   │
                          └─────────────────┘
        │ PostgreSQL (embedded or external)
┌───────▼───────────────────────────────────┐
│  ~/.paperclip/instances/default/db/       │
│  (Drizzle ORM, auto-migrated on startup)  │
└───────────────────────────────────────────┘
```

**Key packages:**

| Package | Description |
| --- | --- |
| `server/` | REST API, auth, heartbeat scheduler, services |
| `ui/` | Board operator React UI |
| `packages/db/` | Drizzle schema, migrations, DB client |
| `packages/shared/` | Shared API types, validators, constants |
| `packages/adapters/` | Built-in adapter implementations |
| `cli/` | `paperclipai` CLI (onboard, configure, heartbeat) |

<br/>

## Development

```bash
pnpm dev              # Full dev (API + UI, watch mode)
pnpm dev:once         # Full dev without file watching
pnpm dev:server       # Server only
pnpm dev:ui           # UI only
pnpm build            # Build all packages
pnpm typecheck        # Type check all packages
pnpm test:run         # Run test suite
pnpm db:generate      # Generate a new DB migration
pnpm db:migrate       # Apply pending migrations
```

See [doc/DEVELOPING.md](doc/DEVELOPING.md) for the full development guide.

<br/>

## Deploying

| Mode | Setup | Use case |
| --- | --- | --- |
| `local_trusted` | `pnpm dev` (no login) | Local machine — single operator, localhost only |
| `authenticated` (private) | Login required | Private network (Tailscale/VPN/LAN) |
| `authenticated` (public) | Login + explicit public URL | Internet-facing cloud deployment |

See [doc/DEPLOYMENT-MODES.md](doc/DEPLOYMENT-MODES.md) and [doc/DOCKER.md](doc/DOCKER.md) for full deployment instructions.

<br/>

## Agent adapters

| Adapter | Mechanism |
| --- | --- |
| `process` | Spawn a local child process |
| `http` | POST to a webhook endpoint |
| `opencode_local` | Local OpenCode (e.g. OpenClaw) session |
| `claude_local` | Local Claude Code process |
| `codex_local` | Local Codex CLI process |
| `cursor` | Cursor API/CLI bridge |
| `openclaw_gateway` | Managed OpenClaw via gateway API |

The minimum contract to be a Paperclip agent: **be callable**. Richer integration (cost reporting, status updates, task CRUD) is optional and progressive.

<br/>

### Using local Ollama models with `opencode_local`

The `opencode_local` adapter supports routing LLM calls to a local [Ollama](https://ollama.com) instance. Set the `OPENCODE_E2E_LLM_URL` env entry in the agent's `adapter_config` to point OpenCode at your local endpoint:

```jsonc
{
  "adapter_type": "opencode_local",
  "adapter_config": {
    "model": "ollama/ceo-agent",
    "env": {
      "OPENCODE_E2E_LLM_URL": { "type": "plain", "value": "http://localhost:11435/v1" },
      "PAPERCLIP_API_KEY":    { "type": "plain", "value": "<agent-api-key>" }
    }
  }
}
```

**Smart proxy** — small Ollama models (e.g. `llama3.2:3b`) often emit tool calls as plain text rather than structured JSON. `scripts/smart_ollama_proxy.py` sits between OpenCode and Ollama on port 11435 and normalises three common text formats into proper SSE `tool_calls` chunks. Start it before running any `opencode_local` agent that uses Ollama:

```bash
# Start proxy (persists across heartbeat runs)
python3 ~/paperclip/scripts/smart_ollama_proxy.py >> /tmp/proxy.log 2>&1 &

# Verify it is running
curl -s http://localhost:11435/v1/models | python3 -m json.tool
```

The proxy transparently forwards all other requests to the real Ollama API at `http://localhost:11434`.

<br/>

## Plugin system

```bash
paperclipai plugin install <package>
```

Plugins can register new adapter types, hook into lifecycle events, contribute UI components, and add background jobs. See [adapter-plugin.md](adapter-plugin.md) for authoring docs.

Browse community plugins at [awesome-paperclip](https://github.com/gsxdsm/awesome-paperclip).

<br/>

## FAQ

**What's the difference between Paperclip and OpenClaw/Claude Code?**
Paperclip *uses* those agents. It orchestrates them into a company — with org charts, budgets, goals, governance, and accountability.

**Can I run multiple companies?**
Yes. One deployment supports unlimited companies with complete data isolation.

**What happens when an agent crashes mid-task?**
Paperclip surfaces stale tasks in the dashboard — it does not auto-reassign them. Recovery is explicit. Visible failures beat silent fixes.

**Do agents run continuously?**
Agents run on scheduled heartbeats and event triggers (task assignment, @-mentions). Continuous runtimes like OpenClaw connect via the `openclaw_gateway` adapter.

<br/>

## Telemetry

Telemetry is **enabled by default**. To disable:

| Method | How |
| --- | --- |
| Environment variable | `PAPERCLIP_TELEMETRY_DISABLED=1` |
| Standard convention | `DO_NOT_TRACK=1` |
| CI environments | Auto-disabled when `CI=true` |
| Config file | `telemetry.enabled: false` |

<br/>

## Roadmap

- ✅ Plugin system
- ✅ OpenClaw / claw-style agent employees
- ✅ Company import/export
- ✅ AGENTS.md configuration
- ✅ Skills Manager
- ✅ Scheduled Routines
- ✅ Budget controls
- ⚪ Artifacts & Deployments
- ⚪ CEO Chat
- ⚪ MAXIMIZER MODE
- ⚪ Multiple Human Users
- ⚪ Cloud / Sandbox agents
- ⚪ Cloud deployments
- ⚪ Desktop App

<br/>

## Contributing

We welcome contributions. See the [contributing guide](CONTRIBUTING.md) for details.

## Community

- [Discord](https://discord.gg/m4HZY7xNG3)
- [GitHub Issues](https://github.com/paperclipai/paperclip/issues)
- [GitHub Discussions](https://github.com/paperclipai/paperclip/discussions)

## License

MIT &copy; 2026 Paperclip

## Star History

[![Star History Chart](https://api.star-history.com/image?repos=paperclipai/paperclip&type=date&legend=top-left)](https://www.star-history.com/?repos=paperclipai%2Fpaperclip&type=date&legend=top-left)

<br/>

---

<p align="center">
  <img src="doc/assets/footer.jpg" alt="" width="720" />
</p>

<p align="center">
  <sub>Open source under MIT. Built for people who want to run companies, not babysit agents.</sub>
</p>
