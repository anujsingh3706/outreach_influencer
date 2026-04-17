import csv
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import streamlit as st


ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "output"
DATA_DIR = ROOT_DIR / "data"


def read_json(path: Path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_csv(path: Path):
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ensure_outputs_exist():
    required = [
        OUTPUT_DIR / "enriched_influencers.json",
        OUTPUT_DIR / "outreach_messages.json",
        OUTPUT_DIR / "delivery_log.csv",
    ]
    return all(p.exists() for p in required)


def run_pipeline():
    command = [sys.executable, "main.py"]
    result = subprocess.run(
        command,
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return result.returncode, result.stdout, result.stderr


def render_metrics(enriched, messages, delivery):
    total = len(enriched)
    micro = sum(1 for x in enriched if str(x.get("is_micro_influencer", "")).lower() == "true" or x.get("is_micro_influencer") is True)
    avg_er = round(sum(float(x.get("engagement_rate", 0)) for x in enriched) / total, 2) if total else 0
    platform_counts = Counter(x.get("platform", "Unknown") for x in enriched)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Influencers discovered", total)
    c2.metric("Micro-influencers", micro)
    c3.metric("Avg engagement rate", f"{avg_er}%")
    c4.metric("Messages generated", len(messages))

    st.write("**Platform split:**", dict(platform_counts))
    st.write("**Outreach actions (simulation):**", len(delivery))


def render_assignment_mapping():
    st.subheader("Assignment 4 Checklist Mapping")
    st.markdown(
        """
- **Task 1: Influencer Discovery** -> `data/influencer_raw.json` with 50 Indian fitness creators.
- **Task 2: Filtering / Classification** -> Segment files:
  - `output/segment_A_instagram_high_engagement.csv`
  - `output/segment_B_youtube_educators.csv`
  - `output/segment_C_top_brand_fit.csv`
- **Task 3: Profile Enrichment** -> `output/enriched_influencers.json` and `.csv`
- **Task 4: Message Personalization** -> `output/outreach_messages.json` and `.csv`
- **Task 5: Sending Layer** -> `scripts/part3_sending_layer.py` + `output/delivery_log.csv` (dry-run simulation)
        """
    )


def render_workflow_diagram():
    st.subheader("End-to-End Workflow")
    st.markdown(
        """
```text
Raw influencer dataset (50 records)
        |
        v
Part 1: Discovery + Enrichment
  - Engagement rate
  - Follower tier
  - Brand fit score
  - Segment files (A/B/C)
        |
        v
Part 2: Personalization Engine
  - Collaboration type selection
  - Personalized email (niche + recent content + value)
  - Personalized DM
        |
        v
Part 3: Sending Layer (Demo)
  - Email channel flow (SendGrid API structure)
  - Instagram DM flow (Meta Graph API structure)
  - Delivery log + status tracking
```
        """
    )


def render_discovery_tab(enriched, segment_a, segment_b, segment_c):
    st.subheader("Part 1 - Discovery, Enrichment, and Segmentation")
    st.write("Enriched influencers preview:")
    st.dataframe(enriched[:15], use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Segment A (Instagram High ER)", len(segment_a))
    c2.metric("Segment B (YouTube Educators)", len(segment_b))
    c3.metric("Segment C (Top Brand Fit)", len(segment_c))

    st.caption("This section proves discovery + filtering + enrichment requirements.")


def render_message_tab(messages):
    st.subheader("Part 2 - Personalized Email + DM")
    if not messages:
        st.warning("No generated messages found yet.")
        return

    influencer_names = [f"{m['name']} (@{m['username']})" for m in messages]
    selected = st.selectbox("Pick influencer to explain personalization", influencer_names, index=0)
    chosen = messages[influencer_names.index(selected)]

    st.write("**Collaboration type:**", chosen.get("collab_type", "N/A"))
    st.write("**Email subject:**", chosen.get("email_subject", "N/A"))
    st.text_area("Email body", value=chosen.get("email_body", ""), height=230)
    st.text_area("Instagram DM", value=chosen.get("dm_message", ""), height=90)
    st.write(
        f"Email word count: **{chosen.get('email_word_count', 0)}** | "
        f"DM word count: **{chosen.get('dm_word_count', 0)}**"
    )
    st.caption("Use this live in demo to explain how templates become personalized outreach.")


def render_sending_tab(delivery, logs):
    st.subheader("Part 3 - Sending Layer Simulation (No Real API Calls)")
    st.info(
        "This assignment demo runs in DRY RUN mode. It shows the API integration workflow "
        "without sending real emails/DMs."
    )

    status_counts = Counter(d.get("status", "unknown") for d in delivery)
    channel_counts = Counter(d.get("channel", "unknown") for d in delivery)

    c1, c2, c3 = st.columns(3)
    c1.metric("Total delivery actions", len(delivery))
    c2.metric("Simulated", status_counts.get("simulated", 0))
    c3.metric("Failed", status_counts.get("failed", 0))

    st.write("**By channel:**", dict(channel_counts))
    st.write("**By status:**", dict(status_counts))

    st.write("Recent delivery logs:")
    st.dataframe(delivery[-20:], use_container_width=True)

    st.write("Execution logs:")
    st.text_area("outreach_log.txt", value=logs, height=300)


def render_api_explanation():
    st.subheader("API Integration Explanation (What would happen in live mode)")
    st.markdown(
        """
### Email channel (SendGrid)
1. Build payload with `to`, `subject`, `body`, tracking settings.
2. Send `POST` request to SendGrid mail endpoint.
3. Track HTTP response and save status in delivery logs.

### Instagram DM channel (Meta Graph API)
1. Resolve Instagram user ID from username.
2. Send message payload to messages endpoint.
3. Track success/failure and store in logs.

### Credentials needed for live mode
- `SENDGRID_API_KEY`
- `FROM_EMAIL`
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_BUSINESS_ACCOUNT_ID`

For assignment demo, keep **DRY_RUN=True** and explain the full flow without real sending.
        """
    )


def main():
    st.set_page_config(page_title="Assignment 4 - Influencer Outreach", layout="wide")
    st.title("Assignment 4: Automated Micro-Influencer Outreach System")
    st.caption("Demo dashboard to explain full workflow using sample data (no production API sending).")

    with st.sidebar:
        st.header("Controls")
        if st.button("Run Full Pipeline", use_container_width=True):
            with st.spinner("Running main.py pipeline..."):
                code, out, err = run_pipeline()
            if code == 0:
                st.success("Pipeline finished successfully.")
            else:
                st.error(f"Pipeline failed with exit code: {code}")
            st.text_area("Pipeline stdout", out, height=220)
            if err.strip():
                st.text_area("Pipeline stderr", err, height=140)

        st.markdown("---")
        st.write("Use this app during presentation to explain each stage.")

    if not ensure_outputs_exist():
        st.warning("Output files not found yet. Click 'Run Full Pipeline' in sidebar first.")
        return

    enriched = read_json(OUTPUT_DIR / "enriched_influencers.json")
    messages = read_json(OUTPUT_DIR / "outreach_messages.json")
    segment_a = read_csv(OUTPUT_DIR / "segment_A_instagram_high_engagement.csv")
    segment_b = read_csv(OUTPUT_DIR / "segment_B_youtube_educators.csv")
    segment_c = read_csv(OUTPUT_DIR / "segment_C_top_brand_fit.csv")
    delivery = read_csv(OUTPUT_DIR / "delivery_log.csv")

    log_path = OUTPUT_DIR / "outreach_log.txt"
    logs = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""

    render_metrics(enriched, messages, delivery)
    st.markdown("---")
    render_assignment_mapping()
    render_workflow_diagram()
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Discovery + Segments", "Personalized Messages", "Sending Simulation", "API Workflow"]
    )
    with tab1:
        render_discovery_tab(enriched, segment_a, segment_b, segment_c)
    with tab2:
        render_message_tab(messages)
    with tab3:
        render_sending_tab(delivery, logs)
    with tab4:
        render_api_explanation()


if __name__ == "__main__":
    main()
