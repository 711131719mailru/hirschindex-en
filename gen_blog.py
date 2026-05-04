"""Generate blog.html from extracted blog_data.json"""
import sys, io, json, html as html_mod
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open(r'C:\Моя папка\1. Наука\004 Контент\Сайты\Индекс Хирша (RU)\blog_data.json', 'r', encoding='utf-8') as f:
    weeks = json.load(f)

# Manual title fixes
title_overrides = {
    '1': 'Писать — значит думать',
    '2': 'Ясность сильнее сложности',
    '3': 'Научная коммуникация',
    '4': 'Академическое письмо',
    '5': 'Нет времени писать',
    '6': 'Как пережить рецензентов',
    '7': 'Что мы читаем и зачем',
    '8': 'Праздничная неделя',
    '9': 'Виды публикаций',
    '10': 'Онлайн-ресурсы исследователя',
    '11': 'Основы научного процесса',
    '12': 'Цель и задачи исследования',
    '13': 'Актуальность и научная новизна',
    '14': 'Объект и предмет исследования',
    '15': 'Доказательная медицина',
    '16': 'Обсервационные и интервенционные исследования',
    '17': 'Виды обсервационных исследований',
    '18': 'Рандомизация и РКИ',
    '19': 'Ослепление и плацебо',
    '20': 'Проспективные и ретроспективные исследования',
    '21': 'Зачем врачу наука?',
    '22': 'Данные рутинной практики',
    '23': 'Корреляция и причинность',
}

for w in weeks:
    if w['num'] in title_overrides:
        w['title'] = title_overrides[w['num']]

weeks_reversed = list(reversed(weeks))

def esc(text):
    return html_mod.escape(text)

def make_post_html(post):
    parts = []
    title = post.get('title', '').strip()
    if title:
        parts.append(f'<h4 style="margin:20px 0 10px; font-size:1.05rem;">{esc(title)}</h4>')
    for line in post.get('body', []):
        line = line.strip()
        if not line:
            continue
        if line.startswith('—') or line.startswith('- '):
            parts.append(f'<p style="margin:4px 0 4px 16px; color:var(--text-light); font-size:0.92rem;">{esc(line)}</p>')
        else:
            parts.append(f'<p style="color:var(--text-light); font-size:0.92rem; margin-bottom:10px;">{esc(line)}</p>')
    return '\n            '.join(parts)

# Build TOC
toc_items = []
for w in weeks_reversed:
    toc_items.append(
        f'<a href="#week-{w["num"]}" class="toc-link">'
        f'<strong>{w["num"]}.</strong> {esc(w["title"])}</a>'
    )

# Build week sections
week_sections = []
for w in weeks_reversed:
    posts_html = []
    for p in w['posts']:
        ph = make_post_html(p)
        if ph.strip():
            posts_html.append(f'<div style="margin-bottom:16px; padding:16px 20px; background:#fff; border:1px solid var(--border-light); border-radius:8px;">\n            {ph}\n          </div>')

    week_sections.append(f'''
      <div id="week-{w['num']}" style="margin-bottom:50px;">
        <div style="display:flex; align-items:baseline; gap:12px; margin-bottom:20px;">
          <span style="font-size:0.8rem; font-weight:600; color:var(--brand); background:var(--border-light); padding:4px 12px; border-radius:4px;">Неделя {w['num']}</span>
          <h3 style="font-size:1.3rem; margin:0;">{esc(w['title'])}</h3>
        </div>
        {"".join(posts_html)}
      </div>''')

