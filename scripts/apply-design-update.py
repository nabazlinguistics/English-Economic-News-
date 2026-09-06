import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

REPO = Path('.')
ASSETS = REPO / 'assets'
APPENDIX = REPO / 'appendix'
ASSETS.mkdir(exist_ok=True)
APPENDIX.mkdir(exist_ok=True)

DOWNLOADS = [
    (
        'https://firestorage.ai/ja/f/xRnxv993nFcW',
        APPENDIX / 'sketch-engine-antconc-similar-results.pdf',
    ),
    (
        'https://firestorage.ai/ja/f/9obElipl_1cv',
        ASSETS / 'university-of-raparin-logo.png',
    ),
]


def download_one(page, url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        print(f'Already present: {dest}')
        return
    print(f'Opening {url}')
    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    try:
        page.wait_for_load_state('networkidle', timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(1500)

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

    # The single-file share page also exposes the filename as a clickable control.
    try:
        for kind in ('link', 'button'):
            loc = page.get_by_role(kind)
            for i in range(min(loc.count(), 30)):
                el = loc.nth(i)
                if el.is_visible():
                    txt = (el.inner_text(timeout=500) or '').strip()
                    if txt and ('pdf' in txt.lower() or 'png' in txt.lower()):
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
                page.wait_for_timeout(900)
            except Exception:
                pass
        except Exception:
            pass

    print('Visible page text:', page.locator('body').inner_text(timeout=5000)[:4000])
    raise RuntimeError(f'Could not download asset from {url}')


def patch_index():
    path = REPO / 'index.html'
    text = path.read_text(encoding='utf-8')

    text = text.replace(
        '<summary><span>Corpus construction and concordance evidence</span><small>12 materials</small></summary>',
        '<summary><span>Corpus construction and concordance evidence</span><small>13 materials</small></summary>'
    )

    anchor = '<a class="appendix-item-link" href="appendix/sketchengine-antconc-crosscheck.pdf"><span class="appendix-type doc">PDF</span><div><strong>eda1ddae-6fb1-4672-a6fd-3e8edcfbb78c.docx</strong><small>Sketch Engine and AntConc concordance cross-check evidence</small></div><span class="appendix-action">View ↗</span></a>'
    new_item = '<a class="appendix-item-link" href="appendix/sketch-engine-antconc-similar-results.pdf"><span class="appendix-type pdf">PDF</span><div><strong>Sketch Engine and AntConc Similar Results.pdf</strong><small>Side-by-side concordance evidence showing comparable results in Sketch Engine and AntConc</small></div><span class="appendix-action">View ↗</span></a>'
    if 'sketch-engine-antconc-similar-results.pdf' not in text:
        if anchor not in text:
            raise RuntimeError('Could not locate the existing Sketch Engine/AntConc appendix item.')
        text = text.replace(anchor, anchor + '\n          ' + new_item)

    # Correct visible spelling/capitalization while preserving permanent file paths.
    corrections = {
        'Concordance zero article perfect. landsscape.pdf': 'Concordance zero article perfect landscape.pdf',
        'Gmail - Re_ Republishing query finical times(1).pdf': 'Gmail - Re_ Republishing query Financial Times(1).pdf',
        'Gmail - NYTimes Digital Subscription Order Confirmation.pdf': 'Gmail - New York Times Digital Subscription Order Confirmation.pdf',
        'Interrater_Reliability_Rater_2026_interactive_fillable_updated(3).pdf': 'Inter-rater_Reliability_Rater_2026_interactive_fillable_updated(3).pdf',
    }
    for old, new in corrections.items():
        text = text.replace(old, new)

    path.write_text(text, encoding='utf-8')
    print('Updated Appendix Materials and corrected visible labels.')


def patch_styles():
    path = REPO / 'styles.css'
    css = path.read_text(encoding='utf-8')
    marker = '/* September 2026 visual refinement: Raparin watermark and outlet logos */'
    if marker in css:
        print('Visual refinement CSS already present.')
        return

    enhancement = r'''

/* September 2026 visual refinement: Raparin watermark and outlet logos */
body{
  background-color:var(--paper);
  background-image:
    linear-gradient(rgba(245,247,244,.91),rgba(245,247,244,.91)),
    url('assets/university-of-raparin-logo.png');
  background-repeat:no-repeat,no-repeat;
  background-position:center top,center 112px;
  background-size:auto,520px auto;
  background-attachment:fixed,fixed;
}

/* Softer outlet colours with each outlet's own logo as a subtle background mark. */
.outlet-card{
  position:relative;
  overflow:hidden;
  isolation:isolate;
  color:var(--ink);
  border:1px solid color-mix(in srgb,var(--outlet) 24%,white);
  box-shadow:0 8px 20px rgba(18,32,29,.08);
}
.outlet-card::before{
  content:"";
  position:absolute;
  inset:12px 12px 12px 42%;
  z-index:-1;
  background-image:var(--outlet-logo);
  background-repeat:no-repeat;
  background-position:center;
  background-size:var(--logo-size,82%) auto;
  opacity:.16;
  transition:opacity .18s ease,transform .18s ease;
}
.outlet-card::after{
  content:"";
  position:absolute;
  inset:0;
  z-index:-2;
  background:linear-gradient(110deg,rgba(255,255,255,.96) 0%,rgba(255,255,255,.88) 54%,rgba(255,255,255,.66) 100%);
}
.outlet-card:hover,.outlet-card:focus-visible{
  box-shadow:0 13px 28px rgba(18,32,29,.13);
  filter:none;
}
.outlet-card:hover::before,.outlet-card:focus-visible::before{opacity:.24;transform:scale(1.035)}
.outlet-card strong{color:var(--ink)}
.outlet-card span{color:#596763}
.outlet-card em{color:var(--outlet)}

.outlet-pill{
  color:var(--ink);
  border:1px solid color-mix(in srgb,var(--outlet) 22%,white);
  box-shadow:0 3px 10px rgba(18,32,29,.07);
}
.outlet-pill b{color:var(--outlet)}

.outlet-card.outlet-ap,.outlet-pill.outlet-ap{background:#fff2f2}
.outlet-card.outlet-bbc,.outlet-pill.outlet-bbc{background:#fff0f0}
.outlet-card.outlet-bloomberg,.outlet-pill.outlet-bloomberg{background:#f3f0fb}
.outlet-card.outlet-cnbc,.outlet-pill.outlet-cnbc{background:#edf6ff}
.outlet-card.outlet-cnn,.outlet-pill.outlet-cnn{background:#fff0f0}
.outlet-card.outlet-nyt,.outlet-pill.outlet-nyt{background:#f3f3f3}
.outlet-card.outlet-reuters,.outlet-pill.outlet-reuters{background:#fff5ed}
.outlet-card.outlet-guardian,.outlet-pill.outlet-guardian{background:#eef4fb}
.outlet-card.outlet-telegraph,.outlet-pill.outlet-telegraph{background:#eff6fb}
.outlet-card.outlet-wsj,.outlet-pill.outlet-wsj{background:#f2f4f5}

.outlet-ap{--outlet-logo:url('https://commons.wikimedia.org/wiki/Special:Redirect/file/Associated_Press_logo.svg');--logo-size:86%}
.outlet-bbc{--outlet-logo:url('https://commons.wikimedia.org/wiki/Special:Redirect/file/BBC_News_2022_%28Alt%2C_boxed%29.svg');--logo-size:76%}
.outlet-bloomberg{--outlet-logo:url('https://commons.wikimedia.org/wiki/Special:Redirect/file/New_Bloomberg_Logo.svg');--logo-size:88%}
.outlet-cnbc{--outlet-logo:url('https://commons.wikimedia.org/wiki/Special:Redirect/file/CNBC_2025.svg');--logo-size:62%}
.outlet-cnn{--outlet-logo:url('https://commons.wikimedia.org/wiki/Special:Redirect/file/CNN_Business_logo.svg');--logo-size:78%}
.outlet-nyt{--outlet-logo:url('https://commons.wikimedia.org/wiki/Special:Redirect/file/The_New_York_Times_Logo.svg');--logo-size:92%}
.outlet-reuters{--outlet-logo:url('https://commons.wikimedia.org/wiki/Special:Redirect/file/Reuters_Logo.svg');--logo-size:78%}
.outlet-guardian{--outlet-logo:url('https://commons.wikimedia.org/wiki/Special:Redirect/file/The_Guardian_2018.svg');--logo-size:76%}
.outlet-telegraph{--outlet-logo:url('https://commons.wikimedia.org/wiki/Special:Redirect/file/The_Telegraph.svg');--logo-size:92%}
.outlet-wsj{--outlet-logo:url('https://commons.wikimedia.org/wiki/Special:Redirect/file/WSJ_Logo.svg');--logo-size:94%}

@media(max-width:650px){
  body{background-position:center top,center 104px;background-size:auto,300px auto}
  .outlet-card::before{inset:14px 12px 14px 50%;opacity:.13}
}
'''
    path.write_text(css + enhancement, encoding='utf-8')
    print('Added Raparin watermark and lighter logo-backed outlet styling.')


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
