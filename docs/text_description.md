# Kinloop — text description

*(This is the submission text description required by the hackathon rules:
what it does, who it's for, and how it works.)*

## What it does

Kinloop is an autonomous agent that manages the day-to-day coordination
burden of family caregiving. Every day, unattended, it:

1. Checks every tracked medication for a shared care recipient and flags —
   or auto-drafts a refill request for — anything overdue or running low.
2. Scans the family's shared appointment calendar for scheduling conflicts:
   a family member double-booked as a driver, or an appointment with nobody
   assigned to take the patient. It proposes a fix using who else is free.
3. Tracks recurring paperwork deadlines (insurance recertification, benefit
   renewals) and flags what's missing before it's too late.
4. Decides — deliberately, as its own dedicated step — which of the above
   is routine (silently logged) versus a genuine decision that needs a
   human, and only notifies a family member for the latter.

A good day for Kinloop is a quiet one: everything routine gets handled or
logged, and the family only hears from it when something actually needs
their judgment.

## Who it's for

Families sharing caregiving duties for an aging parent or a relative with a
chronic condition — typically 2–5 people (adult children, a spouse,
in-laws) spread across different households, which is exactly the
situation where information gets lost between people. In the US alone,
roughly 1 in 5 adults is currently providing unpaid care to a family
member, most of it exactly this kind of fragmented, repetitive
coordination work: medications, appointments, and paperwork.

## Why it matters

Every existing tool in this space — shared calendars, caregiving apps like
CareZone or Lotsa Helping Hands — is a **passive tracker**. A human still
has to open it, read it, and reconcile what's happening across three
different domains (meds, appointments, paperwork) and three different
people's schedules. None of them *act*. That's the actual gap: this is a
background-agent problem, not an app problem, and it hasn't been built as
one. Kinloop is built to run unattended and only interrupt a human for
genuine decisions — which is also the literal design brief of this
hackathon's "Everyday Agents" track.

## How it works

Kinloop is built with the Strands Agents SDK using the **Agents-as-Tools**
multi-agent pattern: a Supervisor agent delegates to four specialist agents
(MedAgent, ApptAgent, PaperworkAgent, NotifierAgent), each with its own
system prompt and tools, called as tools themselves from the Supervisor.
NotifierAgent is a deliberately separate agent — a dedicated escalation
gatekeeper — rather than folding that decision into each specialist, so
"should a human be interrupted" is made once, consistently, by comparing
findings across all three domains together.

Deterministic logic (is a refill overdue, do two appointments conflict, is
a deadline urgent) is implemented as plain, unit-tested Python functions
that the Strands `@tool` decorator exposes to the agent loop — the LLM
reasons about *what to do* with that information (draft a message, decide
who to escalate to, phrase a notification), not about arithmetic on dates.

**Runtime:** AWS Lambda, invoked once daily by EventBridge Scheduler,
backed by DynamoDB and Amazon Bedrock (Amazon Nova Lite, on-demand). A
Strands `BeforeToolCallEvent` hook enforces a hard ceiling on how many
sub-agent calls the Supervisor can make per run, as a cost safety measure
independent of prompting.

**Why not Bedrock AgentCore Runtime for the always-on path:** AgentCore's
Runtime, Memory, Gateway, and Observability components bill independently
and have essentially no free tier beyond a new account's general credit —
and Observability specifically is uncapped, with idle-session memory
accrual as a documented common source of surprise bills. For a background
agent that runs for seconds once a day, Lambda + EventBridge is both
cheaper and safer: near-permanent AWS free tier, and zero cost while idle.
Kinloop still demonstrates AgentCore Runtime deployment (`deploy/agentcore/`)
as a one-time, intentionally torn-down deployment, showing the same agent
code running on AgentCore without being the production path.