output = '''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="Азбука медицинской науки — статьи о научном письме, методологии и публикациях. Индекс Хирша.">
  <title>Блог — Индекс Хирша</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <link rel="stylesheet" href="styles.css">
  <style>
    .page-hero {
      padding: 130px 0 60px;
      background: linear-gradient(135deg, #ecfdf5, #d1fae5);
      text-align: center;
    }
    .page-hero h1 { font-size: 2.75rem; margin-bottom: 16px; }
    .page-hero p { font-size: 1.1rem; color: var(--text-light); max-width: 560px; margin: 0 auto; }
    .toc-sidebar {
      position: sticky; top: 90px;
      max-height: calc(100vh - 120px); overflow-y: auto;
      padding-right: 20px;
    }
    .toc-link {
      display: block; padding: 6px 0; font-size: 0.85rem;
      color: var(--text-light); text-decoration: none;
      border-bottom: 1px solid var(--border-light);
    }
    .toc-link:hover { color: var(--brand); }
    .blog-layout {
      display: grid; grid-template-columns: 240px 1fr; gap: 40px;
      align-items: start;
    }
    @media (max-width: 900px) {
      .blog-layout { grid-template-columns: 1fr; }
      .toc-sidebar { position: static; max-height: none; }
    }
  </style>
</head>
<body>
  <nav>
    <div class="container nav-inner">
      <a href="index.html" class="logo">
        <img src="assets/logo-main.jpg" alt="[h]">
        <span class="logo-text">Индекс Хирша</span>
      </a>
      <div style="display:flex; align-items:center; gap:28px;">
        <div class="menu">
          <a href="education.html">Обучение</a>
          <a href="club.html">Клуб</a>
          <a href="consulting.html">Консалтинг</a>
          <a href="blog.html" class="active">Блог</a>
        </div>
        <a href="https://t.me/hirsch_index_school" class="btn btn-primary btn-sm" style="white-space:nowrap;">
          <i class="fab fa-telegram" style="margin-right:6px;"></i>Telegram
        </a>
        <button class="mobile-toggle" onclick="toggleMobile()" aria-label="Меню"><i class="fas fa-bars"></i></button>
      </div>
    </div>
  </nav>
  <div class="mobile-menu" id="mobileMenu">
    <a href="education.html">Обучение</a><a href="club.html">Клуб</a>
    <a href="consulting.html">Консалтинг</a><a href="blog.html">Блог</a>
  </div>

  <section class="page-hero">
    <div class="container">
      <span class="section-badge">Блог</span>
      <h1>Азбука медицинской науки</h1>
      <p>Статьи о научном письме, методологии исследований и секретах публикаций</p>
    </div>
  </section>

  <section>
    <div class="container">
      <div class="blog-layout">
        <div class="toc-sidebar">
          <h4 style="margin-bottom:12px; font-size:0.95rem;">Оглавление</h4>
          PLACEHOLDER_TOC
        </div>
        <div>
          PLACEHOLDER_WEEKS
        </div>
      </div>
    </div>
  </section>

  <footer>
    <div class="container">
      <div class="footer-grid">
        <div>
          <h4>Индекс Хирша</h4>
          <div class="footer-links">
            <a href="education.html">Обучение</a><a href="club.html">Клуб</a>
            <a href="consulting.html">Консалтинг</a><a href="blog.html">Блог</a>
          </div>
        </div>
        <div>
          <h4>Контакты</h4>
          <div class="footer-links">
            <a href="https://t.me/+79854770449"><i class="fab fa-telegram" style="width:18px;"></i> Telegram</a>
            <a href="https://wa.me/79854770449"><i class="fab fa-whatsapp" style="width:18px;"></i> WhatsApp</a>
            <a href="mailto:zhigalovmd@yandex.ru"><i class="fas fa-envelope" style="width:18px;"></i> zhigalovmd@yandex.ru</a>
          </div>
        </div>
        <div>
          <h4>Соцсети</h4>
          <div class="footer-links">
            <a href="https://t.me/hirsch_index_school"><i class="fab fa-telegram" style="width:18px;"></i> Telegram-канал</a>
            <a href="https://vk.com/club235429996" target="_blank"><i class="fab fa-vk" style="width:18px;"></i> ВКонтакте</a>
            <a href="https://max.ru/join/TmlfyQ5T5BJu-iLZlOYbZolsFX2vrBDQ8t8jaKfz3P0" target="_blank"><i class="fas fa-comment-dots" style="width:18px;"></i> MAX</a>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <span>&copy; 2026 Индекс Хирша. Все права защищены.</span>
        <a href="offer.html">Публичная оферта</a>
      </div>
    </div>
  </footer>
  <script>function toggleMobile(){document.getElementById('mobileMenu').classList.toggle('open');}</script>
</body>
</html>'''

output = output.replace('PLACEHOLDER_TOC', '\n          '.join(toc_items))
output = output.replace('PLACEHOLDER_WEEKS', ''.join(week_sections))

with open(r'C:\Моя папка\1. Наука\004 Контент\Сайты\Индекс Хирша (RU)\blog.html', 'w', encoding='utf-8') as f:
    f.write(output)

print('blog.html generated successfully')
print(f'File size: {len(output):,} chars')
