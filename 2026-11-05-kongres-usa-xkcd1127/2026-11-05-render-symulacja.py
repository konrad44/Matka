import json, math, random, sys
import numpy as np
import cairo
from PIL import Image, ImageDraw, ImageFont

BASE = sys.argv[1]
SRC = f'{BASE}/dl/congress_large.png'
OUT = sys.argv[2]
FD = f'{BASE}/fonts'
bands = json.load(open(f'{BASE}/data/bands.json'))

orig = Image.open(SRC).convert('RGB')
A = np.array(orig)
W, H0 = orig.size

# ---------------- geometry ----------------
S = 18.13            # px per year
D = 319              # inserted height (incl. 2 simulated years)
CUT = 636            # header / chart cut (original coords)
CUT_RIGHT = 600      # cut for the legend panel (x >= 2440)
T_SEAM = 2011.27     # time at original top edge (row 641)
T_NOW = 2028.85      # end of simulated extension
T_TODAY = 2026.85    # 5 Nov 2026
# simulated 120th Congress (2027-2029) after the projected Democratic wins of Nov 2026
SIM = {'S': {'L': [15.9, 19.1, 19.0], 'R': [1.0, 5.8, 39.2]},
       'H': {'L': [133.6, 79.4, 42.0], 'R': [0.3, 25.0, 154.7]}}
for _ch in 'SH':
    bands[_ch]['bands']['120'] = SIM[_ch]
SEAM_Y = 641 + D     # final row of original stream top
HF = H0 + D

def ty(t):           # final y for time t
    return 645 + D - (t - 2011) * S

def tc(c):           # start of congress c
    return 1789 + 2 * (c - 1)

TR = 1.3             # transition length (years) before each congress start

CH = {
    'S': dict(cx=621.5, k=3.5, xl=620.6, xr=622.6,
              colL=[(68,172,232),(11,29,125),(14,26,64)], colR=[(220,0,27),(115,5,15),(41,0,3)],
              img={'L':[63,88,34], 'R':[20,67,78]}, yellow0=617.5,
              margin=(8, 30), x_min=385, x_max=870),
    'H': dict(cx=1933.0, k=0.97, xl=1932.6, xr=1934.4,
              colL=[(68,172,232),(29,44,137),(7,19,59)], colR=[(220,0,27),(115,5,15),(40,0,3)],
              img={'L':[80,58,49], 'R':[0,71,162]}, yellow0=1929.5,
              margin=(10, 34), x_min=1620, x_max=2230),
}

def smooth(u):
    u = min(1, max(0, u)); return u * u * (3 - 2 * u)

def series(ch, side, i):
    """list of (t, value_px) for band i (0=center) of side"""
    c = CH[ch]
    pts = [(T_SEAM, float(c['img'][side][i]))]
    for cg in range(113, 121):
        pts.append((tc(cg), bands[ch]['bands'][str(cg)][side][i] * c['k']))
    return pts

def tstart(t1):
    return T_TODAY + 0.02 if abs(t1 - tc(120)) < 1e-6 else t1 - TR

def val(pts, t):
    v = pts[0][1]
    for (t1, v1) in pts[1:]:
        if t >= t1: v = v1; continue
        a = tstart(t1)
        if t > a:
            return v + (v1 - v) * smooth((t - a) / (t1 - a))
        return v
    return v

def cum(ch, side, t):
    w = [val(series(ch, side, i), t) for i in range(3)]
    return [w[0], w[0] + w[1], w[0] + w[1] + w[2]]

def outer_x(ch, side, t):
    c = CH[ch]; cc = cum(ch, side, t)
    return c['xl'] - cc[2] if side == 'L' else c['xr'] + cc[2]

ts = np.arange(T_SEAM - 0.25, T_NOW + 1e-6, 0.02).tolist()
if ts[-1] < T_NOW: ts.append(T_NOW)
ts_top = T_NOW

# ---------------- cairo layer ----------------
surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, HF)
cr = cairo.Context(surf)

def rgb(c, a=1.0):
    cr.set_source_rgba(c[0] / 255, c[1] / 255, c[2] / 255, a)

