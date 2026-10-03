# AI visibility report

**URL:** https://collab-space-theta.vercel.app
**Checked:** 2026-10-03T19:58:35.341Z

## Result: 0% visible to AI crawlers

Poor: to an AI crawler this page is mostly empty.

| | Words | Title | Meta description |
|---|---|---|---|
| AI crawler (no JavaScript) | 0 | yes | **missing** |
| Person (full browser) | 16 | yes | missing |

## Why
Detected stack: **Client-side single-page app (React/Vue/Vite)**
The page is an empty shell until JavaScript runs. Add pre-rendering at build time (e.g. vite-plugin-prerender / react-snap), or move to a framework with server rendering (Next.js, Astro, Remix).

## AI bots blocked in robots.txt
No robots.txt found.

## What AI crawlers can't see (6 lines)
- CollabFlow
- AI-powered team collaboration platform
- Email Address
- Password
- Sign In
- Don't have an account? Create Account

## The fix
1. **Real fix:** The page is an empty shell until JavaScript runs. Add pre-rendering at build time (e.g. vite-plugin-prerender / react-snap), or move to a framework with server rendering (Next.js, Astro, Remix).
2. **Quick fix:** upload the generated `llms.txt` to your site root.
3. **Point to it:** paste this in your page's `<head>`. It sits in the raw HTML, so crawlers that skip JavaScript still see it:

```html
<link rel="alternate" type="text/markdown" href="/llms.txt" title="Text version for AI tools">
```

Note: no AI company has confirmed its crawler reads llms.txt. The real fix (1) is the only guaranteed one.
