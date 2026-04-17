"""
==============================================================
PART 1: INFLUENCER DISCOVERY & PROFILE ENRICHMENT
Assignment 4 - Automated Micro-Influencer Outreach System
Niche: Fitness | Geography: India
==============================================================
"""

import json
import csv
import math
import os
from datetime import datetime

# ─────────────────────────────────────────────
# STEP 1: LOAD RAW INFLUENCER DATA
# In production, this data is fetched from:
#   - Instagram Graph API (hashtag discovery)
#   - YouTube Data API v3
#   - Platforms: Winkl, Qoruz, One Impression
# ─────────────────────────────────────────────

def load_influencers(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)


# ─────────────────────────────────────────────
# STEP 2: PROFILE ENRICHMENT
# Adds computed fields to each influencer
# ─────────────────────────────────────────────

def calculate_engagement_rate(followers, avg_likes, avg_comments):
    """
    Engagement Rate = (Avg Likes + Avg Comments) / Followers * 100
    Industry benchmark for micro-influencers: 3%–8% is excellent.
    """
    total_engagement = avg_likes + avg_comments
    rate = (total_engagement / followers) * 100
    return round(rate, 2)


def classify_engagement(rate):
    if rate >= 6:
        return "Excellent"
    elif rate >= 4:
        return "Good"
    elif rate >= 2:
        return "Average"
    else:
        return "Low"


def classify_follower_tier(followers):
    if followers < 10000:
        return "Nano (< 10K)"
    elif followers < 50000:
        return "Micro (10K–50K)"
    elif followers <= 100000:
        return "Mid-Micro (50K–100K)"
    else:
        return "Macro (> 100K)"


def enrich_influencer(inf):
    """Adds enriched fields to influencer dict"""
    eng_rate = calculate_engagement_rate(
        inf['followers'], inf['avg_likes'], inf['avg_comments']
    )
    enriched = {
        **inf,
        "engagement_rate": eng_rate,
        "engagement_quality": classify_engagement(eng_rate),
        "follower_tier": classify_follower_tier(inf['followers']),
        "is_micro_influencer": 5000 <= inf['followers'] <= 100000,
        "estimated_reach_per_post": inf['avg_likes'] + inf['avg_comments'],
        "content_frequency": "High" if inf['posts'] > 400 else "Medium" if inf['posts'] > 200 else "Low",
        "brand_fit_score": compute_brand_fit(inf, eng_rate),
        "enriched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return enriched


def compute_brand_fit(inf, eng_rate):
    """
    Brand fit score (0–10) for a fitness brand.
    Based on: engagement rate, follower count, content frequency, location.
    """
    score = 0

    # Engagement score (max 4 pts)
    if eng_rate >= 6:
        score += 4
    elif eng_rate >= 4:
        score += 3
    elif eng_rate >= 2:
        score += 2
    else:
        score += 1

    # Follower range (max 3 pts) — sweet spot is 30K–80K for micro
    if 30000 <= inf['followers'] <= 80000:
        score += 3
    elif 10000 <= inf['followers'] < 30000 or 80000 < inf['followers'] <= 100000:
        score += 2
    else:
        score += 1

    # Content volume (max 2 pts)
    if inf['posts'] > 400:
        score += 2
    elif inf['posts'] > 200:
        score += 1

    # Multi-platform bonus (max 1 pt)
    if inf['platform'] == 'Instagram':
        score += 1  # preferred for visual fitness content

    return min(score, 10)


def enrich_all(influencers):
    return [enrich_influencer(inf) for inf in influencers]


# ─────────────────────────────────────────────
# STEP 3: FILTERING / SEGMENTATION
# Creates 3 filtered segments
# ─────────────────────────────────────────────

def filter_instagram_high_engagement(influencers):
    """
    Segment A: Instagram fitness influencers with Good/Excellent engagement
    Target: Visual campaigns, sponsored posts, reels
    """
    return [
        inf for inf in influencers
        if inf['platform'] == 'Instagram'
        and inf['engagement_quality'] in ['Good', 'Excellent']
        and inf['is_micro_influencer']
    ]


def filter_youtube_fitness_educators(influencers):
    """
    Segment B: YouTube fitness educators — tutorial/long-form content
    Target: Product reviews, sponsored tutorials, affiliate campaigns
    """
    return [
        inf for inf in influencers
        if inf['platform'] == 'YouTube'
        and inf['is_micro_influencer']
        and inf['followers'] >= 30000
    ]


def filter_top_brand_fit(influencers):
    """
    Segment C: Top brand-fit influencers across platforms (score >= 7)
    Target: Brand ambassador and UGC campaigns
    """
    return [
        inf for inf in influencers
        if inf['brand_fit_score'] >= 7
        and inf['is_micro_influencer']
    ]


# ─────────────────────────────────────────────
# STEP 4: EXPORT TO CSV
# ─────────────────────────────────────────────

def export_to_csv(data, filename, output_dir='output'):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    if not data:
        print(f"  [WARN] No data to export for {filename}")
        return

    keys = data[0].keys()
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)
    print(f"  [OK] Exported {len(data)} records → {filepath}")
    return filepath


