# Kinloop

**An autonomous caregiving agent for families sharing care of an aging or ill relative — built with the [Strands Agents SDK](https://strandsagents.com/) for the [Agents for Humans Hackathon](https://agentsforhumans.devpost.com/) (Everyday Agents track).**

Kinloop runs quietly in the background, once a day, reconciling medication
refills, appointment scheduling across the family, and paperwork deadlines
for a shared care recipient. It only interrupts a human when there's a real
decision to make — a double-booked driver, an overdue prescription, a
paperwork deadline going urgent. Everything else it resolves or logs
silently.

> Most caregiving apps are trackers a human still has to read and reconcile.
> Kinloop is the thing that does the reconciling.

## Why

About 1 in 5 adults is an unpaid family caregiver, usually coordinating with
siblings or a spouse across different households. See
[`docs/text_description.md`](docs/text_description.md) for the full
problem statement, audience, and impact case, and
[`docs/architecture.svg`](docs/architecture.svg) for the system diagram.

## How it's built

Four Strands specialist agents, coordinated by a Supervisor using the
**Agents-as-Tools** pattern:

- **Supervisor** — runs daily, delegates to each specialist, enforces a hard
  cost ceiling on sub-agent calls via a Strands hook
- **MedAgent** — medication refill tracking
- **ApptAgent** — appointment conflict detection across family drivers/attendees
- **PaperworkAgent** — recurring benefit/insurance deadline tracking + document field extraction
- **NotifierAgent** — the escalation gatekeeper: decides what's routine (log only) vs. a genuine decision (notify a human)

```
src/kinloop/
  agents/        the 5 Strands agents (Supervisor + 4 specialists)
  tools/         @tool-decorated functions, backed by pure-Python business
                 logic that's unit tested with zero LLM/AWS calls
  data_store.py  backend-agnostic data layer (local JSON <-> DynamoDB)
  config.py      all cost-sensitive settings in one place
  main.py        local CLI entry point
  lambda_handler.py   AWS Lambda entry point (production)
sample_data/     a realistic demo family (see it trigger real decisions)
dashboard/       read-only static dashboard for the day's activity
deploy/          SAM template, DynamoDB seeding script, optional AgentCore path
docs/            architecture diagram, text description, demo video script
tests/           unit tests for the deterministic logic behind every tool
```

## Quickstart (local, costs a few cents at most)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export AWS_REGION=us-east-1   # region with Bedrock Nova model access enabled
python -m kinloop.main
```

No Bedrock access yet (e.g. a brand-new AWS account still in verification)?
Run `python -m kinloop.main --dry-run` instead — exercises the real
deterministic logic behind every tool with no LLM call. See
[`docs/dry_run.md`](docs/dry_run.md) for exactly what that does and doesn't prove.

Open `dashboard/index.html` in a browser to see the day's findings laid out
(it ships with the sample data baked in as a fallback, so it renders even
without running anything first).

Run the tests (free, no AWS calls):

```bash
pip install pytest && pytest tests/
```

## Deploying for real

See [`deploy/README.md`](deploy/README.md) — a literal, step-by-step guide
(Lambda + EventBridge + DynamoDB, deployed via AWS SAM, with a budget alarm
set up before anything else). Also covers the optional one-time AgentCore
Runtime deployment for demo purposes.

## Cost design

Bedrock AgentCore's Runtime/Memory/Observability components have real
bill-shock risk (uncapped observability charges, idle-session memory
accrual) and no meaningful free tier. Kinloop's always-on path is plain AWS
Lambda + EventBridge Scheduler instead — near-permanent AWS free tier,
and it only runs for the few seconds a day the agent actually executes.
AgentCore is demonstrated as an optional one-time deployment (see
`deploy/agentcore/`), not the production path. Full reasoning in
[`docs/text_description.md`](docs/text_description.md).

## License

MIT — see [LICENSE](LICENSE).
