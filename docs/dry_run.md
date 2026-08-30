# A note on AWS Bedrock access during development

Being upfront about this because the rules are explicit that a project
"must function as depicted in the video" — so if you're watching a demo
that used `--dry-run`, here's exactly why, and what that does and doesn't
prove.

## What happened

This AWS account is new, and AWS places new accounts into an extended
identity/billing verification hold that blocks Bedrock (and other
services — CloudShell included) until it clears. That process is normally
described as taking up to a day or two; in this case it ran well past
that, despite an open Support case and live chat contact. This is a
known, documented friction point for brand-new AWS accounts and isn't
specific to Kinloop's code or architecture.

## What this does NOT affect

- All unit tests (`pytest tests/`) — 10/10 passing, zero Bedrock calls,
  zero AWS dependency at all.
- The full SAM deployment (`deploy/template.yaml`) — Lambda, EventBridge,
  DynamoDB, IAM, and the budget alarm all built and deployable; the
  infrastructure itself doesn't require Bedrock access to provision.
- The architecture and multi-agent design (Supervisor + 4 specialists via
  Agents-as-Tools) — this is a code/design property, not a runtime one.

## What this DOES affect

Any invocation that actually calls a Bedrock model — which is every
specialist agent's reasoning step (drafting a refill message, phrasing a
notification, deciding between ambiguous options). Without Bedrock access,
that reasoning cannot execute, on Lambda or locally, regardless of
deployment target.

## The workaround: `--dry-run`

`python -m kinloop.main --dry-run` (see `src/kinloop/dry_run.py`) runs the
exact same deterministic logic every agent's tools are built on — refill
status, conflict detection, deadline urgency, and the same escalation
thresholds NotifierAgent uses — directly, without an LLM call, and labels
every line of output `[DRY RUN — no Bedrock call made]`. It proves the
underlying logic is real and correct (the same functions are covered by
the unit tests). It does not, and isn't presented as, a demonstration of
the agents' natural-language reasoning — that requires an actual Bedrock
call, shown separately once account access clears.

If you're able to grant this account temporary Bedrock access for
evaluation purposes, `python -m kinloop.main` (no flag) runs the real
multi-agent system end to end.
