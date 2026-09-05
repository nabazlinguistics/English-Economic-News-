import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import fitz
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

FILES = [
    ("corpus images.jpg", "https://firestorage.ai/ja/f/KjPqP1eqEl_e", "corpus-images.jpg", False),
    ("corpus images2.jpg", "https://firestorage.ai/ja/f/n7FqxhTeT_gy", "corpus-images2.jpg", False),
    ("Concordance a an(1).pdf", "https://firestorage.ai/ja/f/lW56MMJXGNRI", "concordance-a-an.pdf", False),
    ("Concordance a(20260905-221744).pdf", "https://firestorage.ai/ja/f/u4m3ecZ74Ahb", "concordance-a.pdf", False),
    ("Concordance an only(1).pdf", "https://firestorage.ai/ja/f/zmxKl98LzmMQ", "concordance-an.pdf", False),
    ("Concordance the(1).pdf", "https://firestorage.ai/ja/f/YBDk_Q5FHzSQ", "concordance-the.pdf", False),
    ("Concordance zero article perfect. landsscape.pdf", "https://firestorage.ai/ja/f/Ro4cHgbJdLC6", "concordance-zero-landscape.pdf", False),
    ("Concordance zero article portrait(1).pdf", "https://firestorage.ai/ja/f/P9mDIW82gxH_", "concordance-zero-portrait.pdf", False),
    ("Concordance zero article.pdf", "https://firestorage.ai/ja/f/y8FzZvPwSfC5", "concordance-zero-article.pdf", False),
    ("Concordance zero(20260905-221743).pdf", "https://firestorage.ai/ja/f/b2wNZSipBVti", "concordance-zero.pdf", False),
    ("evidence jpg zero articles.jpg", "https://firestorage.ai/ja/f/IM1MamhsLUJy", "zero-article-evidence.jpg", False),
    ("eda1ddae-6fb1-4672-a6fd-3e8edcfbb78c.docx", "https://firestorage.ai/ja/f/sYEoo9Yf9hwD", "sketchengine-antconc-crosscheck.docx", False),
    ("Daily_Check_Economic_News_2026_Clean(3).docx", "https://firestorage.ai/ja/f/rhXHXpzXYoEy", "daily-check-economic-news-2026.docx", False),
    ("Interrater_Reliability_Rater_2026_interactive_fillable_updated(3).pdf", "https://firestorage.ai/ja/f/mMWhUa-vss4e", "interrater-reliability.pdf", False),
    ("R2_reference_coding(5).docx", "https://firestorage.ai/ja/f/zqFwIXb4J1us", "r2-reference-coding.docx", False),
    ("Gmail - NYTimes Digital Subscription Order Confirmation.pdf", "https://firestorage.ai/ja/f/d6weQOHIKlEG", "nytimes-access-public.pdf", True),
    ("Gmail - Re_ Republishing query finical times(1).pdf", "https://firestorage.ai/ja/f/pBpCQlJzh-SS", "financial-times-response-public.pdf", True),
    ("Gmail - RE_ Sketch Engine feedback from nms.elt [Ticket#7818617](1).pdf", "https://firestorage.ai/ja/f/AuQazvh1AWKX", "sketch-engine-support-public.pdf", True),
    ("Gmail - Request for Permission to Use Financial Times Articles for Non-Commercial Linguistic Corpus Analysis.pdf", "https://firestorage.ai/ja/f/SrdB3WzC9RK9", "financial-times-permission-request-public.pdf", True),
    ("Gmail - Thank you for subscribing to Bloomberg.com.pdf", "https://firestorage.ai/ja/f/FYhljkJxP_oB", "bloomberg-access-public.pdf", True),
    ("Gmail - Welcome to The Wall Street Journal.pdf", "https://firestorage.ai/ja/f/W8EkxxfLYKYE", "wsj-access-public.pdf", True),
]

OUT = Path("appendix")
TMP = Path(".appendix_tmp")
OUT.mkdir(exist_ok=True)
TMP.mkdir(exist_ok=True)


def candidate_controls(page, filename):
    seen = set()
    candidates = []
    patterns = [filename, "download", "ダウンロード", "open", "開く", "save", "保存"]
    for pat in patterns:
        try:
            for kind in ("link", "button"):
                loc = page.get_by_role(kind, name=re.compile(re.escape(pat), re.I))
                count = min(loc.count(), 10)
                for i in range(count):
                    el = loc.nth(i)
                    key = (kind, el.inner_text(timeout=1000) if el.is_visible() else "")
                    if key not in seen and el.is_visible():
                        seen.add(key)
                        candidates.append(el)
        except Exception:
            pass
    try:
        loc = page.locator('a[href*="download"], a[download], button[data-download], [role="button"][data-download]')
        for i in range(min(loc.count(), 20)):
            el = loc.nth(i)
            if el.is_visible():
                candidates.append(el)
    except Exception:
        pass
    return candidates


def try_direct_href(context, page, el, dest):
    try:
        href = el.get_attribute("href")
        if not href:
            return False
        absolute = urljoin(page.url, href)
        response = context.request.get(absolute, timeout=30000)
        ctype = (response.headers.get("content-type") or "").lower()
        dispo = (response.headers.get("content-disposition") or "").lower()
        body = response.body()
        if response.ok and body and ("attachment" in dispo or "application/pdf" in ctype or "image/" in ctype or "officedocument" in ctype or "octet-stream" in ctype):
            Path(dest).write_bytes(body)
            return True
    except Exception:
        return False
    return False


