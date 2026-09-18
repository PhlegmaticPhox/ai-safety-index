"""WCAG AA contrast check over the locked palette.

Run after any colour change. "Low-contrast dark mode" is on the avoid-list, and
this is the thing that stops it happening by accident. Values must match
src/styles/global.css; if they drift, this checks a palette the site no longer
uses, which is worse than not checking at all.
"""

def lum(h):
    h = h.lstrip('#')
    c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

BG, BG_DEEP, BAND = '#0e1829', '#091120', '#13203a'
SURF, SURF2 = '#182946', '#1f3354'
INK, MUTED, MUTED2 = '#eaf1fb', '#b3c2dc', '#93a6c6'
ACCENT, ACCENT_INK = '#f2a950', '#f8cf96'
# Ink used on the accent as a button face. Not a palette token: it exists only
# as the one legible foreground for a solid amber fill.
ACCENT_ON = '#1b1200'
# Data hue. Carries governance wherever governance is plotted, so it has to be
# legible as text and as a fill, not only as a swatch.
GOV, GOV_INK = '#63b3ec', '#9bcdf3'

checks = [
    ('body text on bg',          INK, BG,          4.5),
    ('body text on surface',     INK, SURF,        4.5),
    ('body text on surface-2',   INK, SURF2,       4.5),
    ('muted on bg',              MUTED, BG,        4.5),
    ('muted on surface',         MUTED, SURF,      4.5),
    ('muted on surface-2',       MUTED, SURF2,     4.5),
    ('accent link on bg',        ACCENT, BG,       4.5),
    ('accent link on surface',   ACCENT, SURF,     4.5),
    ('accent link on surface-2', ACCENT, SURF2,    4.5),
    ('accent-ink on surface-2',  ACCENT_INK, SURF2, 4.5),
    ('gov hue on bg',            GOV, BG,          4.5),
    ('gov hue on surface',       GOV, SURF,        4.5),
    ('gov hue on surface-2',     GOV, SURF2,       4.5),
    ('gov-ink on surface-2',     GOV_INK, SURF2,   4.5),
    ('muted-2 on bg',            MUTED2, BG,       4.5),
    ('muted-2 on band',          MUTED2, BAND,     4.5),
    ('muted-2 on surface',       MUTED2, SURF,     4.5),
    ('muted-2 on surface-2',     MUTED2, SURF2,    4.5),
    ('muted-2 on bg-deep',       MUTED2, BG_DEEP,  4.5),
    ('body text on band',        INK, BAND,        4.5),
    ('muted on band',            MUTED, BAND,      4.5),
    ('accent link on band',      ACCENT, BAND,     4.5),
    ('gov hue on band',          GOV, BAND,        4.5),
    ('footer muted on bg-deep',  MUTED, BG_DEEP,   4.5),
    ('BUTTON: ink on accent',    ACCENT_ON, ACCENT, 4.5),
    ('BUTTON: bg-ink on gov',    BG, GOV,          4.5),
    ('large heading on bg',      INK, BG,          3.0),
]

# Field schemes. Each section of the site gets its own ground palette, generated
# into src/styles/fields.css by rotating the base hue and holding luminance
# constant. They are READ FROM THAT FILE rather than copied here: a copy is the
# one thing this checker must never contain, because a copy that drifts checks a
# palette the site no longer uses, which is worse than not checking at all.
import os
import re

_here = os.path.dirname(os.path.abspath(__file__))
_fields_css = os.path.join(_here, '..', 'src', 'styles', 'fields.css')
with open(_fields_css, encoding='utf-8') as _f:
    _css = _f.read()

# A scheme is spread over two rule blocks: the accent pair, which also carries
# [data-accent], and the ground block. Merge every block that names the field.
_merged = {}
for _sel, _body in re.findall(r'((?:\[data-[a-z]+="\w+"\],?\s*)+)\{(.*?)\}', _css, re.S):
    _names = set(re.findall(r'\[data-(?:field|accent)="(\w+)"\]', _sel))
    for _n in _names:
        _merged.setdefault(_n, {}).update(
            dict(re.findall(r'(--[a-z0-9-]+):\s*(#[0-9a-fA-F]{6})', _body))
        )
_schemes = sorted(_merged.items())
if not _schemes:
    raise SystemExit('check_contrast: no [data-field] schemes found in src/styles/fields.css')

# Body text sits on every ground; the field accent is an eyebrow, which is small
# uppercase text and so has to clear AA as text on the grounds it appears over.
_TEXT_ON = ('--bg', '--bg-deep', '--band', '--surface', '--surface-2')
_ACCENT_ON = ('--bg', '--band', '--surface')

for _name, _tok in _schemes:
    _accent = _tok.get('--field')
    missing = [t for t in _TEXT_ON if t not in _tok]
    if missing or not _accent:
        raise SystemExit(f'check_contrast: scheme {_name} is missing {missing or ["--field"]}')
    for _ground in _TEXT_ON:
        for _label, _ink in (('ink', INK), ('muted', MUTED), ('muted-2', MUTED2)):
            checks.append((f'{_name}: {_label} on {_ground[2:]}', _ink, _tok[_ground], 4.5))
    for _ground in _ACCENT_ON:
        checks.append((f'{_name}: accent on {_ground[2:]}', _accent, _tok[_ground], 4.5))

fails = 0
for label, fg, bg, need in checks:
    r = ratio(fg, bg)
    ok = r >= need
    fails += not ok
    print(f"  {'PASS' if ok else 'FAIL'}  {r:5.2f}:1  (need {need})  {label}")
print(f"\n{'ALL PASS' if not fails else f'{fails} FAILURES'}")
raise SystemExit(1 if fails else 0)
