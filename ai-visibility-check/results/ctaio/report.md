# AI visibility report

**URL:** https://ctaio.dev/en/
**Checked:** 2026-10-03T19:59:06.893Z

## Result: 94% visible to AI crawlers

Good: AI crawlers can read almost all of this page.

| | Words | Title | Meta description |
|---|---|---|---|
| AI crawler (no JavaScript) | 271 | yes | yes |
| Person (full browser) | 266 | yes | yes |

## Why
Detected stack: **Astro**
Astro ships HTML by default. Check components marked client:only, which render nothing until JavaScript runs.

## AI bots blocked in robots.txt
None of the major AI bots are blocked.

## What AI crawlers can't see (1 line)
- Localized content is available in German, French, Spanish, Brazilian Portuguese, and a starter hub in Bahasa Indonesia.

## The fix
1. **Real fix:** Astro ships HTML by default. Check components marked client:only, which render nothing until JavaScript runs.
2. **Quick fix:** upload the generated `llms.txt` to your site root.
3. **Point to it:** paste this in your page's `<head>`. It sits in the raw HTML, so crawlers that skip JavaScript still see it:

```html
<link rel="alternate" type="text/markdown" href="/llms.txt" title="Text version for AI tools">
```

Note: no AI company has confirmed its crawler reads llms.txt. The real fix (1) is the only guaranteed one.