def yclip(t):  # final y, clamped below to seam
    return min(ty(t), SEAM_Y + 0.5)

random.seed(1127)

def draw_chamber(ch):
    c = CH[ch]
    cr.save()
    cr.rectangle(0, 0, W, SEAM_Y + 1)   # never draw over the original rows
    cr.clip()
    for side in 'LR':
        cols = c['colL'] if side == 'L' else c['colR']
        sg = -1 if side == 'L' else 1
        x0 = c['xl'] if side == 'L' else c['xr']
        # nested band polygons, outermost first
        for i in (2, 1, 0):
            cr.new_path()
            cr.move_to(x0, ty(ts[0]) + 2)
            for t in ts:
                cr.line_to(x0 + sg * cum(ch, side, t)[i], ty(t) + (2 if t == ts[0] else 0))
            cr.line_to(x0, ty(ts[-1]))
            cr.close_path()
            rgb(cols[i]); cr.fill()
        # branches
        for i in (2, 1, 0):
            pts = series(ch, side, i)
            for j in range(1, len(pts)):
                t1 = pts[j][0]
                dv = pts[j][1] - pts[j - 1][1]
                if abs(dv) < 0.8 * c['k'] or t1 > T_TODAY: continue
                n = max(1, int(math.ceil(abs(dv) / 22.0)))
                wpx = abs(dv) / n
                for p in range(n):
                    rgb(cols[i])
                    cr.set_line_width(wpx)
                    cr.set_line_cap(cairo.LINE_CAP_BUTT)
                    mg = random.uniform(*c['margin']) + p * 10
                    if dv > 0:   # join: free end outside, earlier, merging upward into band
                        tj = t1 - 0.05
                        inner = cum(ch, side, tj)[i] - wpx * (p + 0.5)
                        xe = x0 + sg * inner
                        t0 = max(t1 - 2.5 - 0.35 * p - random.uniform(0, 0.4), T_SEAM + 0.12)
                        if t1 > T_TODAY: t0 = T_TODAY + 0.05 + 0.1 * p
                        xs = outer_x(ch, side, t0) + sg * mg
                        xs = min(max(xs, c['x_min']), c['x_max'])
                        ys, ye = ty(t0), ty(tj)
                        cr.move_to(xs, ys)
                        cr.curve_to(xs + (xe - xs) * 0.35, ys - (ys - ye) * 0.35,
                                    xe, ye + (ys - ye) * 0.6, xe, ye)
                        cr.line_to(xe, ye - 6)
                        cr.stroke()
                    else:        # split: leaves band at the start of the transition, exits upward
                        tsd = tstart(t1) + 0.05
                        inner = cum(ch, side, tsd)[i] - wpx * (p + 0.5)
                        xs = x0 + sg * inner
                        t2 = min(t1 + 1.1 + 0.35 * p + random.uniform(0, 0.4), T_NOW - 0.05)
                        if t2 - tsd < (0.6 if t1 < T_TODAY else 1.2): continue
                        xe = outer_x(ch, side, t2) + sg * mg
                        xe = min(max(xe, c['x_min']), c['x_max'])
                        ys, ye = ty(tsd), ty(t2)
                        cr.move_to(xs, ys + 6)
                        cr.line_to(xs, ys)
                        cr.curve_to(xs, ys - (ys - ye) * 0.6,
                                    xe - (xe - xs) * 0.35, ye + (ys - ye) * 0.35, xe, ye)
                        cr.stroke()
    cr.restore()

def stream_extent(ch, t):
    return outer_x(ch, 'L', t), outer_x(ch, 'R', t)

