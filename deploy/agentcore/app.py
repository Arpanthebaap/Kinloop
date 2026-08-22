"""OPTIONAL: Amazon Bedrock AgentCore Runtime entrypoint.

This is not part of Kinloop's always-on deployment (that's Lambda +
EventBridge — see /deploy/template.yaml and docs/text_description.md for
why). This file exists so you can demonstrate AgentCore Runtime deployment
for the demo video / Technical Implementation score, then tear it down.

Usage (from repo root, with the bedrock-agentcore-starter-toolkit installed):

    pip install bedrock-agentcore bedrock-agentcore-starter-toolkit
    cd deploy/agentcore
    agentcore configure --entrypoint app.py
    agentcore launch
    agentcore invoke '{"prompt": "Run today'"'"'s Kinloop check-in for the family."}'

    # IMPORTANT — tear it down right after capturing your demo footage:
    agentcore destroy

AgentCore Runtime, Memory, Gateway, and Observability all bill separately
and have no meaningful free tier beyond your account's general credit — see
docs/text_description.md. Do not leave this deployed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from kinloop.agents.supervisor import run_daily_check

app = BedrockAgentCoreApp()


@app.entrypoint
def agent_invocation(payload, context):
    note = payload.get("prompt", "") if isinstance(payload, dict) else ""
    summary = run_daily_check(context_note=note)
    return {"result": summary}


if __name__ == "__main__":
    app.run()
