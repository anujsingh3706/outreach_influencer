"""
Project runner for the Automated Micro-Influencer Outreach System.

This executes:
  1) Discovery + enrichment
  2) Message personalization
  3) Sending layer in dry-run mode (safe simulation)
"""

import os
import sys

from scripts.part1_discovery_enrichment import run_discovery_and_enrichment
from scripts.part2_message_personalization import run_message_generation
from scripts.part3_sending_layer import run_outreach


def resolve_raw_data_path(base_dir):
    candidates = [
        os.path.join(base_dir, "data", "influencer_raw.json"),
        os.path.join(base_dir, "data", "influencers_raw.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("No raw influencer dataset found in data/")


def main():
    # Ensure Windows terminals can print Unicode status symbols safely.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    raw_path = resolve_raw_data_path(base_dir)

    run_discovery_and_enrichment(raw_path, output_dir)
    enriched_path = os.path.join(output_dir, "enriched_influencers.json")
    run_message_generation(enriched_path, output_dir)
    messages_path = os.path.join(output_dir, "outreach_messages.json")
    run_outreach(messages_path, send_email=True, send_dm=True)


if __name__ == "__main__":
    main()
