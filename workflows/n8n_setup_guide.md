# n8n Setup Guide — Nova Linh Daily Automation

This guide gets the daily prompt-to-publish pipeline running on n8n Cloud (free tier).
Estimated setup time: **30-45 minutes**.

---

## Step 1: Create n8n Cloud Account

1. Go to **https://app.n8n.cloud/register**
2. Sign up with your email
3. Choose the **Free** plan (1 active workflow, 5 executions/day — enough for our 1 daily post)
4. Verify your email and log in

---

## Step 2: Get Your API Keys

You need 3-4 keys. Get them in this order:

### A. Anthropic (Claude) — Required
1. Go to **https://console.anthropic.com**
2. Sign up / log in
3. Go to **API Keys** → **Create Key**
4. Copy the key: `sk-ant-...`
5. **Cost:** ~$0.002 per daily run (very cheap)

### B. GitHub Personal Access Token — Required
1. Go to **https://github.com** → Sign in (or create account)
2. Go to **Settings** → **Developer settings** → **Personal access tokens** → **Tokens (classic)**
3. Click **Generate new token (classic)**
4. Name: `nova-linh-n8n`
5. Expiration: **No expiration** (or 1 year)
6. Scopes: Check **repo** (full control of private repositories)
7. Click **Generate token** → Copy it immediately (you won't see it again)

### C. Freepik API — Required for auto image generation
1. Go to **https://www.freepik.com/api**
2. Sign up for the API program
3. Copy your API key
4. **Free tier:** Check current free credits at freepik.com/api/pricing
5. **Alternative:** If Freepik API has no free tier, generate images manually at freepik.com/mystic

### D. X (Twitter) Bearer Token — Optional
1. Go to **https://developer.twitter.com/en/portal**
2. Apply for a developer account (takes 1-2 days to approve)
3. Create a Project → Create an App
4. Go to **Keys and Tokens** → Copy the **Bearer Token**
5. **Free tier:** 500K tweet reads/month — more than enough for 1 search/day
6. **If skipped:** The workflow uses built-in fallback trend data — still works!

---

## Step 3: Set Up Your GitHub Repository

1. Go to **https://github.com/new**
2. Repository name: `nova-linh-website`
3. Visibility: **Public** (required for free Netlify hosting)
4. Click **Create repository**

5. Upload your website files:
   - Option A: Use GitHub Desktop (drag and drop the `nova-linh-website` folder)
   - Option B: Command line:
     ```bash
     cd Desktop/nova-linh-website
     git init
     git add .
     git commit -m "Initial Nova Linh website"
     git branch -M main
     git remote add origin https://github.com/YOURUSERNAME/nova-linh-website.git
     git push -u origin main
     ```

---

## Step 4: Connect to Netlify

1. Go to **https://app.netlify.com** → Sign up (free)
2. Click **Add new site** → **Import an existing project**
3. Connect to **GitHub** → Authorize Netlify
4. Select your `nova-linh-website` repository
5. Settings:
   - **Branch:** `main`
   - **Build command:** *(leave blank — static site)*
   - **Publish directory:** `.` (root)
6. Click **Deploy site**
7. Your site is live in ~1 minute at a URL like: `sparkly-nova-123.netlify.app`
8. Optional: Go to **Domain settings** → add a custom domain (e.g., `novalinhofficial.com`)

---

## Step 5: Import the n8n Workflow

1. In n8n Cloud, click **+** to create a new workflow
2. Click the **⋮** menu (top right) → **Import from file**
3. Upload `workflows/n8n_workflow.json`
4. The workflow loads with all nodes pre-configured

---

## Step 6: Add Credentials in n8n

In n8n, go to **Settings** → **Credentials** → add each one:

### Anthropic API
- Credential type: **Anthropic**
- API Key: `sk-ant-YOUR_KEY`

### GitHub API
- Credential type: **GitHub API**
- Access Token: `ghp_YOUR_TOKEN`

### Freepik (HTTP Header Auth)
- Credential type: **Header Auth**
- Name: `x-freepik-api-key`
- Value: `YOUR_FREEPIK_KEY`

### X/Twitter Bearer Token (optional)
- Credential type: **Header Auth**
- Name: `Authorization`
- Value: `Bearer YOUR_BEARER_TOKEN`

---

## Step 7: Configure Environment Variables in n8n

In n8n, go to **Settings** → **Variables** → add:

| Variable | Value |
|----------|-------|
| `GITHUB_REPO` | `yourusername/nova-linh-website` |

---

## Step 8: Connect Credentials to Nodes

1. Open the imported workflow
2. Click each node that has a ⚠️ warning:
   - **Search X for Trends** → select your X Bearer Token credential
   - **Generate Prompt (Claude)** → select your Anthropic credential
   - **Generate Image (Freepik)** → select your Freepik Header Auth credential
   - **Fetch posts.json from GitHub** → select your GitHub API credential
   - **Push to GitHub** → select your GitHub API credential
3. Save the workflow (Ctrl+S)

---

## Step 9: Test the Workflow

1. Click **Test workflow** (play button at bottom)
2. Watch each node execute step by step
3. Check for errors in red nodes — click them to see the error details
4. If successful, verify:
   - A new post appeared in `content/posts.json` on GitHub
   - Netlify deployed the update (check the Netlify dashboard)
   - Your website shows the new post

**Common issues:**
- `401 Unauthorized` on GitHub → check token scopes (needs `repo`)
- `429 Too Many Requests` on X → workflow will auto-use fallback data ✓
- Freepik returns task_id (async) → image may take 30-60s to appear
- Claude returns malformed JSON → check the system prompt, try again

---

## Step 10: Activate the Schedule

1. Once the test passes, toggle **Active** (top right of workflow editor)
2. The workflow will now run automatically every day at 9:00 AM UTC
3. To change the time: click the **Daily 9AM Trigger** node → adjust the cron expression
   - `0 9 * * *` = 9AM UTC daily
   - `0 17 * * *` = 5PM UTC daily (1AM Manila time)
   - `0 1 * * *` = 1AM UTC daily (9AM Manila time)

---

## Manual Override (Any Time)

To manually run the workflow (skip the schedule):
1. Open the workflow in n8n
2. Click **Test workflow** → runs immediately
3. Or use the n8n CLI: `n8n execute --id WORKFLOW_ID`

---

## For Video Posts (Kling AI / Higgsfield)

When the workflow generates a video prompt (Kling or Higgsfield), it:
1. Publishes the post to the website with an empty `image` field
2. Logs a note that manual generation is required

**Your action:**
1. Check the website or n8n execution log for the new prompt
2. Go to klingai.com or higgsfield.ai
3. Paste the prompt → generate → download the video
4. Upload to `assets/images/POST_ID-kling.mp4` on GitHub
5. Update `posts.json` on GitHub → set `"image": "assets/images/POST_ID-kling.mp4"`

This hybrid approach keeps you in control of video quality while images are fully automated.

---

## Monitoring

- **n8n:** Check **Executions** tab daily to see if the workflow ran successfully
- **GitHub:** Check commit history to see new posts being added
- **Netlify:** Check deploy log to confirm auto-deploy worked
- **Website:** Visit your URL each morning to see the new post live

---

## Cost Estimate (Monthly)

| Service | Cost |
|---------|------|
| n8n Cloud (free tier) | $0 |
| Netlify (free tier) | $0 |
| GitHub (free tier) | $0 |
| Anthropic Claude | ~$0.06/month (30 daily calls × $0.002) |
| Freepik API | Depends on plan |
| X API (free tier) | $0 |
| **Total** | **~$0-5/month** |
