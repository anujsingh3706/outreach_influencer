"""
==============================================================
PART 2: MESSAGE PERSONALIZATION ENGINE
Generates personalized Email & Instagram DM outreach
Assignment 4 - Automated Micro-Influencer Outreach System
==============================================================
"""

import json
import csv
import os
import random
from datetime import datetime


# ─────────────────────────────────────────────
# MESSAGE TEMPLATE LIBRARY
# Multiple variants per collaboration type
# ─────────────────────────────────────────────

EMAIL_TEMPLATES = {
    "paid_sponsorship": [
        """Hi {name},

I came across your {platform} profile @{username} and was genuinely impressed by your {sub_niche} content — especially your recent post on "{recent_post}". Your {engagement_quality} engagement rate of {engagement_rate}% speaks volumes about the trust your {followers_formatted} followers place in you.

We're {brand_name}, a {brand_desc}. We'd love to explore a paid sponsorship collaboration with you — featuring our product in your {content_style} content. The campaign would include {collab_detail}.

Would you be open to a quick 15-minute call this week?

Warm regards,
{sender_name}
{brand_name} | Influencer Partnerships""",

        """Dear {name},

Your passion for {sub_niche} truly shines through your content at @{username}! Posts like "{recent_post}" perfectly capture the authentic, relatable style our brand values.

{brand_name} is launching a new fitness campaign and we believe you'd be the perfect face for it. We're offering a paid sponsorship that fits seamlessly with your {content_style} approach, with full creative freedom for you.

Compensation details and a complete brief are ready to share. Can we connect?

Best,
{sender_name}
Partnerships Team, {brand_name}"""
    ],

    "affiliate": [
        """Hi {name},

Loved your recent content on "{recent_post}" — it's exactly the kind of authentic {sub_niche} content that resonates with real fitness enthusiasts. With your {followers_formatted} followers and {engagement_rate}% engagement, you clearly have a highly engaged community.

{brand_name} is inviting select Indian fitness creators to join our affiliate program — earn {commission}% commission on every sale you drive. No rigid scripts, just honest recommendations aligned with your content style.

Interested? I'd love to send over our full affiliate kit.

Cheers,
{sender_name}
{brand_name} Affiliate Program""",
    ],

    "ugc": [
        """Hello {name},

We've been following your {sub_niche} journey on @{username} and love how your recent post "{recent_post}" perfectly blends {content_style}. Your creative eye for fitness content is exactly what we need.

{brand_name} is looking for UGC creators to produce authentic review content for our new product line. You keep full creative control — we just need your honest, styled take on our product.

Compensation is ₹{ugc_fee} for a content pack. Would this interest you?

Looking forward to creating together,
{sender_name}
{brand_name} Content Team""",
    ],

    "brand_ambassador": [
        """Hi {name},

After following your growth in the {sub_niche} space on @{username} — especially content like "{recent_post}" — we knew you were someone we wanted to partner with long-term, not just for a single campaign.

{brand_name} is building an elite squad of Indian fitness brand ambassadors and you've made our shortlist. This is a 3–6 month partnership with monthly compensation, exclusive product access, and co-creation opportunities.

This is the real deal. Can we schedule a call to share details?

Excited to work together,
{sender_name}
Head of Brand Partnerships, {brand_name}""",
    ],

    "barter": [
        """Hi {name},

Your {sub_niche} content on @{username} is genuinely refreshing — posts like "{recent_post}" show exactly why your audience keeps coming back. We think our products would fit perfectly into your world.

As a barter collaboration, {brand_name} would send you a curated product box (worth ₹{barter_value}) in exchange for an honest review post or story feature. No brand scripts — just your authentic experience.

If this sounds good, reply and we'll get the products to you right away!

Cheers,
{sender_name}
{brand_name} Influencer Team""",
    ]
}

