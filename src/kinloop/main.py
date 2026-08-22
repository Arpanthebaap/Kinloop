"""Local entry point — run one Kinloop daily cycle from the command line.

    python -m kinloop.main
    python -m kinloop.main --note "check in on the Medicaid renewal specifically"

Requires AWS credentials with Bedrock model access configured in your
environment (see README.md). Uses the local JSON data backend by default,
so this costs only the Bedrock token spend for one run — a few cents at
most with Nova Lite.
"""

import argparse

from kinloop.agents.supervisor import run_daily_check


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Kinloop daily cycle.")
    parser.add_argument("--note", default="", help="Optional extra context for this run.")
    args = parser.parse_args()

    print("Running Kinloop daily check-in...\n")
    summary = run_daily_check(context_note=args.note)
    print("\n--- Supervisor summary ---")
    print(summary)
    print("\nSee sample_data/activity_log.json and sample_data/pending_decisions.json "
          "for the full trail (or open dashboard/index.html).")


if __name__ == "__main__":
    main()
