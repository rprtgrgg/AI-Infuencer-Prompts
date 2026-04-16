#!/usr/bin/env python3
"""
Tool: search_trending.py
Purpose: Search X (Twitter) for trending visual content relevant to Nova Linh's niche.
Returns a structured trending reference for use in prompt generation.

Usage:
  python tools/search_trending.py
  python tools/search_trending.py --query "travel girl aesthetic" --count 10
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
CLAUDE_API_KEY  = os.getenv("CLAUDE_API_KEY")

# Default search queries for Nova's niche
DEFAULT_QUERIES = [
    "travel girl golden hour -is:retweet has:media lang:en",
    "aesthetic girl travel -is:retweet has:media lang:en min_faves:500",
    "ai influencer girl -is:retweet has:media lang:en min_faves:200",
    "bali girl photography -is:retweet has:media lang:en min_faves:300",
    "tokyo night fashion girl -is:retweet has:media lang:en min_faves:400",
]

# ── X API Search ──────────────────────────────────────────────
def search_x_trends(query: str, count: int = 10) -> list[dict]:
    """Search X API v2 for trending posts matching query."""
    if not X_BEARER_TOKEN:
        print("[WARN] X_BEARER_TOKEN not set. Using fallback trend data.")
        return get_fallback_trends()

    url = "https://api.twitter.com/2/tweets/search/recent"
    headers = {"Authorization": f"Bearer {X_BEARER_TOKEN}"}
    params = {
        "query": query,
        "max_results": min(count, 100),
        "tweet.fields": "public_metrics,created_at,author_id,entities",
        "expansions": "attachments.media_keys",
        "media.fields": "url,preview_image_url,type",
        "sort_order": "relevancy",
    }

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        tweets = data.get("data", [])

        results = []
        for tweet in tweets:
            metrics = tweet.get("public_metrics", {})
            results.append({
                "id": tweet.get("id"),
                "text": tweet.get("text", ""),
                "likes": metrics.get("like_count", 0),
                "replies": metrics.get("reply_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "created_at": tweet.get("created_at", ""),
                "engagement_score": (
                    metrics.get("like_count", 0) * 1 +
                    metrics.get("reply_count", 0) * 3 +   # replies = hot debate
                    metrics.get("retweet_count", 0) * 2
                ),
            })

        # Sort by engagement score
        results.sort(key=lambda x: x["engagement_score"], reverse=True)
        return results

    except requests.exceptions.HTTPError as e:
        if resp.status_code == 429:
            print("[ERROR] X API rate limit hit. Using fallback trends.")
            return get_fallback_trends()
        print(f"[ERROR] X API HTTP error: {e}")
        return get_fallback_trends()
    except Exception as e:
        print(f"[ERROR] X API error: {e}")
        return get_fallback_trends()


def get_fallback_trends() -> list[dict]:
    """Hardcoded fallback when X API is unavailable. Update weekly."""
    return [
        {
            "text": "Golden hour travel photography is dominating the algorithm this week. Beach and terrace shots with warm backlight getting 4-6x more engagement.",
            "likes": 5000, "replies": 200, "retweets": 1500,
            "engagement_score": 8500, "source": "fallback"
        },
        {
            "text": "Tokyo night walks with neon reflections on wet streets are consistently viral. The aesthetic is 'cyberpunk meets candid travel vlog'.",
            "likes": 8000, "replies": 400, "retweets": 2000,
            "engagement_score": 14000, "source": "fallback"
        },
        {
            "text": "Philippines travel content getting massive engagement from both local and diaspora audiences. Palawan and Siargao performing especially well.",
            "likes": 6000, "replies": 600, "retweets": 1800,
            "engagement_score": 13600, "source": "fallback"
        },
    ]


# ── Analyze with Claude ───────────────────────────────────────
def analyze_trends_with_claude(trends: list[dict]) -> str:
    """Use Claude to synthesize trends into an actionable reference summary."""
    if not CLAUDE_API_KEY:
        # Simple fallback: just take the top trend text
        if trends:
            top = trends[0]
            return f"Top trending: {top.get('text', '')[:200]}. Engagement score: {top.get('engagement_score', 0)}."
        return "No trend data available."

    trend_texts = "\n".join([
        f"- [{t.get('likes',0)} likes, {t.get('replies',0)} replies] {t.get('text','')[:200]}"
        for t in trends[:5]
    ])

    prompt = f"""You are analyzing trending content on X (Twitter) to identify the best visual concept for an AI influencer post today.

Top trending posts (sorted by engagement):
{trend_texts}

The AI influencer is Nova Linh: 24yo Vietnamese-Filipino girl, travel/lifestyle niche, cute+sexy+editorial aesthetic.

In 2-3 sentences, summarize:
1. What visual trend is performing best today
2. Why it's getting engagement (emotional hook, seasonal relevance, etc.)
3. What location or aesthetic concept Nova should use today

Be specific and actionable. No fluff."""

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
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"].strip()
    except Exception as e:
        print(f"[WARN] Claude analysis failed: {e}. Using raw trend data.")
        return trends[0].get("text", "")[:300] if trends else ""


# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Search X for trending content for Nova Linh")
    parser.add_argument("--query", type=str, default=None, help="Custom search query")
    parser.add_argument("--count", type=int, default=10, help="Number of results to fetch")
    parser.add_argument("--output", type=str, default=".tmp/trending_reference.json", help="Output file path")
    args = parser.parse_args()

    print(f"[INFO] Searching X for trending content... [{datetime.now().strftime('%Y-%m-%d %H:%M')}]")

    all_results = []
    queries = [args.query] if args.query else DEFAULT_QUERIES[:3]  # Limit to 3 to save API quota

    for q in queries:
        print(f"[INFO] Query: {q}")
        results = search_x_trends(q, args.count)
        all_results.extend(results)

    # Deduplicate and sort by engagement
    seen = set()
    unique_results = []
    for r in all_results:
        key = r.get("id") or r.get("text", "")[:50]
        if key not in seen:
            seen.add(key)
            unique_results.append(r)
    unique_results.sort(key=lambda x: x.get("engagement_score", 0), reverse=True)

    print(f"[INFO] Found {len(unique_results)} unique trending posts.")
    print("[INFO] Analyzing trends with Claude...")

    trending_summary = analyze_trends_with_claude(unique_results[:5])
    print(f"\n[TREND SUMMARY]\n{trending_summary}\n")

    # Save output
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    output = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "trending_reference": trending_summary,
        "raw_results": unique_results[:10],
    }
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"[INFO] Saved to {args.output}")
    return trending_summary


if __name__ == "__main__":
    result = main()
    sys.exit(0)
