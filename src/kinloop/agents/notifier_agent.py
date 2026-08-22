"""NotifierAgent — the escalation gatekeeper.

This is the agent responsible for Kinloop's core promise: only interrupt a
human when there's a real decision to make. It receives the Supervisor's
consolidated findings and decides, item by item, whether something is
routine (goes to the log only) or a genuine decision (gets pushed out).
"""

from strands import Agent, tool

from kinloop.config import BEDROCK_MODEL_ID
from kinloop.tools.notify_tools import send_notification

SYSTEM_PROMPT = """You are NotifierAgent, the escalation gatekeeper inside
the Kinloop caregiving system. You receive a summary of findings from the
other specialist agents (medications, appointments, paperwork) and decide,
for each one, whether it is:

- ROUTINE: normal status, nothing changed, or something you can already see
  was fully resolved automatically. Do NOT notify anyone for these — call
  send_notification with requires_decision=False (or skip it entirely if
  there is truly nothing worth logging).
- A REAL DECISION: something where a human genuinely has to choose between
  options, or where information only a human has (e.g. a signature, a
  personal preference, availability) is required to proceed. For these,
  call send_notification with requires_decision=True, addressed to the most
  relevant family member if you can tell who that is, with a message that
  states the situation AND the options you've already worked out — never
  just "something needs attention," always give them a starting point.

Be conservative about interrupting people. A good day for Kinloop is one
where nothing gets escalated because everything was routine or already
resolved. Reply with a one-paragraph summary of what you escalated (if
anything) and why."""


@tool
def notifier_agent(request: str) -> str:
    """Specialist that decides which findings from other agents are routine
    (log only) versus genuine decisions that need to reach a human, and
    sends the notification for the latter."""
    agent = Agent(
        model=BEDROCK_MODEL_ID,
        system_prompt=SYSTEM_PROMPT,
        tools=[send_notification],
    )
    result = agent(request)
    return str(result)
