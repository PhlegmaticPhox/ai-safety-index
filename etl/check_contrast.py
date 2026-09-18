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

# Field hues. One per section of the site, set with data-field and used for the
# eyebrow, the rule above a section and the dot tint. The eyebrow is small
# uppercase text, so each one has to clear AA as text on every ground it can
# appear over, not merely be visible as a tint.
FIELDS = {
    'progress':   '#f2a950',
    'capability': '#a78bfa',
    'alignment':  '#4fc3a1',
    'adoption':   '#e891a8',
    'map':        '#63b3ec',
    'policy':     '#b5c65a',
    'news':       '#f0996b',
    'sources':    '#9fb0c9',
}
for name, hue in FIELDS.items():
    for ground, label in ((BG, 'bg'), (BAND, 'band'), (SURF, 'surface')):
        checks.append((f'field {name} on {label}', hue, ground, 4.5))
fails = 0
for label, fg, bg, need in checks:
    r = ratio(fg, bg)
    ok = r >= need
    fails += not ok
    print(f"  {'PASS' if ok else 'FAIL'}  {r:5.2f}:1  (need {need})  {label}")
print(f"\n{'ALL PASS' if not fails else f'{fails} FAILURES'}")
raise SystemExit(1 if fails else 0)
