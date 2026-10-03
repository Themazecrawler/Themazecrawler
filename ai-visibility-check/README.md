# ai-visibility-check

**How much of your web page can an AI crawler actually read?**

Many AI crawlers read a page's raw HTML and don't run JavaScript. Sites that build their content in the browser (common with React and Vite apps) can look almost empty to them, and an AI can't recommend a page it can't read.

This script loads a page twice and compares the results:

1. **As an AI crawler sees it:** raw HTML, JavaScript off
2. **As a person sees it:** full browser, JavaScript on

It then writes:

- `report.md`: the percentage visible to AI, the exact text crawlers miss, the detected stack and the fix for that stack, and which AI bots (GPTBot, ClaudeBot, PerplexityBot…) `robots.txt` blocks
- `llms.txt`: a plain-text version of the full rendered page, ready to upload
- the one-line `<link rel="alternate">` tag that points crawlers to that file. It goes in the raw HTML, so crawlers that skip JavaScript still find it

## Run it

```bash
npm install
npx playwright install chromium
node check.mjs https://your-site.com --out report
```

## Real results (3 Oct 2026)

| Site | Stack | Visible to AI | Report |
|---|---|---|---|
| [SmartRecipe](https://smart-recipe-swart.vercel.app) (my project) | Next.js, rendered client-side | **17%** | [report](results/smartrecipe/report.md) |
| [CollabSpace](https://collab-space-theta.vercel.app) (my project) | Vite + React | **0%** | [report](results/collabspace/report.md) |
| [ctaio.dev](https://ctaio.dev/en/) | Astro | **94%** | [report](results/ctaio/report.md) |

Both of my own apps are close to invisible to AI crawlers. CollabSpace ships an empty `<div id="root"></div>`. SmartRecipe uses Next.js, which can render on the server, but the ingredient picker and most of the page text only appear after JavaScript runs.

## Honest limits

- **No AI company has confirmed that its crawler reads `llms.txt`.** The `<link>` tag makes the file easy to find, but the only guaranteed fix is server rendering or pre-rendering (the report names the right one for your stack).
- "Visible" means the text appears somewhere in the raw HTML. It doesn't measure whether an AI understands or ranks the page.
- Coverage is word-weighted, so it checks one URL at a time, not a whole site.

`ROUTE_VIA_NODE=1` sends the browser's requests through Node, for networks with a TLS-inspecting proxy that Chromium doesn't trust (Node honours `NODE_EXTRA_CA_CERTS`).