def grid_lines(ch):
    c = CH[ch]
    lab_font_y = []
    for cg in range(113, 121):
        t = tc(cg); y = round(ty(t)) + 0.5
        xa, xb = stream_extent(ch, t + 0.01)
        cr.save()
        if cg in (115, 117, 119):             # new presidency: solid
            cr.set_source_rgba(1, 1, 1, 0.42); cr.set_line_width(2)
            cr.move_to(xa, y); cr.line_to(xb, y); cr.stroke()
        elif cg % 2 == 0:                      # even congress: dashed + label
            cr.set_source_rgba(1, 1, 1, 0.66); cr.set_line_width(1)
            cr.set_dash([7, 3])
            gap_a, gap_b = c['cx'] - 26, c['cx'] + 44
            cr.move_to(xa, y); cr.line_to(gap_a, y); cr.stroke()
            cr.move_to(gap_b, y); cr.line_to(xb, y); cr.stroke()
            lab_font_y.append((cg, y))
        else:                                  # odd congress: dotted
            cr.set_source_rgba(1, 1, 1, 0.55); cr.set_line_width(1)
            cr.set_dash([1.5, 2.5])
            cr.move_to(xa, y); cr.line_to(xb, y); cr.stroke()
        cr.restore()
    return lab_font_y

def yellow(ch):
    c = CH[ch]
    cr.save()
    cr.rectangle(0, 0, W, SEAM_Y + 1); cr.clip()
    cr.set_source_rgba(220 / 255, 220 / 255, 30 / 255, 0.6)
    cr.set_line_width(1.6); cr.set_dash([6, 3, 1.5, 3])
    first = True
    for t in ts:
        L = sum(val(series(ch, 'L', i), t) for i in range(3))
        R = sum(val(series(ch, 'R', i), t) for i in range(3))
        x = c['cx'] + (R - L) / 2
        u = smooth((t - T_SEAM) / 1.2)
        x = c['yellow0'] + (x - c['yellow0']) * u
        y = ty(t)
        if first: cr.move_to(x, y); first = False
        else: cr.line_to(x, y)
    cr.stroke()
    cr.restore()

def centerline(ch):
    c = CH[ch]
    cr.save(); cr.set_source_rgb(1, 1, 1)
    xa, xb = (621, 623) if ch == 'S' else (1932.6, 1934.6)
    cr.rectangle(xa - 0.4, ty(T_NOW), xb - xa, SEAM_Y + 0.6 - ty(T_NOW)); cr.fill()
    cr.restore()

# tracked member lines (thin solid)
TRACK = {
    'H': [
        ('PELOSI, Nancy', 'L', 1798, 2027.0),
        ('DINGELL, John David, Jr.', 'L', 1815, 2015.0),
        ('BOEHNER, John Andrew', 'R', 2090.5, 2015.8),
        ('RYAN, Paul D.', 'R', 2119.5, 2019.0),
    ]
}

def member_lines(ch):
    c = CH[ch]
    for name, side, ximg, tend in TRACK.get(ch, []):
        tr = bands[ch]['track'][name]
        sg = -1 if side == 'L' else 1
        x0 = c['xl'] if side == 'L' else c['xr']
        img_seats = abs(ximg - x0)
        ratio = img_seats / (tr['112'] * c['k'])
        pts = [(T_SEAM, img_seats)]
        for cg in range(113, 120):
            if str(cg) in tr and tc(cg) < tend + 0.01:
                pts.append((tc(cg), tr[str(cg)] * c['k'] * ratio))
        cr.save()
        cr.rectangle(0, 0, W, SEAM_Y + 0.6); cr.clip()
        cr.set_source_rgba(1, 1, 1, 0.42); cr.set_line_width(1.3)
        first = True
        tt = [t for t in ts if t <= tend] + [tend]
        for t in tt:
            x = x0 + sg * val(pts, t); y = ty(t)
            if first: cr.move_to(x, y + 1); first = False
            else: cr.line_to(x, y)
        cr.stroke()
        if tend < T_NOW - 0.01:
            x = x0 + sg * val(pts, tend)
            cr.arc(x, ty(tend), 3.2, 0, 2 * math.pi); cr.fill()
        cr.restore()

# ---------------- presidency column ----------------
PUR = (71, 58, 88)
IN_A, IN_B = 1119, 1396       # interior [a, b)
MID = 1263
COL_TOP = 605
COL_REDRAW_BOTTOM = 680 + D   # original rows < 680 of the interior are redrawn

