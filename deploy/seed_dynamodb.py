"""Seed the DynamoDB tables (created by template.yaml) with the sample
family data, so the deployed Lambda has something to work with.

Run once after `sam deploy`:

    python deploy/seed_dynamodb.py --region us-east-1

Requires AWS credentials in your environment. Uses only PutItem calls
against the on-demand tables created in template.yaml — negligible cost
(DynamoDB on-demand write is fractions of a cent for this volume).
"""

import argparse
import json
import os

import boto3

HERE = os.path.dirname(os.path.abspath(__file__))
SAMPLE_DIR = os.path.join(os.path.dirname(HERE), "sample_data")

TABLE_MAP = {
    "medications": ("kinloop_medications", "name"),
    "appointments": ("kinloop_appointments", "title"),
    "deadlines": ("kinloop_deadlines", "name"),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--region", default=os.environ.get("AWS_REGION", "us-east-1"))
    args = parser.parse_args()

    ddb = boto3.resource("dynamodb", region_name=args.region)

    for collection, (table_name, key) in TABLE_MAP.items():
        path = os.path.join(SAMPLE_DIR, f"{collection}.json")
        with open(path) as f:
            items = json.load(f)
        table = ddb.Table(table_name)
        with table.batch_writer() as batch:
            for item in items:
                # DynamoDB doesn't accept None for a non-key attribute in
                # some SDK paths — drop null "driver" fields instead.
                clean = {k: v for k, v in item.items() if v is not None}
                batch.put_item(Item=clean)
        print(f"Seeded {len(items)} items into {table_name}")


if __name__ == "__main__":
    main()
