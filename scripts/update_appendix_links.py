from pathlib import Path

path = Path('index.html')
text = path.read_text(encoding='utf-8')

links = {
    'https://firestorage.ai/ja/f/KjPqP1eqEl_e': 'appendix/corpus-images.jpg',
    'https://firestorage.ai/ja/f/n7FqxhTeT_gy': 'appendix/corpus-images2.jpg',
    'https://firestorage.ai/ja/f/lW56MMJXGNRI': 'appendix/concordance-a-an.pdf',
    'https://firestorage.ai/ja/f/u4m3ecZ74Ahb': 'appendix/concordance-a.pdf',
    'https://firestorage.ai/ja/f/zmxKl98LzmMQ': 'appendix/concordance-an.pdf',
    'https://firestorage.ai/ja/f/YBDk_Q5FHzSQ': 'appendix/concordance-the.pdf',
    'https://firestorage.ai/ja/f/Ro4cHgbJdLC6': 'appendix/concordance-zero-landscape.pdf',
    'https://firestorage.ai/ja/f/P9mDIW82gxH_': 'appendix/concordance-zero-portrait.pdf',
    'https://firestorage.ai/ja/f/y8FzZvPwSfC5': 'appendix/concordance-zero-article.pdf',
    'https://firestorage.ai/ja/f/b2wNZSipBVti': 'appendix/concordance-zero.pdf',
    'https://firestorage.ai/ja/f/IM1MamhsLUJy': 'appendix/zero-article-evidence.jpg',
    'https://firestorage.ai/ja/f/sYEoo9Yf9hwD': 'appendix/sketchengine-antconc-crosscheck.pdf',
    'https://firestorage.ai/ja/f/rhXHXpzXYoEy': 'appendix/daily-check-economic-news-2026.pdf',
    'https://firestorage.ai/ja/f/mMWhUa-vss4e': 'appendix/interrater-reliability.pdf',
    'https://firestorage.ai/ja/f/zqFwIXb4J1us': 'appendix/r2-reference-coding.pdf',
    'https://firestorage.ai/ja/f/d6weQOHIKlEG': 'appendix/nytimes-access-public.pdf',
    'https://firestorage.ai/ja/f/pBpCQlJzh-SS': 'appendix/financial-times-response-public.pdf',
    'https://firestorage.ai/ja/f/AuQazvh1AWKX': 'appendix/sketch-engine-support-public.pdf',
    'https://firestorage.ai/ja/f/SrdB3WzC9RK9': 'appendix/financial-times-permission-request-public.pdf',
    'https://firestorage.ai/ja/f/FYhljkJxP_oB': 'appendix/bloomberg-access-public.pdf',
    'https://firestorage.ai/ja/f/W8EkxxfLYKYE': 'appendix/wsj-access-public.pdf',
}

for old, new in links.items():
    text = text.replace(f'href="{old}" target="_blank" rel="noopener noreferrer"', f'href="{new}"')
    text = text.replace(f'href="{old}"', f'href="{new}"')

text = text.replace(
    'Click any material to open the original high-quality file in a new tab.',
    'Tap or click any material to view it directly. PDFs and images open in your browser on phones, tablets, and computers.'
)
text = text.replace(
    'Each item opens in a separate browser tab so the corpus dashboard remains available in the original tab.',
    'Materials are hosted permanently with this research website. Word documents are provided as browser-friendly PDF viewing copies; use your browser’s Back button to return to the dashboard.'
)
text = text.replace('<span class="appendix-type doc">DOCX</span><div><strong>eda1ddae-6fb1-4672-a6fd-3e8edcfbb78c.docx</strong>', '<span class="appendix-type doc">PDF</span><div><strong>eda1ddae-6fb1-4672-a6fd-3e8edcfbb78c.docx</strong>')
text = text.replace('<span class="appendix-type doc">DOCX</span><div><strong>Daily_Check_Economic_News_2026_Clean(3).docx</strong>', '<span class="appendix-type doc">PDF</span><div><strong>Daily_Check_Economic_News_2026_Clean(3).docx</strong>')
text = text.replace('<span class="appendix-type doc">DOCX</span><div><strong>R2_reference_coding(5).docx</strong>', '<span class="appendix-type doc">PDF</span><div><strong>R2_reference_coding(5).docx</strong>')
text = text.replace('>Open ↗</span>', '>View ↗</span>')

# Mark public correspondence copies clearly; personal identifiers were removed before publication.
privacy_notes = {
    'New York Times access documentation': 'New York Times access documentation · public copy with personal identifiers redacted',
    'Financial Times response regarding research use': 'Financial Times response regarding research use · public copy with personal identifiers redacted',
    'Sketch Engine support correspondence': 'Sketch Engine support correspondence · public copy with personal identifiers redacted',
    'Financial Times permission request': 'Financial Times permission request · public copy with personal identifiers redacted',
    'Bloomberg access documentation': 'Bloomberg access documentation · public copy with personal identifiers redacted',
    'Wall Street Journal access documentation': 'Wall Street Journal access documentation · public copy with personal identifiers redacted',
}
for old, new in privacy_notes.items():
    text = text.replace(f'<small>{old}</small>', f'<small>{new}</small>')

# Guard against accidentally leaving temporary Firestorage links behind.
if 'firestorage.ai/ja/f/' in text:
    raise SystemExit('Temporary Firestorage appendix links still remain in index.html')

path.write_text(text, encoding='utf-8')
print('Updated index.html to permanent same-site appendix links.')