def column():
    # interior background
    cr.save()
    cr.rectangle(IN_A, COL_TOP, IN_B - IN_A, COL_REDRAW_BOTTOM - COL_TOP); cr.clip()
    cr.set_source_rgb(1, 1, 1); cr.paint()
    def bar(x0, x1, t0, t1, col):
        rgb(col); y0, y1 = ty(t1), ty(t0)
        cr.rectangle(x0, y0, x1 - x0, y1 - y0); cr.fill()
    bar(IN_A, MID, 2003.2, 2011.96, (175, 175, 175))         # Iraq War (ends Dec 2011)
    bar(MID, IN_B, 2001.8, 2021.66, (150, 150, 150))         # Afghanistan War (ends Aug 2021)
    bar(IN_A, IN_B, 2007.75, 2010.12, (228, 228, 228))       # Financial crisis (existing)
    bar(IN_A, IN_B, 2020.2, 2023.35, (228, 228, 228))        # COVID-19
    # separators at inaugurations (copy of the original 2009 line rows 680..683)
    for yr in (2017.05, 2021.05, 2025.05):
        yc = ty(yr - 0.06)
        for k, g in enumerate((127, 62, 62, 95)):
            pass
        cr.set_source_rgb(62 / 255, 59 / 255, 59 / 255)
        cr.rectangle(IN_A, yc - 1.5, IN_B - IN_A, 3); cr.fill()
    cr.restore()
    # purple year strips
    rgb(PUR)
    cr.rectangle(1065, COL_TOP, 1118 - 1065 + 1, CUT + D - COL_TOP); cr.fill()
    cr.rectangle(1397, COL_TOP, 1450 - 1397 + 1, CUT + D - COL_TOP); cr.fill()
    rgb((112, 102, 125)); cr.rectangle(1396, COL_TOP, 1, CUT + D - COL_TOP); cr.fill()
    rgb((125, 115, 135)); cr.rectangle(1065, COL_TOP, 54, 1); cr.rectangle(1397, COL_TOP, 54, 1); cr.fill()

def triangle(x, y, side, col):
    rgb(col)
    if side == 'L':
        cr.move_to(x, y); cr.line_to(x + 11, y - 6.5); cr.line_to(x + 11, y + 6.5)
    else:
        cr.move_to(x + 11, y); cr.line_to(x, y - 6.5); cr.line_to(x, y + 6.5)
    cr.close_path(); cr.fill()

# ---------------- draw vector parts ----------------
for ch in ('S', 'H'):
    draw_chamber(ch)
labs = {}
for ch in ('S', 'H'):
    member_lines(ch)
    labs[ch] = grid_lines(ch)
    centerline(ch)
    yellow(ch)
column()

# stream top: flat cut like the original
surf.flush()
layer = Image.frombuffer('RGBa', (W, HF), bytes(surf.get_data()), 'raw', 'BGRa', 0, 1).convert('RGBA')

# ---------------- assemble ----------------
base = Image.new('RGB', (W, HF), (255, 255, 255))
B = np.array(base)
# header (left part, cut at CUT; right legend panel cut at CUT_RIGHT)
B[:CUT, :2440] = A[:CUT, :2440]
B[:CUT_RIGHT, 2440:] = A[:CUT_RIGHT, 2440:]
B[CUT + D:, :2440] = A[CUT:, :2440]
B[CUT_RIGHT + D:, 2440:] = A[CUT_RIGHT:, 2440:]

# House spike that poked above the original stream top: restore axis ticks by mirroring
for y in range(614, CUT):
    for x in range(1846, 1890):
        B[y, x] = A[y, int(2 * 1933 - x)]
# clear the old column top in the header (will be redrawn)
B[COL_TOP:CUT, 1060:1456] = 255

# extend frame bands / dashed verticals through the inserted rows
for x0, x1 in [(118, 158), (2382, 2424)]:
    for y in range(CUT, CUT + D):
        B[y, x0:x1] = A[650 + ((y - CUT) % 70), x0:x1]

# remove the old bloc labels that sat at the old top (they are re-drawn at the new top)
PAL = {'S': [(14,26,64),(11,29,125),(68,172,232),(220,0,27),(115,5,15),(41,0,3),(255,255,255)],
       'H': [(7,19,59),(29,44,137),(68,172,232),(220,0,27),(115,5,15),(40,0,3),(192,0,9),(255,255,255)]}
