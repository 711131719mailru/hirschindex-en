"""
Regenerate the blog content section of blog.html (EN site) from blog_data.json.

This script preserves everything in blog.html EXCEPT the section between the
`<!-- Blog Content -->` marker and the `<!-- Footer -->` marker. The hero,
navigation, and footer are left untouched (they are maintained by the
designer / content team directly in blog.html).

Usage:
    python gen_blog.py

Reads:  ./blog_data.json
Writes: ./blog.html  (in-place section replacement)

Block grouping: posts are grouped by the optional "block" field on each week
(e.g. "Patients, Data and Design"). Weeks within a block are listed
newest-first. Blocks themselves appear in the order they first appear in the
data file (so the live block stays at the top while older blocks accumulate
below).
"""
from __future__ import annotations

import html as html_mod
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = Path(__file__).parent
DATA_PATH = BASE / "blog_data.json"
HTML_PATH = BASE / "blog.html"

START_MARKER = "<!-- Blog Content -->"
END_MARKER = "<!-- Footer -->"


def esc(text: str | None) -> str:
    return html_mod.escape(text or "")


def render_post(post: dict) -> str:
    parts: list[str] = []
    title = (post.get("title") or "").strip()
    if title:
        parts.append(
            f'<h4 style="margin:20px 0 10px; font-size:1.05rem; color:#0f172a;">{esc(title)}</h4>'
        )
    for line in post.get("body", []):
        line = (line or "").strip()
        if not line:
            continue
        if line.startswith("- ") or line.startswith("— ") or line.startswith("– "):
            parts.append(
                f'<p style="margin:4px 0 4px 16px; color:#475569; font-size:0.92rem; line-height:1.6;">{esc(line)}</p>'
            )
        else:
            parts.append(
                f'<p style="color:#475569; font-size:0.92rem; line-height:1.6; margin-bottom:10px;">{esc(line)}</p>'
            )
    return "\n            ".join(parts)


def render_week_section(week: dict) -> str:
    posts_html: list[str] = []
    for p in week.get("posts", []):
        ph = render_post(p)
        if ph.strip():
            posts_html.append(
                '<div style="margin-bottom:16px; padding:20px 24px; background:#fff; border:1px solid #e2e8f0; border-radius:8px;">\n            '
                + ph
                + "\n          </div>"
            )
    posts_block = "".join(posts_html)
    return (
        f'<div id="week-{esc(week["num"])}" style="margin-bottom:50px;">\n'
        f'        <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:20px;">\n'
        f'          <span style="font-size:0.8rem; font-weight:600; color:#3366CC; background:#eff6ff; padding:4px 12px; border-radius:4px;">Week {esc(week["num"])}</span>\n'
        f'          <h3 style="font-size:1.3rem; margin:0; color:#0f172a;">{esc(week["title"])}</h3>\n'
        f"        </div>\n"
        f"        {posts_block}\n"
        f"      </div>"
    )


def group_by_block(weeks: list[dict]) -> list[tuple[str, list[dict]]]:
    """Preserve first-seen order of blocks; sort weeks within a block newest first."""
    order: list[str] = []
    buckets: dict[str, list[dict]] = {}
    for w in weeks:
        block = (w.get("block") or "").strip()
        if block not in buckets:
            buckets[block] = []
            order.append(block)
        buckets[block].append(w)
    for block in order:
        buckets[block].sort(key=lambda w: int(w["num"]), reverse=True)
    return [(b, buckets[b]) for b in order]


def build_toc_and_content(weeks: list[dict]) -> tuple[str, str]:
    grouped = group_by_block(weeks)
    toc_lines: list[str] = []
    content_blocks: list[str] = []

    for block_name, block_weeks in grouped:
        if block_name:
            toc_lines.append(
                f'<div style="margin:18px 0 6px; font-size:0.7rem; font-weight:700; color:#c5a065; letter-spacing:0.12em; text-transform:uppercase;">{esc(block_name)}</div>'
            )
            content_blocks.append(
                f'<div style="margin:0 0 28px; padding-bottom:12px; border-bottom:2px solid #c5a065;">\n'
                f'        <div style="font-size:0.75rem; font-weight:700; color:#c5a065; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:6px;">Block · {esc(block_name)}</div>\n'
                f'      </div>'
            )
        for w in block_weeks:
            toc_lines.append(
                f'<a href="#week-{esc(w["num"])}" class="toc-link"><strong>{esc(w["num"])}.</strong> {esc(w["title"])}</a>'
            )
            content_blocks.append(render_week_section(w))

    return ("\n                        ".join(toc_lines), "\n      ".join(content_blocks))


def build_section(toc_html: str, content_html: str) -> str:
    return f"""<!-- Blog Content -->
        <section class="pt-90 pb-90">
            <div class="container">
                <div class="blog-layout">
                    <div class="toc-sidebar wow fadeInLeft">
                        <h4 style="margin-bottom:12px; font-size:0.95rem;">Contents</h4>
                        {toc_html}
                    </div>
                    <div>
                      {content_html}
                    </div>
                </div>
            </div>
        </section>

        """


def main() -> None:
    if not DATA_PATH.exists():
        print(f"ERROR: {DATA_PATH} not found")
        sys.exit(1)

    weeks = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(weeks, list):
        print("ERROR: blog_data.json must contain a JSON array")
        sys.exit(1)

    text = HTML_PATH.read_text(encoding="utf-8")
    si = text.find(START_MARKER)
    ei = text.find(END_MARKER)
    if si < 0 or ei < 0:
        print(f"ERROR: markers not found in blog.html ({START_MARKER!r} or {END_MARKER!r})")
        sys.exit(1)

    if not weeks:
        # No weeks yet — keep the empty skeleton placeholder that is already there.
        print("blog_data.json is empty, leaving blog.html skeleton intact.")
        return

    toc_html, content_html = build_toc_and_content(weeks)
    new_section = build_section(toc_html, content_html)
    new_text = text[:si] + new_section + text[ei:]
    HTML_PATH.write_text(new_text, encoding="utf-8")

    print(f"blog.html: {len(text):,} -> {len(new_text):,} chars")
    print(f"Weeks rendered: {len(weeks)}")


if __name__ == "__main__":
    main()