DM_TEMPLATES = {
    "paid_sponsorship": [
        "Hey {name}! 👋 Loved your post on \"{recent_post_short}\". We'd love to collab with {brand_name} — paid campaign, full creative freedom. DM or email us? 🙌",
        "Hi {name}! Your {sub_niche} content is 🔥 We're {brand_name} — exploring a paid collab with you. Interested? Check your email too! 💪",
    ],
    "affiliate": [
        "Hey {name}! Love your {sub_niche} vibe. {brand_name} has an affiliate program built for creators like you — ₹ on every sale! Interested? 🚀",
        "Hi {name} 💪 Your fitness content is amazing! We'd love to have you as a {brand_name} affiliate. Earn commission sharing products you'd actually use!",
    ],
    "ugc": [
        "Hey {name}! We're {brand_name} 👋 We'd love a UGC collab — your creative style is perfect for our new launch. Paid opportunity. Open to chatting? ✨",
        "Hi {name}! Loved \"{recent_post_short}\" 🙌 {brand_name} is looking for UGC creators for our fitness line. Paid + free product. Interested? 🎯",
    ],
    "brand_ambassador": [
        "Hey {name}! 🌟 {brand_name} is building our ambassador squad & you're on our shortlist! Long-term paid partnership. Can we chat? 💪🔥",
        "Hi {name}! We've been following your {sub_niche} journey 👀 {brand_name} wants YOU as a brand ambassador. Long-term, paid, exciting. DM back! 🚀",
    ],
    "barter": [
        "Hey {name}! 👋 Love your {sub_niche} content! We'd love to send you a {brand_name} product box (₹{barter_value} worth) for an honest review. Interested? 🎁",
        "Hi {name}! {brand_name} here 🙏 Big fan of your content! Barter collab — premium products for honest posts. Would love to connect! ✨",
    ]
}


# ─────────────────────────────────────────────
# BRAND CONFIGURATION
# (Configurable per campaign)
# ─────────────────────────────────────────────

BRAND_CONFIG = {
    "brand_name": "FitFuel India",
    "brand_desc": "homegrown Indian sports nutrition & fitness gear brand",
    "sender_name": "Ayesha Kapoor",
    "commission": "15",
    "ugc_fee": "8,000",
    "barter_value": "3,500",
    "collab_detail": "a dedicated reel + 2 story frames with tracked affiliate link"
}


# ─────────────────────────────────────────────
# PERSONALIZATION LOGIC
# ─────────────────────────────────────────────

COLLAB_TYPE_BY_FOLLOWERS = {
    (5000, 25000): "barter",
    (25001, 50000): "affiliate",
    (50001, 75000): "ugc",
    (75001, 100000): "paid_sponsorship",
}

AMBASSADOR_CANDIDATES_MIN_SCORE = 8  # brand_fit_score threshold


def pick_collab_type(inf):
    """Auto-assign collaboration type based on profile"""
    if inf.get('brand_fit_score', 0) >= AMBASSADOR_CANDIDATES_MIN_SCORE:
        return "brand_ambassador"
    followers = inf['followers']
    for (low, high), ctype in COLLAB_TYPE_BY_FOLLOWERS.items():
        if low <= followers <= high:
            return ctype
    return "paid_sponsorship"


def format_followers(n):
    if n >= 1000:
        return f"{n/1000:.1f}K"
    return str(n)


def get_content_style(sub_niche):
    styles = {
        "Calisthenics": "raw, motivational bodyweight",
        "Yoga & Wellness": "calming, educational wellness",
        "Strength Training": "informative, science-backed strength",
        "Running & Endurance": "energetic, community-driven running",
        "HIIT & Fat Loss": "high-energy, transformation-focused",
        "Dance Fitness & Zumba": "fun, vibrant dance",
        "Home Workout & No Equipment": "accessible, beginner-friendly home",
        "Women's Strength & Empowerment": "empowering, confidence-building",
        "Fitness Nutrition & Meal Prep": "educational, recipe-driven nutrition",
        "Natural Bodybuilding": "authentic, transformation-driven bodybuilding",
    }
    return styles.get(sub_niche, "engaging, community-first fitness")


