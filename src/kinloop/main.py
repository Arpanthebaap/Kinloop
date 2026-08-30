"""Local entry point — run one Kinloop daily cycle from the command line.

    python -m kinloop.main
    python -m kinloop.main --note "check in on the Medicaid renewal specifically"
    python -m kinloop.main --dry-run    # no Bedrock call — see dry_run.py

Requires AWS credentials with Bedrock model access configured in your
environment (see README.md), UNLESS run with --dry-run, which exercises
the same underlying decision logic without calling Bedrock at all — useful
if your AWS account is still in new-account verification (this is a known,
sometimes multi-day delay unrelated to Kinloop itself; see docs/dry_run.md).
Uses the local JSON data backend by default, so a real (non-dry-run) run
costs only the Bedrock token spend for one run — a few cents at most with
Nova Lite.
"""

import argparse

from kinloop.agents.supervisor import run_daily_check
from kinloop.dry_run import run_dry_run_check


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Kinloop daily cycle.")
    parser.add_argument("--note", default="", help="Optional extra context for this run.")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run the real decision logic without calling Bedrock (see dry_run.py).",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("Running Kinloop in DRY RUN mode (no Bedrock call)...\n")
        summary = run_dry_run_check()
    else:
        print("Running Kinloop daily check-in...\n")
        summary = run_daily_check(context_note=args.note)

    print("\n--- Summary ---")
    print(summary)
    print("\nSee sample_data/activity_log.json and sample_data/pending_decisions.json "
          "for the full trail (or open dashboard/index.html).")


if __name__ == "__main__":
    main()

