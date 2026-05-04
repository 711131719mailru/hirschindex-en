# Hirsch Index — International (EN) website

Static site for [hirschindex.com](https://hirschindex.com) — a school of scientific publishing for physicians and researchers.

## Stack

- Static HTML + CSS (Bootstrap + WOW.js + custom)
- Hosted on GitHub Pages + Cloudflare (DNS + proxy)
- Blog rendered from `blog_data.json` via `gen_blog.py`

## Structure

| File | Purpose |
|------|---------|
| `index.html` | Home — hero, ecosystem (4 pillars), founder, social, CTA |
| `consulting.html` | Consulting service page |
| `blog.html` | Blog index — generated from `blog_data.json` |
| `resources.html` | Free researcher tools |
| `privacy.html` | Privacy Policy |
| `offer.html` | Terms of Service |
| `styles.css` | Site-wide styles |
| `assets/` | Images, fonts, JS, CSS frameworks |
| `gen_blog.py` | Regenerates `blog.html` from `blog_data.json` |

## Local preview

```
python -m http.server 8765
```

Open http://localhost:8765/

## Deploy

Push to `main`. GitHub Pages serves from root. CNAME points to `hirschindex.com`. Cloudflare proxies and provides HTTPS.
