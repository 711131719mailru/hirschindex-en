"""Extract clean blog content from Telegram docx export and generate blog.html"""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from docx import Document

doc = Document(r'C:\Моя папка\1. Наука\004 Контент\Telegram-канал\Опубликованный контент азбуки.docx')

paragraphs = [p.text.strip() for p in doc.paragraphs]

# Patterns to skip
SKIP_PATTERNS = [
    r'^Индекс Хирша, \[',           # old format metadata
    r'^\[\d{2}\.\d{2}\.\d{4} \d',   # new format metadata [dd.mm.yyyy HH:MM]
    r'^@hirsch_index_school',
    r'^#\w+',                         # hashtags line
    r'^👍\s*(было полезно|Читать|Неделя|MAX|Мы в)',
    r'^👎',
    r'^❤',
    r'^🔥',
    r'^> Читать',
    r'^> Наш (MAX|VK)',
]

def should_skip(text):
    for pat in SKIP_PATTERNS:
        if re.match(pat, text):
            return True
    return False

def clean_text(text):
    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\s*\(https?://[^\)]+\)', r'\1', text)
    # Remove bare (url) references
    text = re.sub(r'\s*\(https?://[^\)]+\)', '', text)
    return text.strip()

# Parse weeks
weeks = []
current_week = None
current_posts = []
current_post_lines = []

# Extract week number and title from various header formats
def parse_week_header(text):
    # "Неделя 1 – 12.11.2025-16.11.2025"
    m = re.match(r'Неделя (\d+(?:-\d+)?)\s*[–-]\s*(.*)', text)
    if m:
        return m.group(1), m.group(2).strip()
    # "Неделя 5 – 08.12.2025-14.12.2025" then next line has title
    m = re.match(r'Неделя (\d+)$', text)
    if m:
        return m.group(1), ''
    return None, None

# First pass: identify week boundaries
week_starts = []
for i, text in enumerate(paragraphs):
    if text.startswith('Неделя') and not text.startswith('Неделя "') and not text.startswith('Неделя с '):
        num, dates = parse_week_header(text)
        if num:
            week_starts.append((i, num, dates))

# Deduplicate: keep first occurrence of each week number
seen_weeks = {}
unique_week_starts = []
for idx, num, dates in week_starts:
    base_num = num.split('-')[0]
    if base_num not in seen_weeks:
        seen_weeks[base_num] = True
        unique_week_starts.append((idx, num, dates))

# Second pass: extract content for each week
for wi, (start_idx, week_num, week_dates) in enumerate(unique_week_starts):
    end_idx = unique_week_starts[wi+1][0] if wi+1 < len(unique_week_starts) else len(paragraphs)

    posts = []
    current_title = None
    current_body = []

    for i in range(start_idx + 1, end_idx):
        text = paragraphs[i]
        if not text:
            continue
        if should_skip(text):
            # But extract title from metadata lines
            m = re.match(r'^\[\d{2}\.\d{2}\.\d{4} \d{1,2}:\d{2}\] Индекс Хирша:\s*(.*)', text)
            if m:
                # Save previous post
                if current_title or current_body:
                    posts.append({'title': current_title or '', 'body': current_body})
                title_text = m.group(1).strip()
                current_title = clean_text(title_text)
                current_body = []
                continue
            m2 = re.match(r'^Индекс Хирша, \[\d{2}\.\d{2}\.\d{4}', text)
            if m2:
                # Save previous post
                if current_title or current_body:
                    posts.append({'title': current_title or '', 'body': current_body})
                current_title = None
                current_body = []
                continue
            continue

        # Check if this is a sub-week title like "Неделя 10-1. ..." or "Неделя 12. ..."
        if re.match(r'^Неделя \d+', text):
            # This is a sub-header within a week, use as title
            if current_title or current_body:
                posts.append({'title': current_title or '', 'body': current_body})
            m = re.match(r'^Неделя [\d-]+\.?\s*(.*)', text)
            current_title = clean_text(m.group(1)) if m and m.group(1) else clean_text(text)
            current_body = []
            continue

        # If no title yet, first non-empty line becomes title
        if current_title is None:
            current_title = clean_text(text)
            current_body = []
            continue

        cleaned = clean_text(text)
        if cleaned:
            current_body.append(cleaned)

    # Save last post
    if current_title or current_body:
        posts.append({'title': current_title or '', 'body': current_body})

    # Find a good week title
    week_title = ''
    for p in posts:
        if p['title'] and ('Тема недели' in p['title'] or 'Неделя' in p['title'] or week_num in p['title']):
            week_title = re.sub(r'^.*?[:.]\s*', '', p['title'])
            break
    if not week_title and posts:
        week_title = posts[0]['title']

    weeks.append({
        'num': week_num,
        'dates': week_dates,
        'title': week_title,
        'posts': posts
    })

# Generate HTML
print(f"Extracted {len(weeks)} weeks")
for w in weeks:
    print(f"  Week {w['num']}: {w['title']} ({len(w['posts'])} posts)")

# Save as JSON for the HTML generator
with open(r'C:\Моя папка\1. Наука\004 Контент\Сайты\Индекс Хирша (RU)\blog_data.json', 'w', encoding='utf-8') as f:
    json.dump(weeks, f, ensure_ascii=False, indent=2)
print("Saved blog_data.json")
