"""Parse vidIQ instagram/tiktok outlier_search markdown output into dicts."""
import re, sys, json

NUM = {'K': 1e3, 'M': 1e6, 'B': 1e9}
def num(s):
    s = s.replace(',', '')
    m = re.match(r'([\d.]+)([KMB]?)', s)
    return float(m.group(1)) * NUM.get(m.group(2), 1)

def parse(text, source):
    out, platform = [], None
    blocks = re.split(r'\n(?=\*\*@|## )', text)
    for b in blocks:
        if b.startswith('## '):
            platform = b[3:].split('\n')[0].strip().lower()
            b = b.split('\n', 1)[1] if '\n' in b else ''
            if not b.strip().startswith('**@'):
                continue
        b = b.strip()
        m = re.match(r'\*\*@([^*]+)\*\* — "(.*?)"\n\s+([\d.,]+[KMB]?) views \(([\d.,]+)x their median of [^)]*\) · ([\d.,]+[KMB]?) followers(?: · (\d+)s)? · posted (\d{4}-\d\d-\d\d)\n\s+(\S+)', b, re.S)
        if not m:
            continue
        rec = dict(platform=platform, handle=m.group(1), caption=m.group(2).replace('\n', ' ').strip(),
                   views=int(num(m.group(3))), outlier_x=float(m.group(4).replace(',', '')),
                   followers=int(num(m.group(5))), duration_s=m.group(6) or '',
                   posted_at=m.group(7), url=m.group(8), source=source)
        def field(name):
            mm = re.search(r'\*\*' + name + r'\*\*: (.*)', b)
            return mm.group(1).strip() if mm else ''
        rec['vidiq_concept'] = field('reel_concept') or field('tiktok_concept')
        mm = re.search(r'\n\s+style: (.*)', b); rec['vidiq_style'] = mm.group(1).strip() if mm else ''
        mm = re.search(r'\n\s+barrier: (.*)', b); rec['vidiq_tool_guess'] = mm.group(1).strip() if mm else ''
        rec['content_id'] = rec['url'].rstrip('/').split('/')[-1]
        out.append(rec)
    return out

if __name__ == '__main__':
    recs = parse(open(sys.argv[1], encoding='utf-8').read(), sys.argv[2])
    json.dump(recs, sys.stdout, ensure_ascii=False, indent=0)
