def lum(h):
    h = h.lstrip('#')
    c = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

def ratio(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

BG, SURF, SURF2 = '#0f1115', '#161920', '#1d2129'
INK, MUTED, ACCENT, ACCENT_INK = '#e9ebef', '#9aa1ad', '#e9a23b', '#f3c485'

checks = [
    ('body text on bg',        INK, BG,       4.5),
    ('body text on surface',   INK, SURF,     4.5),
    ('body text on surface-2', INK, SURF2,    4.5),
    ('muted on bg',            MUTED, BG,     4.5),
    ('muted on surface',       MUTED, SURF,   4.5),
    ('muted on surface-2',     MUTED, SURF2,  4.5),
    ('accent link on bg',      ACCENT, BG,    4.5),
    ('accent link on surface', ACCENT, SURF,  4.5),
    ('accent-ink on surface2', ACCENT_INK, SURF2, 4.5),
    ('BUTTON: bg-ink on accent', BG, ACCENT,  4.5),
    ('large heading on bg',    INK, BG,       3.0),
]
fails = 0
for label, fg, bg, need in checks:
    r = ratio(fg, bg)
    ok = r >= need
    fails += not ok
    print(f"  {'PASS' if ok else 'FAIL'}  {r:5.2f}:1  (need {need})  {label}")
print(f"\n{'ALL PASS' if not fails else f'{fails} FAILURES'}")
