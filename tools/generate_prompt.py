#!/usr/bin/env python3
"""
Tool: generate_prompt.py
Purpose: Use Claude to generate a high-engagement AI image/video prompt for Nova Linh.
Reads trending reference from search_trending.py output and returns a structured post object.

Usage:
  python tools/generate_prompt.py
  python tools/generate_prompt.py --reference "Tokyo neon aesthetic is trending" --platform "Kling AI"
  python tools/generate_prompt.py --trending-file .tmp/trending_reference.json
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# ── Nova's Persona ────────────────────────────────────────────
NOVA_PERSONA = """
Influencer: Nova Linh
Age: 24
Ethnicity: Vietnamese-Filipino mix (Southeast Asian features, warm medium skin tone, dark hair)
Body: Petite but curvaceous — cute and sexy
Vibe: Travel-obsessed, effortlessly stylish, candid and real-feeling
Typical content: Golden hour travel portraits, fashion moments in iconic locations, aesthetic lifestyle shots
Goal: Content that looks like a real influencer took it — NOT obviously AI-generated
"""

PLATFORM_TIPS = {
    "Freepik Mystic": "Best for still images. Add '8K, ultra-realistic, photographic quality' at the end. Avoid complex multi-person scenes.",
    "Kling AI": "Best for short video clips. Describe motion explicitly (e.g., 'she slowly turns', 'hair blowing in wind'). Keep scenes simple — one character, clear action.",
    "Higgsfield": "Specializes in cinematic motion. Add 'cinematic camera movement', 'rack focus', 'slow push-in'. Great for landscape + character combos.",
    "Other": "Standard diffusion model. Use common quality enhancers: 'best quality, masterpiece, ultra-detailed'.",
}

# ── Generate prompt via Claude ────────────────────────────────
def generate_post_prompt(trending_reference: str, platform: str, post_id: str) -> dict:
    """Call Claude API to generate a structured post object."""
    if not CLAUDE_API_KEY:
        print("[ERROR] CLAUDE_API_KEY not set in .env")
        sys.exit(1)

    platform_tip = PLATFORM_TIPS.get(platform, PLATFORM_TIPS["Other"])
    today = datetime.now().strftime("%Y-%m-%d")

    system_prompt = f"""You are an expert AI image/video prompt engineer. You create viral content prompts for AI influencers.

Your job: Generate ONE perfect AI generation prompt for Nova Linh based on today's trending visual content.

{NOVA_PERSONA}

Platform-specific tips for {platform}:
{platform_tip}

Rules for the prompt:
1. Be hyper-specific: include location name, exact outfit description, lighting direction, camera specs
2. Make Nova feel REAL: use candid directions ("laughs genuinely", "glances back", "lost in thought")
3. Avoid AI tells: no glowing eyes, no perfect symmetry descriptions, no "beautiful woman" generic phrases
4. Include film/photography references: "shot on 85mm f/1.4", "Leica M", "iPhone 15 Pro", "analog film"
5. End with quality enhancers appropriate for the platform
6. For videos: describe specific motion (what she does, how camera moves)

Return ONLY a valid JSON object with this exact structure:
{{
  "id": "{post_id}",
  "date": "{today}",
  "title": "5-7 word evocative title",
  "platform": "{platform}",
  "type": "image or video",
  "image": "",
  "prompt": "the full detailed prompt here",
  "tags": ["tag1", "tag2", "tag3", "tag4"],
  "trending_reference": "1-2 sentence summary of what's trending and why",
  "notes": "1-2 sentence tip for using this prompt effectively"
}}"""

    user_message = f"""Today's trending reference:
{trending_reference}

Generate the best possible Nova Linh post for {platform} based on this trend. Make it highly likely to go viral."""

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_message}],
            },
            timeout=45,
        )
        resp.raise_for_status()
        raw_text = resp.json()["content"][0]["text"].strip()

        # Parse JSON from response
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        post_obj = json.loads(raw_text)
        return post_obj

    except json.JSONDecodeError as e:
        print(f"[ERROR] Claude returned invalid JSON: {e}")
        print(f"[DEBUG] Raw response: {raw_text[:500]}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Claude API call failed: {e}")
        sys.exit(1)


# ── Get next post ID ──────────────────────────────────────────
def get_next_post_id(posts_file: str = "content/posts.json") -> str:
    """Read posts.json and return the next incremented post ID."""
    try:
        with open(posts_file) as f:
            data = json.load(f)
        posts = data.get("posts", [])
        if not posts:
            return "post-001"
        # Extract max numeric ID
        ids = []
        for p in posts:
            try:
                num = int(p["id"].replace("post-", ""))
                ids.append(num)
            except (ValueError, KeyError):
                pass
        next_num = max(ids) + 1 if ids else 1
        return f"post-{next_num:03d}"
    except FileNotFoundError:
        return "post-001"


# ── Platform selection ────────────────────────────────────────
def auto_select_platform(post_num: int) -> str:
    """Rotate platforms to ensure variety in the feed."""
    rotation = ["Freepik Mystic", "Kling AI", "Freepik Mystic", "Higgsfield", "Freepik Mystic", "Kling AI"]
    return rotation[post_num % len(rotation)]


# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate a Nova Linh post prompt using Claude")
    parser.add_argument("--reference", type=str, default=None, help="Trending reference text")
    parser.add_argument("--trending-file", type=str, default=".tmp/trending_reference.json", help="Path to trending reference JSON")
    parser.add_argument("--platform", type=str, default=None, help="Target platform (Freepik Mystic, Kling AI, Higgsfield)")
    parser.add_argument("--output", type=str, default=".tmp/new_post.json", help="Output file path")
    args = parser.parse_args()

    # Load trending reference
    trending_reference = args.reference
    if not trending_reference:
        try:
            with open(args.trending_file) as f:
                trend_data = json.load(f)
            trending_reference = trend_data.get("trending_reference", "")
            print(f"[INFO] Loaded trending reference from {args.trending_file}")
        except FileNotFoundError:
            print(f"[WARN] No trending file found at {args.trending_file}. Using generic reference.")
            trending_reference = "Travel and lifestyle content with golden hour aesthetics is consistently high-performing. Focus on authentic, candid moments in iconic Asian or European destinations."

    # Get next post ID
    post_id = get_next_post_id()
    post_num = int(post_id.replace("post-", ""))

    # Select platform
    platform = args.platform or auto_select_platform(post_num)

    print(f"[INFO] Generating prompt for post {post_id} on {platform}...")
    print(f"[INFO] Trending reference: {trending_reference[:100]}...")

    # Generate
    post_obj = generate_post_prompt(trending_reference, platform, post_id)

    # Save
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(post_obj, f, indent=2)

    print(f"\n[SUCCESS] Generated post: {post_obj.get('title')}")
    print(f"[INFO] Platform: {post_obj.get('platform')}")
    print(f"[INFO] Type: {post_obj.get('type')}")
    print(f"\n[PROMPT PREVIEW]\n{post_obj.get('prompt', '')[:300]}...\n")
    print(f"[INFO] Saved to {args.output}")

    return post_obj


if __name__ == "__main__":
    result = main()
    sys.exit(0)
