# AI visibility report

**URL:** https://smart-recipe-swart.vercel.app
**Checked:** 2026-10-03T19:58:33.116Z

## Result: 17% visible to AI crawlers

Poor: to an AI crawler this page is mostly empty.

| | Words | Title | Meta description |
|---|---|---|---|
| AI crawler (no JavaScript) | 22 | yes | yes |
| Person (full browser) | 127 | yes | yes |

## Why
Detected stack: **Next.js**
Render these pages on the server: move data fetching into Server Components / getStaticProps, and avoid 'use client' wrappers around the whole page.

## AI bots blocked in robots.txt
No robots.txt found.

## What AI crawlers can't see (33 lines)
- Smart Recipe Generator
- Favorites
- Sign in to save your favorite recipes and get personalized recommendations
- Sign In
- What ingredients do you have?
- Add your available ingredients below to generate personalized recipes
- Quick add common ingredients:
- chicken
- rice
- tomatoes
- onions
- garlic
- olive oil
- eggs
- milk
- cheese
- bread
- pasta
- bell peppers
- carrots
- potatoes
- spinach
- mushrooms
- lemon
- herbs
- Generate Recipes
- 💡 Sign in to save your favorite recipes for later!
- Smart Ingredient Matching
- Our AI analyzes your ingredients and creates perfect recipe combinations.
- Quick & Easy
- ...and 3 more

## The fix
1. **Real fix:** Render these pages on the server: move data fetching into Server Components / getStaticProps, and avoid 'use client' wrappers around the whole page.
2. **Quick fix:** upload the generated `llms.txt` to your site root.
3. **Point to it:** paste this in your page's `<head>`. It sits in the raw HTML, so crawlers that skip JavaScript still see it:

```html
<link rel="alternate" type="text/markdown" href="/llms.txt" title="Text version for AI tools">
```

Note: no AI company has confirmed its crawler reads llms.txt. The real fix (1) is the only guaranteed one.
