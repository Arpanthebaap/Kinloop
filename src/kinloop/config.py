"""Central configuration for Kinloop.

Everything cost-sensitive lives here so it's easy to audit in one place
before a deployment. Defaults are deliberately the cheapest viable option —
see docs/text_description.md for the reasoning.
"""

import os

# --- Model ---------------------------------------------------------------
# Amazon Nova Lite is the default: it is inexpensive, fast, and more than
# capable of the structured, tool-calling reasoning Kinloop's agents do.
# Override with KINLOOP_MODEL_ID if you want to try a different Bedrock model.
BEDROCK_MODEL_ID = os.environ.get(
    "KINLOOP_MODEL_ID", "amazon.nova-lite-v1:0"
)
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# --- Data store ------------------------------------------------------------
# "local" = JSON files on disk (default, zero AWS cost, used for the demo).
# "dynamodb" = swap in the DynamoDB-backed store for a real deployment.
DATA_BACKEND = os.environ.get("KINLOOP_DATA_BACKEND", "local")
LOCAL_DATA_DIR = os.environ.get(
    "KINLOOP_DATA_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "sample_data"),
)
DYNAMODB_TABLE_PREFIX = os.environ.get("KINLOOP_TABLE_PREFIX", "kinloop")

# --- Notifications -----------------------------------------------------
# "console" = print to stdout / write to the activity log (default, free,
#             used for local runs and the demo).
# "ses"      = send real email via Amazon SES (requires a verified identity).
# "slack"    = post to a Slack incoming webhook (set KINLOOP_SLACK_WEBHOOK_URL).
NOTIFY_CHANNEL = os.environ.get("KINLOOP_NOTIFY_CHANNEL", "console")
SLACK_WEBHOOK_URL = os.environ.get("KINLOOP_SLACK_WEBHOOK_URL", "")
SES_SENDER = os.environ.get("KINLOOP_SES_SENDER", "")

# --- Safety rails ----------------------------------------------------------
# Hard ceiling on how many sub-agent calls the Supervisor may make in a
# single run. Prevents a reasoning loop from silently burning tokens/money.
MAX_SUB_AGENT_CALLS_PER_RUN = int(os.environ.get("KINLOOP_MAX_CALLS", "8"))
