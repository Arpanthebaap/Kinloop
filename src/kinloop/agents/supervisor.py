"""Supervisor — the top-level orchestrator.

This is Kinloop's entry point, and the core of its "Agents-as-Tools"
architecture: the Supervisor doesn't do any domain work itself, it just
decides which specialist agents to call, in what order, and then hands
their combined findings to NotifierAgent for the escalation decision.

This is what runs once a day, triggered by EventBridge Scheduler in
production, or by hand for local testing (see main.py).
"""

from strands import Agent
from strands.hooks import BeforeToolCallEvent

from kinloop.config import BEDROCK_MODEL_ID, MAX_SUB_AGENT_CALLS_PER_RUN
from kinloop.agents.appt_agent import appt_agent
from kinloop.agents.med_agent import med_agent
from kinloop.agents.notifier_agent import notifier_agent
from kinloop.agents.paperwork_agent import paperwork_agent

SYSTEM_PROMPT = """You are the Kinloop Supervisor. You run once a day,
unattended, for a family sharing caregiving duties. Your job is to check in
with each specialist and produce one consolidated outcome for the day.

Every run:
1. Call med_agent to check medication refills.
2. Call appt_agent to check for appointment conflicts.
3. Call paperwork_agent to check paperwork/benefit deadlines.
4. Once you have all three specialists' findings, call notifier_agent
   exactly once with a consolidated summary of everything found, so it can
   decide what (if anything) needs to reach a human today.
5. Reply with a short end-of-run summary: how many things were checked,
   how many were fine, and what (if anything) got escalated.

You are a background process, not a chat assistant — there is no user
watching this run in real time. Do not ask questions. Make the best call
you can with the information available, and let NotifierAgent be the single
place where a decision to interrupt a human actually gets made."""


def _cost_guard(max_calls: int):
    """Build a hook that hard-stops the Supervisor's sub-agent calls once a
    ceiling is hit. This is a real cost control, not decoration: a reasoning
    loop that goes sideways can otherwise keep calling specialist agents
    (each of which makes its own Bedrock calls) indefinitely."""
    state = {"count": 0}

    def guard(event: BeforeToolCallEvent):
        state["count"] += 1
        if state["count"] > max_calls:
            event.cancel_tool = (
                f"Sub-agent call limit ({max_calls}) reached for this run. "
                "Wrap up with what you have so far."
            )

    return guard


def run_daily_check(context_note: str = "") -> str:
    """Run one full Kinloop daily cycle. `context_note` can carry any
    extra context for this run (e.g. 'weekly deep check' or a specific
    family member's note) — leave blank for the standard daily run."""
    agent = Agent(
        model=BEDROCK_MODEL_ID,
        system_prompt=SYSTEM_PROMPT,
        tools=[med_agent, appt_agent, paperwork_agent, notifier_agent],
        hooks=[_cost_guard(MAX_SUB_AGENT_CALLS_PER_RUN)],
    )
    prompt = "Run today's Kinloop check-in for the family." + (
        f" Additional context: {context_note}" if context_note else ""
    )
    result = agent(prompt)
    return str(result)
