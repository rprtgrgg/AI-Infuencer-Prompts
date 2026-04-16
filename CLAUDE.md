# Agent Instructions — Nova Linh AI Influencer

You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution.

## Project: Nova Linh AI Influencer Prompt Reference Website

**Nova Linh** is an AI-generated influencer: 24yo Vietnamese-Filipino mix, travel/lifestyle/fashion niche, cute+sexy+editorial aesthetic. Handle: `@novalinhofficial`.

**Goal:** Every day, find a trending reference photo from X/Threads, write a detailed AI prompt based on it, and publish both to the website. The user copies the prompt and pastes it into Freepik Mystic, Kling AI, or Higgsfield to generate Nova's version.

**Website purpose:** Reference photo + copyable prompt. Nothing else.

## File Structure

```
claude AI Influencer prompts/
├── index.html               # Single-page site — reference photo + prompt list
├── assets/
│   └── images/              # Optional: locally stored reference images
├── content/
│   └── posts.json           # THE data file — all posts live here
├── tools/
│   ├── search_trending.py   # Step 1: Scrape X for trending content
│   ├── generate_prompt.py   # Step 2: Claude generates the post prompt
│   └── update_website.py    # Step 3: Pushes new post to GitHub
├── workflows/
│   ├── daily_prompt_research.md  # Full SOP for daily workflow
│   ├── n8n_workflow.json         # Importable n8n automation workflow
│   └── n8n_setup_guide.md        # Step-by-step n8n setup (30-45 min)
├── .env.example             # Template for API keys
├── .env                     # Actual keys (gitignored — never commit)
└── .gitignore
```

## The WAT Architecture

**Layer 1: Workflows (The Instructions)**
- `workflows/daily_prompt_research.md` — the full SOP
- `workflows/n8n_workflow.json` — automated n8n pipeline
- `workflows/n8n_setup_guide.md` — how to set up automation

**Layer 2: Agents (This is your role)**
- Read the workflow, orchestrate tools in sequence
- Handle failures, update workflows when you learn something new
- Ask before running tools that use paid API credits

**Layer 3: Tools (The Execution)**
- `tools/search_trending.py` → fetches X trends
- `tools/generate_prompt.py` → Claude generates post JSON
- `tools/generate_image.py` → Freepik/Higgsfield generates asset
- `tools/update_website.py` → pushes to GitHub → Netlify auto-deploys

## Daily Post Format (posts.json)

Each post in `content/posts.json` follows this schema:
```json
{
  "id": "post-XXX",
  "date": "YYYY-MM-DD",
  "title": "5-7 word title",
  "platform": "Freepik Mystic | Kling AI | Higgsfield | Other",
  "type": "image | video",
  "reference_image": "URL of the trending photo found on X/Threads (the inspiration)",
  "prompt": "Full detailed AI generation prompt — what the user copies and pastes",
  "tags": ["travel", "location", "style", "..."],
  "trending_reference": "Why this photo/style is trending and what engagement it drives"
}
```

**Rules:**
- `reference_image` = the real photo found on X/Threads used as inspiration (NOT a generated image)
- `prompt` = the detailed text the user copies into Freepik/Kling/Higgsfield
- Newest post goes first (prepend, not append)
- IDs follow `post-001`, `post-002`, etc.
- Platform rotation: Freepik → Kling → Freepik → Higgsfield → Freepik → Kling
- Always include `trending_reference` — this is the learning log

## Deployment

- **Hosting:** Netlify (auto-deploys on GitHub push)
- **Repo:** GitHub (`yourusername/nova-linh-website`) — update GITHUB_REPO in .env
- **Automation:** n8n Cloud runs daily at 9AM UTC
- **Data flow:** posts.json on GitHub → Netlify serves it → JS renders it in browser

## API Keys Needed

| Key | Where to Get | Required? |
|-----|-------------|-----------|
| `CLAUDE_API_KEY` | console.anthropic.com | Yes |
| `GITHUB_TOKEN` | github.com → Settings → Tokens | Yes |
| `FREEPIK_API_KEY` | freepik.com/api | Yes (for auto images) |
| `X_BEARER_TOKEN` | developer.twitter.com | No (fallback data used) |
| `HIGGSFIELD_API_KEY` | higgsfield.ai | No (manual fallback) |

## How to Run Manually

```bash
# Full pipeline (requires all API keys in .env)
python tools/search_trending.py
python tools/generate_prompt.py
python tools/generate_image.py
python tools/update_website.py

# Dry run (no API calls to GitHub)
python tools/update_website.py --dry-run

# With custom trending reference
python tools/generate_prompt.py --reference "Tokyo cherry blossom content is trending"
```

## Nova's Canon Face — ALWAYS USE THIS DESCRIPTION

Nova's face is locked. Every single prompt must include this exact face block verbatim:

```
She has light-medium warm skin with a dewy natural glow, almond-shaped dark brown eyes with a natural double eyelid and a soft warm gaze, softly arched dark brown brows, a small straight nose with a slightly rounded tip, full lips with a soft cupid's bow in a natural nude-pink, an oval face with soft high cheekbones and a gentle rounded jaw, and long dark brown wavy hair that is voluminous with face-framing layers.
```

**Character reference image:** The user has a saved canon face image (`nova-canon-face.jpg`) — they must upload this to Freepik Mystic / Kling / Higgsfield as the **Character Reference / Face Lock** before generating, so the face stays consistent across all posts.

**Never describe her as:** "beautiful woman", "gorgeous girl", "stunning model" — these are generic and produce inconsistent AI faces. Always use the specific face block above.

## Nova's Prompt Formula

Every prompt must follow this structure in order:

1. **Face block** (copy exactly from above — never skip this)
2. **Who + age:** "A 24-year-old Vietnamese-Filipino woman"
3. **Where:** Specific location ("Tegallalang rice terraces, Bali" not just "Bali")
4. **Outfit:** Specific (color + fabric + style — e.g. "flowing white linen sundress with thin spaghetti straps")
5. **Action/Mood:** Candid direction ("looks over her shoulder with a soft smile", "laughs genuinely at something off-camera", "lost in thought, eyes slightly downcast")
6. **Lighting:** Direction + quality ("warm low-angle golden backlight", "soft morning window light from the left")
7. **Camera:** Specific lens + style ("shot on 85mm f/1.4", "35mm analog film", "Leica M", "iPhone 15 Pro candid")
8. **Avoid:** glowing eyes, perfect symmetry, plastic skin, obvious AI aesthetics
9. **End with:** "Ultra-realistic, 8K, photographic quality. No AI artifacts." (images) or "Cinematic 4K, film grain, natural motion." (video)

## Self-Improvement Loop

When you learn something new (better prompt formula, better platform setting, new trending pattern):
1. Note it in the `Learning Log` section of `workflows/daily_prompt_research.md`
2. If it's a formula change, update the prompt in `tools/generate_prompt.py`
3. Update this CLAUDE.md if the architecture changes

## Bottom Line

One post per day. Keep Nova looking real, not AI. Chase the trend, not the perfect prompt. Update the workflow when you learn. That's how she grows.
