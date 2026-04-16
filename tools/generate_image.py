#!/usr/bin/env python3
"""
Tool: generate_image.py
Purpose: Generate an AI image using Freepik Mystic API (or Higgsfield).
Reads the new_post.json from generate_prompt.py and downloads the generated image.

Usage:
  python tools/generate_image.py
  python tools/generate_image.py --post-file .tmp/new_post.json --platform freepik
"""

import os
import sys
import json
import time
import argparse
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

FREEPIK_API_KEY   = os.getenv("FREEPIK_API_KEY")
HIGGSFIELD_API_KEY = os.getenv("HIGGSFIELD_API_KEY")

# ── Freepik Mystic ────────────────────────────────────────────
def generate_freepik(prompt: str, post_id: str) -> str:
    """
    Generate image via Freepik Mystic API.
    Returns: local file path of downloaded image.

    Freepik API docs: https://freepik.com/api/mystic
    Endpoint: POST https://api.freepik.com/v1/ai/text-to-image
    """
    if not FREEPIK_API_KEY:
        print("[ERROR] FREEPIK_API_KEY not set in .env")
        print("[INFO] Get your API key at: https://freepik.com/api")
        sys.exit(1)

    url = "https://api.freepik.com/v1/ai/text-to-image"
    headers = {
        "x-freepik-api-key": FREEPIK_API_KEY,
        "Content-Type": "application/json",
        "Accept-Language": "en-US",
    }
    payload = {
        "prompt": prompt,
        "negative_prompt": "ugly, deformed, extra fingers, distorted face, blurry, low quality, watermark, text, logo, frame, border, artificial look, plastic skin, glowing eyes",
        "guidance_scale": 7,
        "num_inference_steps": 30,
        "aspect_ratio": "portrait_4_5",  # Perfect for Instagram/social
        "image": {
            "size": "portrait_4_5"
        },
        "styling": {
            "style": "photo",
            "color": "warm",
            "lighting": "warm",
        }
    }

    print(f"[INFO] Sending prompt to Freepik Mystic API...")
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        # Freepik returns a task_id for async generation
        task_id = data.get("data", {}).get("task_id") or data.get("task_id")
        if task_id:
            return poll_freepik_task(task_id, post_id)

        # Some endpoints return direct image URL
        image_url = data.get("data", [{}])[0].get("url") if isinstance(data.get("data"), list) else None
        if image_url:
            return download_image(image_url, post_id, "freepik")

        print(f"[ERROR] Unexpected Freepik response: {json.dumps(data)[:300]}")
        sys.exit(1)

    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] Freepik API error {resp.status_code}: {e}")
        if resp.status_code == 429:
            print("[INFO] Rate limited. Try again in 1 hour or use the Freepik web interface.")
        sys.exit(1)


