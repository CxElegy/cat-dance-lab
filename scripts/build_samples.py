"""Merge raw vidIQ results + manual labels + evidence into data/samples.csv."""
import csv, json, re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from parse_vidiq import parse
from labels import ORIG, SUPP1, SUPP2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = lambda p: os.path.join(ROOT, p)

def load():
    recs = []
    with open(R('data/raw/vidiq_search_2026-11-17_from_paste.tsv'), encoding='utf-8') as f:
        for i, row in enumerate(csv.DictReader(f, delimiter='\t')):
            row.update(views=int(row['views']), outlier_x=float(row['outlier_x']), followers=int(row['followers']),
                       source='orig_2026-11-17', content_id=row['url'].rstrip('/').split('/')[-1])
            row['label'] = ORIG[i]; recs.append(row)
    for name, labels in (('supp1', SUPP1), ('supp2', SUPP2)):
        txt = open(R(f'data/raw/vidiq_search_raw_2026-11-19_{name}.txt'), encoding='utf-8').read()
        for i, row in enumerate(parse(txt, name)):
            row['label'] = labels.get(i, ('n', 'n', 'unlabelled'))
            recs.append(row)
    seen, out = set(), []
    for r in recs:                       # first occurrence wins (original file first)
        if r['content_id'] in seen: continue
        seen.add(r['content_id']); out.append(r)
    return out

# caption / tag evidence -> (model, confidence, evidence)
CAPTION_RULES = [
    (r'klingai|kling ai|#kling\b|可灵', 'Kling', 'caption tag #klingai'),
    (r'dreamina', 'Seedance (Dreamina)', 'caption @dreamina_ai'),
    (r'pixverse', 'PixVerse', 'caption @PixVerse / #pixverse'),
    (r'higgsfield|힉스필드', 'Higgsfield (aggregator)', 'caption: made with Higgsfield'),
    (r'syntx', 'Syntx (aggregator)', 'caption: created with Syntx'),
    (r'pollo', 'Pollo AI (aggregator)', 'caption: created with Pollo AI'),
    (r'imagineart', 'ImagineArt (aggregator)', 'caption: created with ImagineArt'),
    (r'creativefabrica', 'Creative Fabrica Studio AI', 'caption: made with Studio AI'),
    (r'capcut', 'CapCut template', 'caption #capcut (template)'),
]
# account-level evidence: same account names a tool on other posts in the sample -> likely
ACCOUNT_HINTS = {
    'neko.manma2024': ('Kling', 'same account tags #klingai on other posts'),
    'neko.manma0': ('Kling', 'same account tags #klingai on other posts'),
    'josechari_world': ('Kling', 'same series tagged #KlingAI on another post'),
    'the.meow.moves': ('Seedance (Dreamina)', 'same account tags @dreamina_ai on another post'),
    'kosowska.ai': ('Higgsfield (aggregator)', 'account posts are all Higgsfield Genjutsu'),
    'bellvtrix.ai': ('Higgsfield (aggregator)', 'account posts are all Higgsfield Genjutsu'),
    'snowpllanet': ('Higgsfield (aggregator)', 'account posts are all Higgsfield Genjutsu'),
}
# visual evidence (watermarks / platform labels) filled in from cover checks + watch_shortform
VISUAL = {}
if os.path.exists(R('data/visual_evidence.json')):
    VISUAL = json.load(open(R('data/visual_evidence.json'), encoding='utf-8'))

def attribute(r):
    ai, dance, _ = r['label']
    if ai != 'y' or dance != 'y':
        return '', '', ''
    v = VISUAL.get(r['content_id'])
    if v and v.get('model'):
        return v['model'], v.get('confidence', 'confirmed'), v['evidence']
    cap = r['caption'].lower()
    for pat, model, ev in CAPTION_RULES:
        if re.search(pat, cap):
            return model, 'confirmed', ev
    if r['handle'] in ACCOUNT_HINTS:
        m, ev = ACCOUNT_HINTS[r['handle']]
        return m, 'likely', ev
    ev = v['evidence'] if v else 'visual features only'
    return 'unknown', 'unknown', ev

FIELDS = ['id', 'platform', 'handle', 'url', 'caption', 'views', 'outlier_x', 'followers', 'posted_at', 'duration_s',
          'vidiq_concept', 'vidiq_style', 'vidiq_tool_guess', 'is_ai', 'is_cat_dance', 'model', 'model_evidence',
          'confidence', 'notes', 'source', 'content_id']

def main():
    rows = []
    for i, r in enumerate(load(), 1):
        ai, dance, note = r['label']
        model, conf, ev = attribute(r)
        rows.append({**{k: r.get(k, '') for k in FIELDS}, 'id': i,
                     'is_ai': {'y': 'yes', 'n': 'no', 'u': 'unsure'}[ai], 'is_cat_dance': {'y': 'yes', 'n': 'no'}[dance],
                     'model': model, 'model_evidence': ev, 'confidence': conf, 'notes': note})
    with open(R('data/samples.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, FIELDS); w.writeheader(); w.writerows(rows)
    keep = [r for r in rows if r['is_ai'] == 'yes' and r['is_cat_dance'] == 'yes']
    print('total', len(rows), '| ai+cat_dance', len(keep),
          '| by platform', {p: sum(r['platform'] == p for r in keep) for p in ('instagram', 'tiktok')},
          '| unsure', sum(r['is_ai'] == 'unsure' for r in rows))
    from collections import Counter
    print(Counter((r['model'], r['confidence']) for r in keep))

if __name__ == '__main__':
    main()
