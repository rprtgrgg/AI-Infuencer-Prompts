#!/usr/bin/env python3
"""
Tool: update_website.py
Purpose: Add a new post to posts.json and push to GitHub (triggers Netlify auto-deploy).

Usage:
  python tools/update_website.py
  python tools/update_website.py --post-file .tmp/new_post.json
  python tools/update_website.py --post-file .tmp/new_post.json --dry-run
"""

import os
import sys
import json
import base64
import argparse
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN  = os.getenv("GITHUB_TOKEN")
GITHUB_REPO   = os.getenv("GITHUB_REPO")   # e.g. "yourusername/nova-linh-website"
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

POSTS_FILE_PATH = "content/posts.json"   # Path inside the GitHub repo


# ── GitHub API helpers ────────────────────────────────────────
def gh_get_file(path: str) -> tuple[str, str]:
    """Get file content and SHA from GitHub. Returns (content_str, sha)."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH}, timeout=15)
    if resp.status_code == 404:
        return "", ""
    resp.raise_for_status()
    data = resp.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def gh_put_file(path: str, content: str, sha: str, message: str) -> bool:
    """Create or update a file in GitHub. Returns True on success."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, json=payload, timeout=30)
    if resp.status_code in (200, 201):
        return True
    print(f"[ERROR] GitHub API error {resp.status_code}: {resp.text[:300]}")
    return False


def gh_upload_image(local_path: str, repo_path: str) -> bool:
    """Upload a binary file (image/video) to GitHub."""
    if not os.path.exists(local_path):
        print(f"[WARN] Image file not found: {local_path}")
        return False

    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{repo_path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Check if file already exists (need SHA)
    check = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH}, timeout=10)
    sha = check.json().get("sha", "") if check.status_code == 200 else ""

    payload = {
        "message": f"Upload image: {os.path.basename(local_path)}",
        "content": content_b64,
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, json=payload, timeout=60)
    if resp.status_code in (200, 201):
        # Return the raw GitHub CDN URL
        cdn_url = resp.json().get("content", {}).get("download_url", "")
        print(f"[INFO] Image uploaded: {cdn_url}")
        return cdn_url
    print(f"[ERROR] Image upload failed {resp.status_code}: {resp.text[:200]}")
    return False


# ── Update posts.json ─────────────────────────────────────────
def prepend_post_to_json(new_post: dict, dry_run: bool = False) -> bool:
    """Fetch posts.json from GitHub, prepend new post, push back."""
    print(f"[INFO] Fetching {POSTS_FILE_PATH} from GitHub...")
    current_content, sha = gh_get_file(POSTS_FILE_PATH)

    if current_content:
        try:
            data = json.loads(current_content)
        except json.JSONDecodeError:
            print("[ERROR] posts.json on GitHub is malformed.")
            return False
    else:
        # First time — create fresh structure
        data = {
            "last_updated": "",
            "influencer": {
                "name": "Nova Linh",
                "persona": "24-year-old Vietnamese-Filipino AI model.",
                "handle": "@novalinhofficial"
            },
            "posts": []
        }

    # Prepend new post (newest first)
    posts = data.get("posts", [])

    # Avoid duplicates
    if any(p.get("id") == new_post.get("id") for p in posts):
        print(f"[WARN] Post {new_post['id']} already exists. Skipping.")
        return False

    posts.insert(0, new_post)
    data["posts"] = posts
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    updated_json = json.dumps(data, indent=2, ensure_ascii=False)

    if dry_run:
        print("[DRY RUN] Would push the following posts.json:")
        print(updated_json[:500] + "...")
        return True

    commit_msg = f"[Nova] Add post: {new_post.get('title', 'new post')} ({datetime.now().strftime('%Y-%m-%d')})"
    success = gh_put_file(POSTS_FILE_PATH, updated_json, sha, commit_msg)

    if success:
        print(f"[SUCCESS] posts.json updated on GitHub.")
        print(f"[INFO] Netlify will auto-deploy in ~60 seconds.")
        print(f"[INFO] View at: https://YOUR-NETLIFY-URL.netlify.app")
    return success


# ── Main ──────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Update Nova Linh website with new post")
    parser.add_argument("--post-file", type=str, default=".tmp/new_post.json", help="Path to new post JSON")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without pushing")
    parser.add_argument("--upload-image", action="store_true", default=True, help="Upload local image to GitHub")
    args = parser.parse_args()

    # Validate env
    if not args.dry_run:
        if not GITHUB_TOKEN:
            print("[ERROR] GITHUB_TOKEN not set in .env")
            print("[INFO] Create a token at: GitHub → Settings → Developer settings → Personal access tokens")
            print("[INFO] Required scopes: repo (full control)")
            sys.exit(1)
        if not GITHUB_REPO:
            print("[ERROR] GITHUB_REPO not set in .env (e.g. 'yourusername/nova-linh-website')")
            sys.exit(1)

    # Load post
    try:
        with open(args.post_file) as f:
            new_post = json.load(f)
    except FileNotFoundError:
        print(f"[ERROR] Post file not found: {args.post_file}")
        print("[INFO] Run generate_prompt.py and generate_image.py first.")
        sys.exit(1)

    print(f"[INFO] Publishing: {new_post.get('title')}")
    print(f"[INFO] Platform: {new_post.get('platform')} | Type: {new_post.get('type')}")

    # Upload image to GitHub if local path
    local_image = new_post.get("image", "")
    if args.upload_image and local_image and os.path.exists(local_image) and not args.dry_run:
        repo_image_path = local_image.replace("\\", "/")  # Normalize path
        cdn_url = gh_upload_image(local_image, repo_image_path)
        if cdn_url:
            new_post["image"] = cdn_url

    # Push posts.json update
    success = prepend_post_to_json(new_post, dry_run=args.dry_run)

    if success and not args.dry_run:
        print(f"\n[DONE] Post published: {new_post.get('title')}")
        print(f"[INFO] ID: {new_post.get('id')}")
    elif not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
