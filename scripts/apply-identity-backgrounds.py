from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

REPO = Path('.')
ASSETS = REPO / 'assets'
ASSETS.mkdir(exist_ok=True)

DOWNLOADS = [
    ('https://firestorage.ai/ja/f/FimLi9mmaK5s', ASSETS / 'researcher-ranya-campus.png'),
    ('https://firestorage.ai/ja/f/ZxQuUoqvEZ0f', ASSETS / 'supervisor-qaladze-campus.png'),
]


def download_one(page, url, dest):
    print(f'Opening {url}')
    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    try:
        page.wait_for_load_state('networkidle', timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(1200)

    candidates = []
    for selector in [
        'a[download]',
        'a:has-text("ダウンロード")',
        'button:has-text("ダウンロード")',
        'a:has-text("Download")',
        'button:has-text("Download")',
    ]:
        try:
            loc = page.locator(selector)
            for i in range(min(loc.count(), 8)):
                el = loc.nth(i)
                if el.is_visible():
                    candidates.append(el)
        except Exception:
            pass

    try:
        for kind in ('link', 'button'):
            loc = page.get_by_role(kind)
            for i in range(min(loc.count(), 30)):
                el = loc.nth(i)
                if el.is_visible():
                    txt = (el.inner_text(timeout=500) or '').strip().lower()
                    if txt and ('.png' in txt or '.jpg' in txt or '.jpeg' in txt):
                        candidates.append(el)
    except Exception:
        pass

    seen = set()
    for el in candidates:
        try:
            key = (el.evaluate('(e)=>e.tagName'), el.inner_text(timeout=500))
        except Exception:
            key = id(el)
        if key in seen:
            continue
        seen.add(key)
        try:
            with page.expect_download(timeout=9000) as info:
                el.click(timeout=5000)
            info.value.save_as(str(dest))
            print(f'Downloaded {dest} ({dest.stat().st_size} bytes)')
            return
        except PlaywrightTimeoutError:
            try:
                el.click(timeout=3000)
                page.wait_for_timeout(800)
            except Exception:
                pass
        except Exception:
            pass
    raise RuntimeError(f'Could not download asset from {url}')


def patch_index():
    path = REPO / 'index.html'
    text = path.read_text(encoding='utf-8')
    old_researcher = '<button class="identity-card research-profile"><span>Researcher</span><strong>Nabaz Muhammad Saeed</strong><small>View research details ↗</small></button>'
    new_researcher = '<button class="identity-card research-profile researcher-campus"><span>Researcher</span><strong>Nabaz Muhammad Saeed</strong><small>View research details ↗</small></button>'
    old_supervisor = '<button class="identity-card research-profile"><span>Supervisor</span><strong>Asst. Prof. Dr. Salih Ibrahim Ahmed</strong><small>View supervision details ↗</small></button>'
    new_supervisor = '<button class="identity-card research-profile supervisor-campus"><span>Supervisor</span><strong>Asst. Prof. Dr. Salih Ibrahim Ahmed</strong><small>View supervision details ↗</small></button>'
    if 'researcher-campus' not in text:
        if old_researcher not in text:
            raise RuntimeError('Researcher identity card not found.')
        text = text.replace(old_researcher, new_researcher, 1)
    if 'supervisor-campus' not in text:
        if old_supervisor not in text:
            raise RuntimeError('Supervisor identity card not found.')
        text = text.replace(old_supervisor, new_supervisor, 1)
    path.write_text(text, encoding='utf-8')


def patch_styles():
    path = REPO / 'styles.css'
    css = path.read_text(encoding='utf-8')
    marker = '/* Identity card campus backgrounds */'
    if marker in css:
        return
    enhancement = r'''

/* Identity card campus backgrounds */
.identity-card.researcher-campus,
.identity-card.supervisor-campus{
  position:relative;
  overflow:hidden;
  isolation:isolate;
  min-height:138px;
  background:#fff;
}
.identity-card.researcher-campus::after,
.identity-card.supervisor-campus::after{
  content:"";
  position:absolute;
  inset:0;
  z-index:0;
  background-repeat:no-repeat;
  background-size:cover;
  transition:transform .25s ease,opacity .25s ease;
}
.identity-card.researcher-campus::before,
.identity-card.supervisor-campus::before{
  content:"";
  position:absolute;
  inset:0;
  z-index:1;
  background:linear-gradient(90deg,rgba(255,255,255,.95) 0%,rgba(255,255,255,.86) 44%,rgba(255,255,255,.67) 100%);
}
.identity-card.researcher-campus::after{
  background-image:url('assets/researcher-ranya-campus.png');
  background-position:center 48%;
  opacity:.55;
}
.identity-card.supervisor-campus::after{
  background-image:url('assets/supervisor-qaladze-campus.png');
  background-position:center 53%;
  opacity:.58;
}
.identity-card.researcher-campus > *,
.identity-card.supervisor-campus > *{
  position:relative;
  z-index:2;
}
.identity-card.researcher-campus:hover::after,
.identity-card.researcher-campus:focus-visible::after,
.identity-card.supervisor-campus:hover::after,
.identity-card.supervisor-campus:focus-visible::after{
  transform:scale(1.025);
  opacity:.66;
}
.identity-card.researcher-campus:hover,
.identity-card.researcher-campus:focus-visible,
.identity-card.supervisor-campus:hover,
.identity-card.supervisor-campus:focus-visible{
  background:#fff;
}
@media(max-width:560px){
  .identity-card.researcher-campus,
  .identity-card.supervisor-campus{min-height:126px}
  .identity-card.researcher-campus::before,
  .identity-card.supervisor-campus::before{background:rgba(255,255,255,.78)}
}
'''
    path.write_text(css + enhancement, encoding='utf-8')


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        for url, dest in DOWNLOADS:
            download_one(page, url, dest)
        browser.close()
    patch_index()
    patch_styles()


if __name__ == '__main__':
    main()