def export_to_json(data, filename, output_dir='output'):
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  [OK] Exported JSON → {filepath}")
    return filepath


# ─────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────

def print_summary(label, data):
    print(f"\n{'='*55}")
    print(f"  Segment: {label}")
    print(f"  Total influencers: {len(data)}")
    if data:
        avg_er = round(sum(d['engagement_rate'] for d in data) / len(data), 2)
        avg_followers = int(sum(d['followers'] for d in data) / len(data))
        avg_brand = round(sum(d['brand_fit_score'] for d in data) / len(data), 1)
        print(f"  Avg Engagement Rate : {avg_er}%")
        print(f"  Avg Followers       : {avg_followers:,}")
        print(f"  Avg Brand Fit Score : {avg_brand}/10")
        platforms = {}
        for d in data:
            platforms[d['platform']] = platforms.get(d['platform'], 0) + 1
        print(f"  Platform Breakdown  : {platforms}")
    print(f"{'='*55}")


def run_discovery_and_enrichment(raw_path, output_dir):
    print("\n" + "="*55)
    print("  PART 1: INFLUENCER DISCOVERY & ENRICHMENT")
    print("="*55)

    # Load
    print("\n[1/4] Loading raw influencer data...")
    raw = load_influencers(raw_path)
    print(f"  Loaded {len(raw)} influencers from dataset")

    # Enrich
    print("\n[2/4] Enriching profiles...")
    enriched = enrich_all(raw)
    export_to_json(enriched, 'enriched_influencers.json', output_dir)
    export_to_csv(enriched, 'enriched_influencers.csv', output_dir)

    # Filter / Segment
    print("\n[3/4] Running segmentation filters...")
    seg_a = filter_instagram_high_engagement(enriched)
    seg_b = filter_youtube_fitness_educators(enriched)
    seg_c = filter_top_brand_fit(enriched)

    export_to_csv(seg_a, 'segment_A_instagram_high_engagement.csv', output_dir)
    export_to_csv(seg_b, 'segment_B_youtube_educators.csv', output_dir)
    export_to_csv(seg_c, 'segment_C_top_brand_fit.csv', output_dir)

    # Summary
    print("\n[4/4] Segment Summary Reports")
    print_summary("Segment A — Instagram High Engagement", seg_a)
    print_summary("Segment B — YouTube Fitness Educators", seg_b)
    print_summary("Segment C — Top Brand Fit (Score ≥ 7)", seg_c)

    print(f"\n✅ Discovery & Enrichment complete. Files saved to: {output_dir}/")
    return enriched, seg_a, seg_b, seg_c


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Support both legacy and current dataset filenames.
    candidate_paths = [
        os.path.join(BASE_DIR, '..', 'data', 'influencer_raw.json'),
        os.path.join(BASE_DIR, '..', 'data', 'influencers_raw.json'),
    ]
    RAW_PATH = next((p for p in candidate_paths if os.path.exists(p)), candidate_paths[0])
    OUT_DIR = os.path.join(BASE_DIR, '..', 'output')

    enriched, seg_a, seg_b, seg_c = run_discovery_and_enrichment(RAW_PATH, OUT_DIR)