def personalize_email(inf):
    collab_type = pick_collab_type(inf)
    templates = EMAIL_TEMPLATES[collab_type]
    template = random.choice(templates)

    recent_post = inf['recent_content'][0] if inf['recent_content'] else "your latest content"

    variables = {
        **BRAND_CONFIG,
        "name": inf['name'].split()[0],
        "username": inf['username'],
        "platform": inf['platform'],
        "sub_niche": inf['sub_niche'],
        "niche": inf['niche'],
        "followers_formatted": format_followers(inf['followers']),
        "engagement_rate": str(inf['engagement_rate']),
        "engagement_quality": inf['engagement_quality'].lower(),
        "recent_post": recent_post,
        "content_style": get_content_style(inf['sub_niche']),
        "location": inf['location'],
    }

    message = template.format(**variables)
    subject = generate_subject(inf, collab_type)

    return {
        "collab_type": collab_type,
        "subject": subject,
        "body": message
    }


def generate_subject(inf, collab_type):
    name = inf['name'].split()[0]
    subjects = {
        "paid_sponsorship": f"Paid Collab Opportunity for @{inf['username']} 🎯",
        "affiliate": f"Earn with {BRAND_CONFIG['brand_name']} — Affiliate Invite for {name} 💰",
        "ugc": f"UGC Creator Opportunity — {name}, we want YOUR content 🎬",
        "brand_ambassador": f"You're on Our Shortlist, {name} 🌟 Brand Ambassador Invite",
        "barter": f"Free Product + Collab for @{inf['username']} 🎁",
    }
    return subjects.get(collab_type, f"Collaboration Opportunity — {BRAND_CONFIG['brand_name']}")


def personalize_dm(inf):
    collab_type = pick_collab_type(inf)
    templates = DM_TEMPLATES[collab_type]
    template = random.choice(templates)

    recent_post = inf['recent_content'][0] if inf['recent_content'] else "your latest video"
    # Shorten for DM
    recent_post_short = recent_post[:40] + "..." if len(recent_post) > 40 else recent_post

    variables = {
        **BRAND_CONFIG,
        "name": inf['name'].split()[0],
        "username": inf['username'],
        "sub_niche": inf['sub_niche'],
        "recent_post_short": recent_post_short,
    }

    message = template.format(**variables)

    # Validate DM word count (15–30 words)
    word_count = len(message.split())

    return {
        "collab_type": collab_type,
        "dm_message": message,
        "word_count": word_count
    }


# ─────────────────────────────────────────────
# BATCH MESSAGE GENERATION
# ─────────────────────────────────────────────

