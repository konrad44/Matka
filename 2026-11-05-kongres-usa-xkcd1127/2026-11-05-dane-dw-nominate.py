import csv, collections, json, sys
D = sys.argv[1]
# measured 112th widths in the original image (seats), order from center outward
IMG112 = {
 'S': {'L': [63/3.5, 88/3.5, 34/3.5], 'R': [20/3.5, 67/3.5, 78/3.5]},
 'H': {'L': [80/0.97, 58/0.97, 49/0.97], 'R': [0.0, 71/0.97, 162/0.97]},
}
def side(ch, p):
    p = p.split('.')[0]
    if p == '100': return 'L'
    if p == '200': return 'R'
    if p == '328': return 'L' if ch == 'S' else 'R'
    return None
out = {}
for ch, fn in [('S', 'Sall_members.csv'), ('H', 'Hall_members.csv')]:
    rows = [r for r in csv.DictReader(open(f'{D}/{fn}')) if r['chamber'] in ('Senate','House') and int(r['congress']) >= 112 and r['nominate_dim1'] and r['state_abbrev'] not in ('AS','DC','GU','MP','PR','VI')]
    per = collections.defaultdict(list)
    for r in rows:
        s = side(ch, r['party_code'])
        if s is None: print('skip', r['bioname'], r['party_code']); continue
        key = (int(r['congress']), r['state_abbrev'], r['district_code'] if ch == 'H' else '')
        per[key].append((r, s))
    members = collections.defaultdict(list)  # congress -> list of (side, |score|, weight, name, icpsr)
    for key, lst in per.items():
        seats = 2.0 if ch == 'S' else 1.0
        tot = sum(max(1, int(r['nominate_number_of_votes'] or 1)) for r, s in lst)
        for r, s in lst:
            w = seats * max(1, int(r['nominate_number_of_votes'] or 1)) / tot
            members[key[0]].append((s, abs(float(r['nominate_dim1'])), w, r['bioname'], r['icpsr']))
    # calibrate thresholds on 112th
    thr = {}
    for s in 'LR':
        lst = sorted([m for m in members[112] if m[0] == s], key=lambda m: m[1])
        target = IMG112[ch][s]; tot = sum(m[2] for m in lst)
        scale = tot / sum(target)
        cum = 0; t1 = t2 = None; c1 = target[0]*scale; c2 = (target[0]+target[1])*scale
        prev = 0
        for m in lst:
            if t1 is None and cum + m[2] > c1: t1 = (prev + m[1]) / 2 if cum > 0 else m[1] - 1e-3
            if t2 is None and cum + m[2] > c2: t2 = (prev + m[1]) / 2
            cum += m[2]; prev = m[1]
        thr[s] = (t1, t2)
    res = {}
    for c in range(112, 120):
        res[c] = {}
        for s in 'LR':
            b = [0.0, 0.0, 0.0]
            for m in members[c]:
                if m[0] != s: continue
                i = 0 if m[1] < thr[s][0] else (1 if m[1] < thr[s][1] else 2)
                b[i] += m[2]
            res[c][s] = b
    # rank positions for tracked members (seats from center)
    track = {}
    for c in range(112, 120):
        for s in 'LR':
            lst = sorted([m for m in members[c] if m[0] == s], key=lambda m: m[1])
            cum = 0
            for m in lst:
                nm = m[3]
                if any(k in nm for k in ('PELOSI', 'BOEHNER', 'RYAN, Paul', 'DINGELL, John David')):
                    track.setdefault(nm, {})[c] = cum + m[2] / 2
                cum += m[2]
    out[ch] = {'thr': thr, 'bands': res, 'track': track}
    print(ch, 'thr', thr)
    for c in range(112, 120):
        print(' ', c, ['%.1f' % v for v in res[c]['L']], ['%.1f' % v for v in res[c]['R']], 'L=%.1f R=%.1f' % (sum(res[c]['L']), sum(res[c]['R'])))
    for k, v in track.items(): print('  ', k, {c: round(x, 1) for c, x in v.items()})
json.dump(out, open(f'{D}/bands.json', 'w'), indent=1)