def poll_freepik_task(task_id: str, post_id: str, max_wait: int = 120) -> str:
    """Poll Freepik for async task completion."""
    url = f"https://api.freepik.com/v1/ai/text-to-image/{task_id}"
    headers = {"x-freepik-api-key": FREEPIK_API_KEY}

    print(f"[INFO] Waiting for Freepik to generate image (task: {task_id})...")
    for attempt in range(max_wait // 5):
        time.sleep(5)
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()
        status = data.get("data", {}).get("status") or data.get("status")

        if status == "completed":
            image_url = (
                data.get("data", {}).get("generated", [{}])[0].get("url") or
                data.get("data", {}).get("url")
            )
            if image_url:
                print(f"[INFO] Generation complete!")
                return download_image(image_url, post_id, "freepik")
        elif status == "failed":
            print(f"[ERROR] Freepik generation failed: {data}")
            sys.exit(1)
        else:
            print(f"[INFO] Status: {status} (attempt {attempt+1})")

    print("[ERROR] Timed out waiting for Freepik.")
    sys.exit(1)


# ── Higgsfield ────────────────────────────────────────────────
def generate_higgsfield(prompt: str, post_id: str) -> str:
    """
    Generate video via Higgsfield API.
    Returns: local file path of downloaded video.
    """
    if not HIGGSFIELD_API_KEY:
        print("[ERROR] HIGGSFIELD_API_KEY not set in .env")
        print("[INFO] Sign up at: https://higgsfield.ai")
        sys.exit(1)

    url = "https://api.higgsfield.ai/v1/generation/text-to-video"
    headers = {
        "Authorization": f"Bearer {HIGGSFIELD_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "prompt": prompt,
        "duration": 5,         # 5 seconds
        "aspect_ratio": "9:16", # Vertical for Reels/TikTok
        "motion_strength": 0.7,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        generation_id = data.get("id") or data.get("generation_id")
        if generation_id:
            return poll_higgsfield_generation(generation_id, post_id)

        print(f"[ERROR] Unexpected Higgsfield response: {data}")
        sys.exit(1)

    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] Higgsfield API error {resp.status_code}: {e}")
        sys.exit(1)


def poll_higgsfield_generation(generation_id: str, post_id: str, max_wait: int = 300) -> str:
    """Poll Higgsfield for video generation completion."""
    url = f"https://api.higgsfield.ai/v1/generation/{generation_id}"
    headers = {"Authorization": f"Bearer {HIGGSFIELD_API_KEY}"}

    print(f"[INFO] Waiting for Higgsfield video (ID: {generation_id})... This can take 2-5 minutes.")
    for attempt in range(max_wait // 10):
        time.sleep(10)
        resp = requests.get(url, headers=headers, timeout=15)
        data = resp.json()
        status = data.get("status")

        if status == "completed":
            video_url = data.get("video_url") or data.get("output", {}).get("url")
            if video_url:
                return download_image(video_url, post_id, "higgsfield", ext="mp4")
        elif status in ("failed", "error"):
            print(f"[ERROR] Higgsfield generation failed: {data}")
            sys.exit(1)
        else:
            print(f"[INFO] Status: {status} (attempt {attempt+1}/{max_wait//10})")

    print("[ERROR] Timed out waiting for Higgsfield.")
    sys.exit(1)


# ── Download helper ───────────────────────────────────────────
def download_image(url: str, post_id: str, source: str, ext: str = "jpg") -> str:
    """Download image/video from URL to assets/images/ folder."""
    filename = f"{post_id}-{source}.{ext}"
    output_path = os.path.join("assets", "images", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"[INFO] Downloading to {output_path}...")
    resp = requests.get(url, stream=True, timeout=60)
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    size_kb = os.path.getsize(output_path) // 1024
    print(f"[INFO] Downloaded {size_kb}KB → {output_path}")
    return output_path


# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate AI image/video for Nova Linh post")
    parser.add_argument("--post-file", type=str, default=".tmp/new_post.json", help="Post JSON file from generate_prompt.py")
    parser.add_argument("--platform", type=str, default=None, help="Override platform (freepik/higgsfield/kling)")
    args = parser.parse_args()

    # Load post data
    try:
        with open(args.post_file) as f:
            post = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Post file not found: {args.post_file}")
        print("[INFO] Run generate_prompt.py first.")
        sys.exit(1)

    prompt   = post.get("prompt", "")
    post_id  = post.get("id", "post-000")
    platform = args.platform or post.get("platform", "Freepik Mystic")

    if not prompt:
        print("[ERROR] No prompt found in post file.")
        sys.exit(1)

    print(f"[INFO] Generating content for: {post.get('title')}")
    print(f"[INFO] Platform: {platform}")
    print(f"[INFO] Type: {post.get('type', 'image')}")

    # Route to correct generator
    platform_lower = platform.lower()
    if "freepik" in platform_lower:
        local_path = generate_freepik(prompt, post_id)
    elif "higgsfield" in platform_lower:
        local_path = generate_higgsfield(prompt, post_id)
    elif "kling" in platform_lower:
        print("[WARN] Kling AI does not have a public API yet.")
        print("[ACTION] Manual step required:")
        print(f"  1. Go to https://klingai.com")
        print(f"  2. Paste this prompt:\n\n{prompt}\n")
        print(f"  3. Download the video and save as: assets/images/{post_id}-kling.mp4")
        print(f"  4. Update '{args.post_file}' → set 'image' to 'assets/images/{post_id}-kling.mp4'")
        sys.exit(0)
    else:
        print(f"[WARN] Unknown platform '{platform}'. Trying Freepik as fallback.")
        local_path = generate_freepik(prompt, post_id)

    # Update post file with local path
    post["image"] = local_path
    with open(args.post_file, "w") as f:
        json.dump(post, f, indent=2)

    print(f"\n[SUCCESS] Image saved: {local_path}")
    print(f"[INFO] Updated post file with image path.")


if __name__ == "__main__":
    main()
