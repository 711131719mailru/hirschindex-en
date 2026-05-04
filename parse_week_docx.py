"""
Parse a single Week_N.docx (Boss's content source for the EN blog) and
upsert the resulting week into blog_data.json.

Usage:
    python parse_week_docx.py <path_to_docx> --week-num <N> [--block "Block name"]

Example:
    python parse_week_docx.py "C:/.../Week 24/Week_24.docx" --week-num 1 --block "Patients, Data and Design"

Conventions:
- Source docx contains both RU and EN sections. We extract only the EN section.
- EN section is delimited by either "EN-versions" or "EN versions" (case-insensitive).
- Posts inside the section are delimited by lines that are exactly "—", "—", "–", or similar
  long-dashes / horizontal-rule markers (in practice "— — —" or "– – –"). We treat any line
  whose stripped text consists only of dashes/em-dashes/spaces as a separator.
- The first sub-block after the EN delimiter is the "Intro" (post 0).
- Each subsequent sub-block starts with a heading line of the form "N-K: Title" or
  "N-K Title" (where N is the source week number, K is the sub-post number). We use
  that line as the post title.
"""
import argparse
import io
import json
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    from docx import Document
except ImportError:
    print("ERROR: python-docx not installed. Run: pip install python-docx")
    sys.exit(1)


SEPARATOR_RE = re.compile(r"^[\s\u2014\u2013\-—–]+$")
EN_HEADER_RE = re.compile(r"^\s*EN[\s\-]*(versions?|version|версии|версия)\b.*$", re.IGNORECASE)
RU_HEADER_RE = re.compile(r"^\s*RU[\s\-]*(versions?|version|adaptation|версии|версия|адаптация)\b.*$", re.IGNORECASE)
POST_HEADER_RE = re.compile(r"^\s*(\d+)\s*[-–—]\s*(\d+)\s*[:.\s]\s*(.+?)\s*$")
INTRO_RE = re.compile(r"^\s*Intro\b", re.IGNORECASE)
WEEK_TITLE_RE = re.compile(r"^\s*Week\s+\d+\.\s*(.+?)\s*$", re.IGNORECASE)


def extract_paragraphs(docx_path: Path) -> list[str]:
    doc = Document(str(docx_path))
    return [p.text for p in doc.paragraphs if p.text and p.text.strip()]


def find_en_section(paragraphs: list[str]) -> list[str]:
    """Slice paragraphs to only the EN-versions block."""
    start = None
    end = len(paragraphs)
    for i, p in enumerate(paragraphs):
        if EN_HEADER_RE.match(p):
            start = i + 1
        elif start is not None and RU_HEADER_RE.match(p):
            end = i
            break
    if start is None:
        raise ValueError(
            "No EN-versions section header found in docx. Expected a line like 'EN-versions' or 'EN versions'."
        )
    return paragraphs[start:end]


def split_into_posts(en_paragraphs: list[str]) -> list[list[str]]:
    """Split EN paragraphs into post-sized chunks using long-dash separators."""
    posts = []
    current = []
    for p in en_paragraphs:
        if SEPARATOR_RE.match(p):
            if current:
                posts.append(current)
                current = []
        else:
            current.append(p)
    if current:
        posts.append(current)
    return posts


def parse_post(chunk: list[str], week_title: str | None) -> dict:
    """A chunk is a list of paragraphs that form one post.
    Returns {title, body[]} where title is the post heading and body is the rest.
    """
    if not chunk:
        return {"title": "", "body": []}

    head = chunk[0].strip()
    rest = chunk[1:]

    # Skip a standalone "Intro" header line; the next line is the real title (e.g. "Week 24. Population and Sampling")
    if INTRO_RE.match(head) and rest:
        head = rest[0].strip()
        rest = rest[1:]

    # If head matches "N-K: Title" or "N-K Title", extract title
    m = POST_HEADER_RE.match(head)
    if m:
        title = m.group(3).strip()
        body = [r.strip() for r in rest if r.strip()]
        return {"title": title, "body": body}

    # Else: treat first line as title (typical for Intro: "Week 24. Population and Sampling")
    return {"title": head, "body": [r.strip() for r in rest if r.strip()]}


def derive_week_title(posts: list[dict]) -> str:
    """The intro post's title is typically 'Week N. <Topic>'. Extract <Topic>."""
    if not posts:
        return ""
    intro_title = posts[0].get("title", "")
    m = WEEK_TITLE_RE.match(intro_title)
    if m:
        return m.group(1).strip()
    return intro_title


def upsert_week(blog_data: list[dict], week: dict) -> list[dict]:
    """Insert or replace by 'num'."""
    out = [w for w in blog_data if str(w.get("num")) != str(week["num"])]
    out.append(week)
    out.sort(key=lambda w: int(w["num"]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", type=Path, help="Path to Week_N.docx")
    ap.add_argument("--week-num", required=True, help="EN week number (e.g. 1 for the first published EN week)")
    ap.add_argument("--block", default="", help="Block name (e.g. 'Patients, Data and Design')")
    ap.add_argument(
        "--blog-data",
        type=Path,
        default=Path(__file__).parent / "blog_data.json",
        help="Path to blog_data.json (default: alongside this script)",
    )
    args = ap.parse_args()

    paragraphs = extract_paragraphs(args.docx)
    en_section = find_en_section(paragraphs)
    chunks = split_into_posts(en_section)
    if not chunks:
        raise SystemExit("No posts found after splitting EN section.")

    posts = [parse_post(c, None) for c in chunks]
    posts = [p for p in posts if p.get("title") or p.get("body")]
    title = derive_week_title(posts)

    # Intro post repeats the week title ("Week N. Topic"); the rendered HTML
    # already shows that in a separate badge, so suppress the duplicate.
    if posts and WEEK_TITLE_RE.match(posts[0].get("title", "")):
        posts[0]["title"] = ""

    # Filter Cyrillic paragraphs that slipped into the EN section (Boss left
    # an untranslated reference paragraph, etc.). Warn so the operator knows.
    cyrillic_re = re.compile(r"[А-Яа-яЁё]")
    for p in posts:
        clean_body = []
        for line in p.get("body", []):
            cyr_chars = len(cyrillic_re.findall(line))
            if cyr_chars > 30 and cyr_chars / max(len(line), 1) > 0.3:
                print(f"  WARN: dropped Cyrillic paragraph in '{p.get('title') or 'intro'}': {line[:80]}...")
                continue
            clean_body.append(line)
        p["body"] = clean_body

    week = {
        "num": str(args.week_num),
        "title": title,
        "block": args.block,
        "posts": posts,
    }

    if args.blog_data.exists() and args.blog_data.stat().st_size > 0:
        blog_data = json.loads(args.blog_data.read_text(encoding="utf-8"))
    else:
        blog_data = []

    blog_data = upsert_week(blog_data, week)
    args.blog_data.write_text(json.dumps(blog_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Week {week['num']} '{week['title']}' upserted ({len(week['posts'])} posts) → {args.blog_data}")


if __name__ == "__main__":
    main()
