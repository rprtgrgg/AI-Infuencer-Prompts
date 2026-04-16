# Workflow: Daily Prompt Research & Publishing

**Objective:** Every day, research trending visual content on X/Threads, generate a high-engagement AI prompt for Nova Linh, generate the image/video, and publish it to the website.

**Schedule:** Daily at 9:00 AM (your timezone)

**Automation:** This workflow runs in n8n. Manual fallback described in Step 5.

---

## Required Inputs
- Claude API key (for prompt generation)
- Freepik API key (for image generation)
- GitHub token (for website updates)
- X/Twitter API key (for trend research) — *optional; fallback: manual search*

## Expected Outputs
- One new entry in `content/posts.json`
- Image/video asset uploaded or linked
- Website auto-deployed via Netlify

---

## Step 1: Research Trending Visual Content

**Tool:** `tools/search_trending.py`  
**Fallback (manual):** Go to X.com and search the following:
- `filter:media min_faves:1000` (top media posts past 24h)
- Keywords: `travel girl`, `ai model`, `aesthetic`, `[city name] girl`
- Check Threads: look at Explore tab → Lifestyle/Travel

**What to look for:**
- Posts with 1K+ likes, high comment-to-like ratio (signals debate/discussion = more reach)
- Visual aesthetics that match Nova's persona: warm travel, editorial fashion, golden hour
- Locations trending in pop culture (after a big movie/show, viral travel post, etc.)
- Seasonal: beach in summer, cozy café in winter, cherry blossoms in spring

**Output:** A "trending reference" note — 1-2 sentences on what's performing and why.

**Rate limit note:** X API Free Tier is limited to 500k tweet reads/month. Query sparingly — 1 search/day max. If rate-limited, use manual fallback.

---

## Step 2: Generate the Prompt

**Tool:** `tools/generate_prompt.py`  
**Prompt sent to Claude:**

```
You are an AI image/video prompt engineer specializing in creating viral content for an AI influencer.

Influencer persona:
- Name: Nova Linh
- Age: 24
- Ethnicity: Vietnamese-Filipino mix
- Vibe: Cute but sexy, travel-obsessed, editorial but candid
- Typical content: Travel destinations, golden hour portraits, fashion moments, lifestyle shots

Today's trending reference:
[INSERT TRENDING REFERENCE HERE]

Target platform: [Freepik Mystic / Kling AI / Higgsfield]

Generate ONE highly detailed AI generation prompt that:
1. Fits Nova's persona perfectly
2. Is likely to generate a viral, high-engagement image/video
3. Includes: subject description, location, outfit, lighting, camera specs, style keywords
4. Avoids: generic AI tropes (glowing eyes, symmetrical poses, obvious CGI aesthetics)
5. Ends with quality enhancers: "Ultra-realistic, 8K detail" or "Cinematic 4K, film grain"

Also return:
- Suggested title (5-7 words)
- 4-6 tags
- Post type (image or video)
- Platform recommendation
- Short trending reference summary (1-2 sentences)
- Optional: Nova's notes (tip for using this prompt)

Return as JSON.
```

**Expected JSON output:**
```json
{
  "id": "post-XXX",
  "date": "YYYY-MM-DD",
  "title": "...",
  "platform": "Freepik Mystic",
  "type": "image",
  "prompt": "...",
  "tags": ["travel", "..."],
  "trending_reference": "...",
  "notes": "..."
}
```

---

## Step 3: Generate the Image/Video

### Option A — Freepik Mystic (Images)
**Tool:** `tools/generate_image.py`  
- API endpoint: `POST https://api.freepik.com/v1/ai/text-to-image`
- Input: prompt from Step 2
- Output: image URL → download and save to `.tmp/`
- Rename: `post-XXX-freepik.jpg`

### Option B — Kling AI (Videos)
- Kling does not have a public API yet as of April 2026
- **Manual step:** Go to klingai.com → paste prompt → generate → download video
- Save as `.tmp/post-XXX-kling.mp4`
- Upload to GitHub repo `assets/images/` folder

### Option C — Higgsfield (Videos)
- Higgsfield API: `POST https://api.higgsfield.ai/v1/generate`
- **Tool:** `tools/generate_image.py` (set `--platform higgsfield`)
- If API unavailable: manual generation at higgsfield.ai

**Image storage decision:**
- Option 1 (Recommended): Upload to GitHub repo `/assets/images/` — fully self-hosted
- Option 2: Use the direct Freepik CDN URL — no download needed, but URL may expire

---

## Step 4: Update the Website

**Tool:** `tools/update_website.py`

Steps:
1. Load `content/posts.json`
2. Prepend the new post object (newest first)
3. Update `last_updated` field to today
4. Commit and push to GitHub repo
5. Netlify detects push → auto-deploys (usually within 60 seconds)

**Required env vars:**
```
GITHUB_TOKEN=your_token
GITHUB_REPO=username/nova-linh-website
GITHUB_BRANCH=main
```

---

## Step 5: Manual Fallback (No API)

If any API is unavailable:

1. **Research:** Manually browse X/Threads for 10 minutes
2. **Generate prompt:** Run `tools/generate_prompt.py` with your research note as input
3. **Generate image:** Paste prompt into Freepik.com/mystic (free credits) or Kling AI web
4. **Download image:** Save to `assets/images/post-XXX.jpg`
5. **Update posts.json:** Add new entry at the top of the `posts` array
6. **Push to GitHub:** `git add . && git commit -m "Add post: [title]" && git push`

---

## Edge Cases

| Situation | Action |
|-----------|--------|
| Freepik API rate limit | Switch to Freepik web (free tier has daily credits) |
| Kling/Higgsfield no API | Manual generation on web platform |
| X API rate limit | Manual 10-min trend research on X.com |
| Generated image looks obviously AI | Re-run with "shot on iPhone 15 Pro, candid, unposed" added |
| Platform content policy blocks prompt | Remove explicit style words; keep it editorial/artistic |
| GitHub push fails | Check token expiry; regenerate in GitHub Settings → Tokens |

---

## Quality Checklist Before Publishing

- [ ] Image does NOT have obvious AI artifacts (extra fingers, distorted text, glitchy background)
- [ ] Nova's ethnicity reads correctly (Southeast Asian features, warm skin tone)
- [ ] Prompt includes a specific location (not just "beach" — say "Palawan, Philippines")
- [ ] Tags are accurate and include at least one trending keyword
- [ ] Trending reference is logged (helps track what works over time)
- [ ] Post ID follows format: `post-XXX` (increment from last ID)

---

## Learning Log

*Add entries here when you discover new patterns that improve engagement or quality:*

| Date | Learning | Applied To |
|------|----------|------------|
| 2026-04-16 | "Eyes slightly downcast" direction reads as more authentic than direct gaze | Paris Café post |
| 2026-04-16 | Philippine location tags drive strong diaspora engagement | Palawan beach post |
| 2026-04-16 | Golden hour + silhouette posts get 4-6x more engagement on X | Bali post |