def download_share(context, page, share_url, filename, dest):
    print(f"Opening {share_url} for {filename}")
    page.goto(share_url, wait_until="domcontentloaded", timeout=60000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    time.sleep(2)

    # Try anchors that already point to downloadable media.
    for el in candidate_controls(page, filename):
        if try_direct_href(context, page, el, dest):
            print(f"Downloaded via direct href: {filename}")
            return

    # Click through up to three screens, looking for a browser download each time.
    for _ in range(3):
        controls = candidate_controls(page, filename)
        print("Candidate controls:", [c.inner_text(timeout=1000)[:120] for c in controls[:10]])
        for el in controls[:20]:
            try:
                with page.expect_download(timeout=8000) as info:
                    el.click(timeout=5000)
                dl = info.value
                dl.save_as(str(dest))
                print(f"Downloaded by click: {filename}")
                return
            except PlaywrightTimeoutError:
                try:
                    el.click(timeout=3000)
                    page.wait_for_timeout(1200)
                except Exception:
                    pass
                if Path(dest).exists() and Path(dest).stat().st_size > 0:
                    return
                if try_direct_href(context, page, el, dest):
                    return
            except Exception:
                pass
        # Fallback: inspect all visible links and click likely single-file entries.
        links = page.locator("a")
        for i in range(min(links.count(), 100)):
            el = links.nth(i)
            try:
                text = (el.inner_text(timeout=500) or "").strip()
                href = el.get_attribute("href") or ""
                if filename.lower() in text.lower() or any(k in href.lower() for k in ("download", "file", "object")):
                    if try_direct_href(context, page, el, dest):
                        return
            except Exception:
                pass
        page.wait_for_timeout(1000)

    # Diagnostics to make failures easy to fix from Actions logs.
    print("Page title:", page.title())
    print("Final URL:", page.url)
    try:
        print("Visible text sample:", page.locator("body").inner_text(timeout=5000)[:5000])
    except Exception:
        pass
    try:
        anchors = page.locator("a")
        print("Anchors:")
        for i in range(min(anchors.count(), 80)):
            a = anchors.nth(i)
            print(i, (a.inner_text(timeout=500) or "")[:100], a.get_attribute("href"))
    except Exception:
        pass
    raise RuntimeError(f"Could not download {filename} from {share_url}")


def redact_pdf(src, dest):
    doc = fitz.open(src)
    sensitive_email = re.compile(r"nms\.elt@gmail\.com", re.I)
    long_id = re.compile(r"\b\d{8,}\b")
    account_code = re.compile(r"\b(?:BB-\d{4}-\d{4}|\d{4})\b")
    card_context = re.compile(r"(?:mastercard|visa|credit card)", re.I)

    for page in doc:
        # Remove live links from public correspondence copies.
        for link in list(page.get_links()):
            try:
                page.delete_link(link)
            except Exception:
                pass

        words = page.get_text("words")
        for x0, y0, x1, y1, word, *_ in words:
            w = word.strip()
            redact = False
            if sensitive_email.search(w) or long_id.search(w) or account_code.fullmatch(w):
                redact = True
            if redact:
                page.add_redact_annot(fitz.Rect(x0, y0, x1, y1), fill=(1, 1, 1))

        # Redact Gmail print URLs and the whole line they occupy.
        for needle in ("https://mail.google.com", "nms.elt@gmail.com", "BB-5088-3824"):
            for r in page.search_for(needle):
                page.add_redact_annot(fitz.Rect(0, max(0, r.y0 - 2), page.rect.width, min(page.rect.height, r.y1 + 2)), fill=(1, 1, 1))

        # Redact last four card digits when they appear on a payment-method line.
        blocks = page.get_text("blocks")
        for b in blocks:
            text = b[4] if len(b) > 4 else ""
            if card_context.search(text):
                for m in re.finditer(r"\b\d{4}\b", text):
                    token = m.group(0)
                    for r in page.search_for(token):
                        page.add_redact_annot(r, fill=(1, 1, 1))

        page.apply_redactions()
    doc.save(dest, garbage=4, deflate=True, clean=True)
    doc.close()


def convert_docx_to_pdf(docx_paths):
    if not docx_paths:
        return
    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", "--outdir", str(OUT)] + [str(p) for p in docx_paths]
    print("Converting DOCX files to PDF for browser viewing")
    result = os.system(" ".join('"'+x.replace('"','\\"')+'"' for x in cmd))
    if result != 0:
        raise RuntimeError("LibreOffice PDF conversion failed")


def main():
    downloaded_docx = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        for original_name, share_url, repo_name, sensitive in FILES:
            temp_path = TMP / repo_name
            download_share(context, page, share_url, original_name, temp_path)
            if not temp_path.exists() or temp_path.stat().st_size == 0:
                raise RuntimeError(f"Empty download: {original_name}")
            if sensitive and temp_path.suffix.lower() == ".pdf":
                public_path = OUT / repo_name
                redact_pdf(temp_path, public_path)
                print(f"Created redacted public copy: {public_path}")
            else:
                public_path = OUT / repo_name
                public_path.write_bytes(temp_path.read_bytes())
            if public_path.suffix.lower() == ".docx":
                downloaded_docx.append(public_path)
        browser.close()

    convert_docx_to_pdf(downloaded_docx)
    print("Imported appendix files:")
    for f in sorted(OUT.iterdir()):
        print(f, f.stat().st_size)


if __name__ == "__main__":
    main()
