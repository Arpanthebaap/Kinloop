"""MedAgent — specialist agent for medication refill tracking.

Wrapped with @tool so the Supervisor can call it as part of the
Agents-as-Tools pattern (see supervisor.py).
"""

from strands import Agent, tool

from kinloop.config import BEDROCK_MODEL_ID
from kinloop.tools.med_tools import check_refill_status, draft_refill_message, log_med_action

SYSTEM_PROMPT = """You are MedAgent, a focused specialist inside the Kinloop
caregiving system. Your only job is medication refills.

Each run:
1. Call check_refill_status to see every tracked medication.
2. For anything "overdue" or "warning", call draft_refill_message to prepare
   the refill request.
3. Call log_med_action with a one- or two-sentence summary of what you found
   and did.
4. Reply with a short structured summary the Supervisor can use to decide
   whether this needs to be escalated to a human (overdue medications should
   generally be escalated; "warning" status usually does not need to
   interrupt anyone yet).

Be concise. You are not a chatbot — you are a background process. Never ask
the user a question; decide and act, or report why you couldn't."""


@tool
def med_agent(request: str) -> str:
    """Specialist for medication refill tracking: checks refill status for
    every tracked medication and drafts refill requests for anything
    overdue or running low."""
    agent = Agent(
        model=BEDROCK_MODEL_ID,
        system_prompt=SYSTEM_PROMPT,
        tools=[check_refill_status, draft_refill_message, log_med_action],
    )
    result = agent(request)
    return str(result)