LABEL_BOXES = {
    'S': [(489,657,515,670),(565,646,609,676),(423,683,446,713),(661,649,690,664),(736,648,768,679),(622,683,667,713)],
    'H': [(1786,682,1815,698),(1852,666,1894,698),(1704,697,1733,728),(1940,655,1971,670),(2019,647,2051,679),(1934,779,1977,813)],
}
SKIP_ROWS = {645, 680, 681, 682, 718} | set(range(752, 757))
for ch, boxes in LABEL_BOXES.items():
    pal = np.array(PAL[ch])
    for (x0, y0, x1, y1) in boxes:
        reg = A[y0 - 6:y1 + 7, x0 - 6:x1 + 7].astype(int)
        d = np.linalg.norm(reg[:, :, None, :] - pal[None, None], axis=3)
        near = d.argmin(2); dmin = d.min(2)
        clean = dmin < 6
        for yy in range(y0, y1 + 1):
            if yy in SKIP_ROWS: continue
            for xx in range(x0, x1 + 1):
                ry, rx = yy - y0 + 6, xx - x0 + 6
                if clean[ry, rx]: continue
                if ch == 'S' and abs(xx - 448) < 5 and abs(yy - 705) < 5: continue   # keep member dot
                win_c = clean[ry - 5:ry + 6, rx - 5:rx + 6]
                win_n = near[ry - 5:ry + 6, rx - 5:rx + 6][win_c]
                if len(win_n) == 0: continue
                # majority palette colour in the window
                vals, cnts = np.unique(win_n, return_counts=True)
                B[yy + D, xx] = pal[vals[cnts.argmax()]]
# small dark-blue wedge at the top of the House center-left bloc (would look cut off)
for y in range(641, 700):
    if y in SKIP_ROWS: continue
    for x in range(1878, 1904):
        p = A[y, x].astype(int)
        lb, cl = np.array((29, 44, 137)), np.array((68, 172, 232))
        v = cl - lb; u = np.dot(p - lb, v) / np.dot(v, v)
        if np.linalg.norm(p - (lb + u * v)) < 14 and u < 0.97:
            B[y + D, x] = cl

for x in range(1878, 1904):
    p = B[645 + D, x].astype(int)
    if np.linalg.norm(p - np.array((168, 179, 214))) < 30: B[645 + D, x] = (193, 230, 248)
    elif np.linalg.norm(p - np.array((29, 44, 137))) < 40: B[645 + D, x] = (68, 172, 232)
base = Image.fromarray(B)
base.paste(layer, (0, 0), layer)

# ---------------- simulated part: fade + TODAY line ----------------
yT = int(round(ty(T_TODAY)))
Bf = np.array(base).astype(float)
for (xa, xb, y0) in [(300, 1000, 630), (IN_A, IN_B, 605), (1500, 2370, 630)]:
    reg = Bf[y0:yT, xa:xb]
    nonwhite = reg.sum(2) < 760
    reg[nonwhite] = reg[nonwhite] * 0.65 + 255 * 0.35
    Bf[y0:yT, xa:xb] = reg
base = Image.fromarray(Bf.astype(np.uint8))
dr0 = ImageDraw.Draw(base)
ftd = ImageFont.truetype(f'{FD}/Oswald.ttf', 12); ftd.set_variation_by_name('Regular')
for (xa, xb, lx) in [(160, 1064, 165), (1452, 2383, 1470)]:
    for x in range(xa, xb, 8):
        dr0.line([(x, yT), (min(x + 5, xb), yT)], fill=(30, 30, 30), width=2)
    dr0.rectangle([lx - 3, yT - 9, lx + 140, yT + 9], fill=(255, 255, 255))
    dr0.text((lx, yT), 'TODAY  (NOV. 5, 2026)', font=ftd, fill=(30, 30, 30), anchor='lm')
    dr0.text((lx, yT - 20), 'SIMULATED: 120TH CONGRESS', font=ftd, fill=(130, 130, 130), anchor='lm')
for x in range(IN_A, IN_B, 8):
    dr0.line([(x, yT), (min(x + 5, IN_B), yT)], fill=(30, 30, 30), width=2)

