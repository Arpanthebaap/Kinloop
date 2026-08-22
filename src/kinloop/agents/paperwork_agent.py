"""PaperworkAgent — specialist agent for benefit/insurance paperwork
deadlines and required-document tracking."""

from strands import Agent, tool

from kinloop.config import BEDROCK_MODEL_ID
from kinloop.tools.paperwork_tools import check_deadline, extract_form_fields, log_paperwork_action

SYSTEM_PROMPT = """You are PaperworkAgent, a focused specialist inside the
Kinloop caregiving system. Your only job is tracking recurring paperwork
deadlines — insurance recertification, Medicaid/benefit renewals, and
similar — and flagging what's missing before it's too late.

Each run:
1. Call check_deadline to see every tracked deadline.
2. For anything "urgent" or "missed", note exactly what's still needed
   (use extract_form_fields if document text is provided in the request).
3. Call log_paperwork_action with a short summary.
4. Reply with a short structured summary. A deadline going from ok to
   urgent, or any missed deadline, should always be flagged as needing a
   human decision — these often require a signature or personal
   information only a family member can provide.

Be concise. You are not a chatbot — you are a background process. Never ask
the user a question; decide and act, or report why you couldn't."""


@tool
def paperwork_agent(request: str) -> str:
    """Specialist for paperwork/benefit deadline tracking: checks recurring
    deadlines and flags missing required fields on documents."""
    agent = Agent(
        model=BEDROCK_MODEL_ID,
        system_prompt=SYSTEM_PROMPT,
        tools=[check_deadline, extract_form_fields, log_paperwork_action],
    )
    result = agent(request)
    return str(result)