def generate_all_messages(enriched_influencers):
    results = []
    for inf in enriched_influencers:
        if not inf.get('is_micro_influencer', False):
            continue

        email_data = personalize_email(inf)
        dm_data = personalize_dm(inf)

        result = {
            "id": inf['id'],
            "name": inf['name'],
            "username": inf['username'],
            "platform": inf['platform'],
            "email": inf['email'],
            "profile_url": inf['profile_url'],
            "followers": inf['followers'],
            "engagement_rate": inf['engagement_rate'],
            "niche": inf['niche'],
            "sub_niche": inf['sub_niche'],
            "location": inf['location'],
            "brand_fit_score": inf['brand_fit_score'],
            "collab_type": email_data['collab_type'],
            "email_subject": email_data['subject'],
            "email_body": email_data['body'],
            "dm_message": dm_data['dm_message'],
            "dm_word_count": dm_data['word_count'],
            "email_word_count": len(email_data['body'].split()),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        results.append(result)

    return results


def export_messages(messages, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Full JSON
    json_path = os.path.join(output_dir, 'outreach_messages.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, indent=2, ensure_ascii=False)
    print(f"  [OK] JSON export → {json_path}")

    # CSV (flat)
    csv_path = os.path.join(output_dir, 'outreach_messages.csv')
    if messages:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=messages[0].keys())
            writer.writeheader()
            writer.writerows(messages)
    print(f"  [OK] CSV export → {csv_path}")

    # Human-readable text dump for sample review
    txt_path = os.path.join(output_dir, 'sample_messages_readable.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=" * 65 + "\n")
        f.write("  PERSONALIZED OUTREACH MESSAGES — SAMPLE REVIEW\n")
        f.write(f"  Brand: {BRAND_CONFIG['brand_name']}\n")
        f.write(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 65 + "\n\n")

        for msg in messages[:10]:  # First 10 as samples
            f.write(f"{'─'*65}\n")
            f.write(f"INFLUENCER   : {msg['name']} (@{msg['username']})\n")
            f.write(f"Platform     : {msg['platform']} | Followers: {msg['followers']:,}\n")
            f.write(f"Engagement   : {msg['engagement_rate']}% | Brand Fit: {msg['brand_fit_score']}/10\n")
            f.write(f"Collab Type  : {msg['collab_type'].replace('_', ' ').title()}\n")
            f.write(f"Email        : {msg['email']}\n\n")
            f.write(f"📧 EMAIL ({msg['email_word_count']} words)\n")
            f.write(f"Subject: {msg['email_subject']}\n\n")
            f.write(f"{msg['email_body']}\n\n")
            f.write(f"📱 INSTAGRAM DM ({msg['dm_word_count']} words)\n")
            f.write(f"{msg['dm_message']}\n\n")

    print(f"  [OK] Readable samples → {txt_path}")
    return json_path, csv_path, txt_path


def print_message_stats(messages):
    print(f"\n{'='*55}")
    print("  MESSAGE GENERATION SUMMARY")
    print(f"{'='*55}")
    print(f"  Total messages generated : {len(messages)}")

    collab_counts = {}
    for msg in messages:
        ct = msg['collab_type']
        collab_counts[ct] = collab_counts.get(ct, 0) + 1

    print(f"\n  Collaboration Type Breakdown:")
    for ct, count in sorted(collab_counts.items(), key=lambda x: -x[1]):
        print(f"    {ct.replace('_',' ').title():<25} : {count} influencers")

    platform_counts = {}
    for msg in messages:
        p = msg['platform']
        platform_counts[p] = platform_counts.get(p, 0) + 1
    print(f"\n  Platform Breakdown:")
    for p, count in sorted(platform_counts.items()):
        print(f"    {p:<15} : {count} influencers")

    avg_er = round(sum(m['engagement_rate'] for m in messages) / len(messages), 2)
    avg_score = round(sum(m['brand_fit_score'] for m in messages) / len(messages), 1)
    print(f"\n  Avg Engagement Rate  : {avg_er}%")
    print(f"  Avg Brand Fit Score  : {avg_score}/10")
    print(f"{'='*55}")


def run_message_generation(enriched_path, output_dir):
    print("\n" + "="*55)
    print("  PART 2: MESSAGE PERSONALIZATION ENGINE")
    print("="*55)

    print("\n[1/3] Loading enriched influencer data...")
    with open(enriched_path, 'r') as f:
        enriched = json.load(f)
    print(f"  Loaded {len(enriched)} enriched profiles")

    print("\n[2/3] Generating personalized messages...")
    messages = generate_all_messages(enriched)
    print(f"  Generated {len(messages)} email + DM pairs")

    print("\n[3/3] Exporting message files...")
    export_messages(messages, output_dir)

    print_message_stats(messages)
    print(f"\n✅ Message personalization complete. Files saved to: {output_dir}/")
    return messages


if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ENRICHED_PATH = os.path.join(BASE_DIR, '..', 'output', 'enriched_influencers.json')
    OUT_DIR = os.path.join(BASE_DIR, '..', 'output')

    messages = run_message_generation(ENRICHED_PATH, OUT_DIR)