# ---------------- text ----------------
dr = ImageDraw.Draw(base)
def F(name, size, var=None):
    f = ImageFont.truetype(f'{FD}/{name}', size)
    if var: f.set_variation_by_name(var)
    return f
TXT = (35, 31, 32)

# bloc labels at the new top (same relative placement as the original)
def bloc_label(text, x, y, fill, size=13, anchor='mm'):
    f = F('Lato-Light.ttf', size)
    lines = text.split('\n')
    for k, ln in enumerate(lines):
        dr.text((x, y + k * 13), ln, font=f, fill=fill, anchor=anchor)
def mix(c, a=0.30):
    c = tuple(c[i] * 0.65 + 255 * 0.35 for i in range(3))
    return tuple(int(c[i] + (255 - c[i]) * a) for i in range(3))
for ch in ('S', 'H'):
    c = CH[ch]
    t = T_NOW
    for side in 'LR':
        cc = cum(ch, side, t); x0 = c['xl'] if side == 'L' else c['xr']; sg = -1 if side == 'L' else 1
        cols = c['colL'] if side == 'L' else c['colR']
        names = ['Center\nLeft', 'Left', 'Far\nLeft'] if side == 'L' else ['Center\nRight', 'Right', 'Far\nRight']
        for i in range(3):
            lo = 0 if i == 0 else cc[i - 1]
            w = cc[i] - lo
            yy = 649 if '\n' in names[i] else 655
            if w >= 26:
                xm = x0 + sg * (lo + w / 2)
                bloc_label(names[i], xm, yy, mix(cols[i]))
            else:   # too thin: place it next to the centre line, spilling into the next bloc (as the original does)
                xm = x0 + sg * 4
                nxt = cols[min(i + 1, 2)]
                f = F('Lato-Light.ttf', 13)
                for k, ln in enumerate(names[i].split('\n')):
                    dr.text((xm, yy + 39 + k * 13), ln, font=f, fill=mix(nxt), anchor='lm' if side == 'R' else 'rm')

# congress labels on dashed lines
fc = F('Oswald.ttf', 11, 'Regular')
fcs = F('Oswald.ttf', 7, 'Regular')
for ch in ('S', 'H'):
    c = CH[ch]
    for cg, y in labs[ch]:
        xe = c['cx'] - 6
        dr.text((xe, y), f'{cg}', font=fc, fill=(205, 196, 40), anchor='rm')
        dr.text((xe + 0.5, y - 5), 'th', font=fcs, fill=(205, 196, 40), anchor='lm')
        dr.text((c['cx'] + 3, y), 'CONGRESS', font=fc, fill=(232, 150, 0), anchor='lm')

# year labels
fbig = F('Oswald.ttf', 23, 'Regular')
fsm = F('Oswald.ttf', 12, 'Light')
for Y in range(2012, 2029, 2):
    y = 622 + D - (Y - 2012) * S
    f = fbig if Y % 4 == 0 else fsm
    for xc in (1091.5, 1423.5):
        dr.text((xc, y), str(Y), font=f, fill=(255, 255, 255), anchor='mm')

# president names
ffirst = F('Lato-Regular.ttf', 19)
flast = F('Oswald.ttf', 30, 'Regular')
def president(first, last, t_mid, party, inline=False):
    yc = ty(t_mid)
    col = (29, 44, 137) if party == 'D' else (115, 5, 15)
    cx = (IN_A + IN_B) / 2
    if inline:
        wf = dr.textlength(first + ' ', font=ffirst); wl = dr.textlength(last, font=flast)
        x = cx - (wf + wl + 14) / 2
        dr.text((x, yc + 3), first, font=ffirst, fill=TXT, anchor='ls')
        dr.text((x + wf, yc + 3), last, font=flast, fill=TXT, anchor='ls')
        return x + wf + wl, yc - 7
    dr.text((cx, yc - 10), first, font=ffirst, fill=TXT, anchor='ms')
    dr.text((cx, yc + 18), last, font=flast, fill=TXT, anchor='ms')
    wl = dr.textlength(last, font=flast)
    return cx, wl, yc + 7

