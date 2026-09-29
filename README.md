# daily-ai-learn

An open-source agent that helps people keep learning AI — one sharp idea per day.

Every day, a GitHub Actions workflow asks an open-weights model to teach **one non-obvious AI concept** as:

1. **An X-ready post** (≤280 chars, English, no fluff) — printed in the Actions log and saved below.
2. **A short explainer** (~150 words) — committed to [`posts/`](posts/) as markdown.

Nothing is auto-posted to X. The human reviews the daily post and publishes the ones worth sharing. Real project, real commits, real learning.

## How it works

```
GitHub Actions (daily, 6am PT)
  → agent/generate.py picks today's topic (rotates through agent/topics.txt)
  → calls an OpenAI-compatible API (DeepSeek / GLM / any)
  → writes posts/YYYY-MM-DD.md and commits it
```

## Setup

1. Fork / clone this repo.
2. Add your model API key as a repository secret named `AI_API_KEY`
   (Settings → Secrets and variables → Actions).
3. Optional secrets: `AI_API_BASE` (default `https://api.deepseek.com`),
   `AI_MODEL` (default `deepseek-chat`). Any OpenAI-compatible endpoint works —
   e.g. Zhipu's GLM API for `glm-5.3`.
4. The workflow runs on schedule, or trigger it manually from the Actions tab
   (`workflow_dispatch`).

No API key? `python agent/generate.py --dry-run` prints the prompt it *would*
send, so you can paste it into any chat model by hand.

## Cost

One short completion per day — fractions of a cent on DeepSeek/GLM pricing.

## License

MIT — learn in public.
