# Deploying Kinloop

This guide is written to be handed to an AI coding agent (e.g. Google
Antigravity) along with this repo — every step is a literal command. Do
steps 1–3 yourself in the AWS Console first (they involve clicking "I
agree" on billing things no agent should do on your behalf); everything
after that can be delegated.

## 0. Before anything else — cost safety

1. **Set a Budget alert manually first**, before deploying anything:
   AWS Console → Billing and Cost Management → Budgets → Create budget →
   Monthly cost budget → set $20 (or your comfort level) → add your email
   at 50%/80%/100% thresholds. (The SAM template also creates one
   automatically at deploy time — this manual one is your immediate
   safety net while you're still setting things up.)
2. **Request the hackathon's $50 AWS credit** using the form linked in the
   official rules — due **Sept 11, 12pm PT**. Don't leave this to the last
   day.
3. **Enable Bedrock model access** for Amazon Nova Lite (and Nova Micro, as
   a fallback) in the Bedrock console → Model access → Manage model access,
   in whichever region you plan to deploy (default: us-east-1). This is a
   one-time approval per account/region and is free.

## 1. Local test run (no AWS deployment yet, minimal cost)

```bash
git clone <your-repo-url>
cd kinloop
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export AWS_REGION=us-east-1   # wherever you enabled Bedrock model access
python -m kinloop.main
```

This runs one full Kinloop cycle against the sample data in `sample_data/`,
using your local AWS credentials for Bedrock only (no Lambda, no DynamoDB —
the local JSON backend is used). Expect it to cost a few cents at most with
Nova Lite. Check `sample_data/activity_log.json` and
`sample_data/pending_decisions.json` afterward, or open
`dashboard/index.html` in a browser.

Run the (free, no AWS calls) unit tests too:

```bash
pip install pytest
pytest tests/
```

## 2. Deploy the real thing (Lambda + EventBridge + DynamoDB)

Requires the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).

```bash
cd deploy
sam build --template-file template.yaml
sam deploy --guided \
  --template-file template.yaml \
  --stack-name kinloop \
  --parameter-overrides BudgetAlertEmail=you@example.com MonthlyBudgetLimitUSD=20 \
  --capabilities CAPABILITY_IAM
```

`sam deploy --guided` will ask a handful of questions (region, confirm
changeset, etc.) — accept the defaults except region, which should match
where you enabled Bedrock model access.

Then seed the tables with the sample family data:

```bash
python seed_dynamodb.py --region us-east-1
```

Test it manually before waiting for the daily schedule:

```bash
aws lambda invoke --function-name kinloop-daily-run --payload '{}' out.json
cat out.json
```

## 3. (Optional, for the demo video only) AgentCore Runtime

See `deploy/agentcore/app.py` for a one-time AgentCore Runtime deployment
you can capture on camera and then **immediately tear down** with
`agentcore destroy`. This is not the always-on deployment — see
`docs/text_description.md` for why.

## 4. Tear down when you're done

```bash
cd deploy
sam delete --stack-name kinloop
```

This removes the Lambda, EventBridge schedule, and DynamoDB tables. Double
check the AWS Console billing dashboard afterward to confirm nothing is
still running.