tri = []
cx_, wl, yy = president('Barack', 'OBAMA', 2013.4, 'D'); tri.append((cx_ - wl / 2 - 14, yy, 'L', (29, 44, 137)))
cx_, wl, yy = president('Donald J.', 'TRUMP', 2018.75, 'R'); tri.append((cx_ + wl / 2 + 3, yy, 'R', (115, 5, 15)))
cx_, wl, yy = president('Joe', 'BIDEN', 2023.05, 'D'); tri.append((cx_ - wl / 2 - 14, yy, 'L', (29, 44, 137)))
xe_, yy = president('Donald J.', 'TRUMP', 2025.75, 'R', inline=True); tri.append((xe_ + 3, yy, 'R', (115, 5, 15)))

fev = F('Lato-Light.ttf', 11)
dr.text((IN_B - 5, ty(2020.2) - 4), 'COVID-19 Pandemic', font=fev, fill=(95, 95, 95), anchor='rs')

# annotations
fa = F('Lato-Regular.ttf', 16)
def para(x, y, text, align='left', width=None):
    for k, ln in enumerate(text.split('\n')):
        if align == 'left':
            dr.text((x, y + k * 20), ln, font=fa, fill=TXT, anchor='ls')
        else:
            dr.text((x, y + k * 20), ln, font=fa, fill=TXT, anchor='rs')

para(165, ty(2020.6), "Republicans took the Senate\nin 2014 and held it for six\nyears. In 2021 Democrats ran\na 50–50 chamber, relying on\nthe Vice President's\ntie-breaking vote.")
para(1040, ty(2024.2), "Republicans retook the\nSenate in 2024, 53–47.\nThe far right bloc\nkept growing.", align='right')
para(1470, ty(2019.9), "Democrats won back the\nHouse in 2018, gaining\n41 seats. Most of the new\nmembers joined the\ncenter-left bloc.")
para(2375, ty(2024.3), "Republicans regained\nthe House in 2022 with\na slim majority and kept\nit in 2024.", align='right')

# update box in the empty space above the legend
bx0, by0, bx1, by1 = 2462, 612, 2838, 618 + D - 14
dash = 3
for x in range(bx0, bx1, dash * 2):
    dr.line([(x, by0), (min(x + dash, bx1), by0)], fill=(90, 90, 90)); dr.line([(x, by1), (min(x + dash, bx1), by1)], fill=(90, 90, 90))
for y in range(by0, by1, dash * 2):
    dr.line([(bx0, y), (bx0, min(y + dash, by1))], fill=(90, 90, 90)); dr.line([(bx1, y), (bx1, min(y + dash, by1))], fill=(90, 90, 90))
dr.text(((bx0 + bx1) / 2, by0 + 40), 'UPDATE 2012–2028', font=F('Lato-Light.ttf', 34), fill=TXT, anchor='mm')
fu = F('Lato-Regular.ttf', 12)
upd = ("Extended through the 119th Congress (2025–2027)\n"
       "using Voteview DW-NOMINATE scores. Bloc\n"
       "boundaries were calibrated so the 112th Congress\n"
       "matches the original chart.\n"
       "\n"
       "Nov. 3, 2026: Democrats are projected to win both\n"
       "chambers (count still in progress). The 120th\n"
       "Congress takes office in January 2027.\n"
       "\n"
       "Above the TODAY line (faded): a simulation of the\n"
       "120th Congress (2027–2029), assuming Senate 54–46\n"
       "and House 255–180. New Democrats are placed\n"
       "mostly in the center-left bloc (as in 2018),\n"
       "Republican losses mostly from the center. Not data.")
for k, ln in enumerate(upd.split('\n')):
    dr.text((bx0 + 16, by0 + 74 + k * 16), ln, font=fu, fill=(70, 70, 70), anchor='ls')

base_arr = base
# triangles via a tiny second cairo pass
s2 = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, HF); cr = cairo.Context(s2)
for (x, y, side, col) in tri:
    triangle(x, y, side, col)
s2.flush()
l2 = Image.frombuffer('RGBa', (W, HF), bytes(s2.get_data()), 'raw', 'BGRa', 0, 1).convert('RGBA')
base.paste(l2, (0, 0), l2)
base.save(OUT)
print('saved', OUT, base.size)
