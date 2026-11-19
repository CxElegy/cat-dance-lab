"""Build output/dashboard.html (self-contained; covers embedded as data URIs).

The dashboard embeds third-party cover frames, so it is gitignored and only shared privately.
"""
import base64, csv, io, json, os, statistics as st
from collections import Counter, defaultdict
from datetime import date
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda p: os.path.join(ROOT, p)

MODELS = [  # display order, short label, colour token
    ('Kling', '可灵 Kling', 'm1'),
    ('Seedance (Dreamina)', 'Seedance（即梦）', 'm2'),
    ('PixVerse', 'PixVerse', 'm3'),
    ('CapCut template', 'CapCut AI 模板', 'm4'),
    ('Higgsfield (aggregator)', 'Higgsfield*', 'm5'),
    ('Syntx (aggregator)', 'Syntx*', 'm6'),
    ('ImagineArt (aggregator)', 'ImagineArt*', 'm7'),
    ('Pollo AI (aggregator)', 'Pollo AI*', 'm8'),
    ('unknown', '未能归因', 'mu'),
]

def evidence_kind(ev):
    if ev.startswith('cover watermark'): return '水印'
    if ev.startswith('caption'): return '文案标注'
    if 'same account' in ev or 'same series' in ev or 'account posts' in ev: return '同账号推断'
    if ev.startswith('watch_shortform'): return '逐帧查无水印'
    return '仅画面'

def thumb(cid):
    p = R(f'output/thumbs/{cid}.jpg')
    if not os.path.exists(p): return ''
    im = Image.open(p).convert('RGB'); w, h = im.size
    im = im.resize((240, round(h * 240 / w)))
    b = io.BytesIO(); im.save(b, 'JPEG', quality=72)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

def main():
    allrows = list(csv.DictReader(open(R('data/samples.csv'), encoding='utf-8')))
    rows = [r for r in allrows if r['is_ai'] == 'yes' and r['is_cat_dance'] == 'yes']
    items = []
    for r in rows:
        items.append(dict(id=r['content_id'], p='IG' if r['platform'] == 'instagram' else 'TT', h=r['handle'], u=r['url'],
                          v=int(r['views']), x=float(r['outlier_x']), d=r['posted_at'], m=r['model'], c=r['confidence'],
                          ek=evidence_kind(r['model_evidence']), ev=r['model_evidence'], cap=r['caption'][:140],
                          t=thumb(r['content_id'])))
    stats = []
    g = defaultdict(list)
    for it in items: g[it['m']].append(it)
    for key, label, tok in MODELS:
        rs = g.get(key, [])
        if not rs: continue
        v = [i['v'] for i in rs]; x = [i['x'] for i in rs]
        stats.append(dict(key=key, label=label, tok=tok, n=len(rs), conf=sum(i['c'] == 'confirmed' for i in rs),
                          likely=sum(i['c'] == 'likely' for i in rs), ig=sum(i['p'] == 'IG' for i in rs),
                          tt=sum(i['p'] == 'TT' for i in rs), medv=st.median(v), meanv=st.mean(v),
                          medx=st.median(x), meanx=st.mean(x)))
    meta = dict(total=len(allrows), ai_dance=len(rows), unsure=sum(r['is_ai'] == 'unsure' for r in allrows),
                not_ai=sum(r['is_ai'] == 'no' for r in allrows),
                not_dance=sum(r['is_ai'] == 'yes' and r['is_cat_dance'] == 'no' for r in allrows),
                creators=len({i['h'] for i in items}), built=str(date.today()))
    tpl = open(R('scripts/dashboard_template.html'), encoding='utf-8').read()
    html = tpl.replace('/*__DATA__*/', 'const ITEMS=' + json.dumps(items, ensure_ascii=False) +
                       ';\nconst STATS=' + json.dumps(stats, ensure_ascii=False) +
                       ';\nconst META=' + json.dumps(meta, ensure_ascii=False) + ';')
    open(R('output/dashboard.html'), 'w', encoding='utf-8').write(html)
    print('dashboard', len(html) // 1024, 'KB;', meta)

if __name__ == '__main__':
    main()
