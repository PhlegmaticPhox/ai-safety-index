"""Generate a per-section ground palette from the base blue one.

Each section of the site gets its own scheme: the base palette with its hue
rotated to that section's own, keeping every token's saturation and lightness,
and then rescaled in linear light to the base token's exact relative luminance.

Luminance is the only term in the WCAG contrast formula, so holding it fixed
means every scheme keeps precisely the contrast the base palette had against
--ink, --muted and --muted-2. The hue moves; the legibility cannot.

The ground hues are chosen, not derived from the field accent. Deriving them
does not work: an accent scaled down to a dark ground's luminance is nearly
grey, so a far-off hue like lime barely moves the ground while a near one
overshoots. Choosing them keeps every ground inside one cool institutional
family while still making each page visibly its own.
"""
import colorsys, io, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

BASE = {
    '--bg':        '#0e1829',
    '--bg-deep':   '#091120',
    '--band':      '#13203a',
    '--surface':   '#182946',
    '--surface-2': '#1f3354',
    '--line':      '#2c426a',
    '--line-soft': '#223759',
}

# field: (accent hue, ground hue in degrees, saturation scale, note)
FIELDS = {
    'progress':   ('#f2a950', 217, 1.00, 'Outputs. The base navy, because benchmarks are what the site leads on.'),
    'capability': ('#83a9c7', 206, 0.42, 'Inputs. A restrained steel blue for compute and silicon.'),
    'environment': ('#a9c47c', 148, 0.34, 'Energy. A moss ground for power, emissions and where they are counted.'),
    'alignment':  ('#4fc3a1', 197, 0.80, 'Safety. A colder, greener blue.'),
    'usage':      ('#aba6ea', 236, 0.55, 'Volume. An indigo ground for how much the models are used and for what.'),
    'adoption':   ('#8eb59c', 165, 0.38, 'People. A quiet green-teal, distinct from the site\'s technical pages.'),
    'map':        ('#63b3ec', 206, 0.90, 'Governance, and the one page where ground and data hue agree.'),
    'policy':     ('#b5c65a', 183, 0.80, 'Law. The ground goes to a deep teal.'),
    'news':       ('#8fbac4', 195, 0.34, 'The wire. Cool blue-grey grounds with a soft cyan field accent.'),
    'sources':    ('#9fb0c9', 217, 0.50, 'The registry. The base hue at half saturation: deliberately the flattest ground on the site, because this page is about the others.'),
}


def to_lin(h):
    h = h.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return out


def to_hex(lin):
    s = ''
    for c in lin:
        c = max(0.0, min(1.0, c))
        v = 12.92 * c if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
        s += '%02x' % round(max(0.0, min(1.0, v)) * 255)
    return '#' + s


def lum(lin):
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a, b):
    la, lb = lum(to_lin(a)), lum(to_lin(b))
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def recolour(base_hex, hue_deg, sat_scale):
    """Set hue and scale saturation, then restore the base's exact luminance."""
    h = base_hex.lstrip('#')
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    _, l, s = colorsys.rgb_to_hls(r, g, b)
    nr, ng, nb = colorsys.hls_to_rgb(hue_deg / 360.0, l, min(1.0, s * sat_scale))
    lin = to_lin('#%02x%02x%02x' % (round(nr * 255), round(ng * 255), round(nb * 255)))
    target, have = lum(to_lin(base_hex)), lum(lin)
    if have > 0:
        scale = target / have
        # Only rescale when it cannot clip; hue rotation at constant L moves
        # luminance by a few percent at most, so this holds in practice.
        if max(c * scale for c in lin) <= 1.0:
            lin = [c * scale for c in lin]
    return to_hex(lin)


INKS = (('--ink', '#eaf1fb'), ('--muted', '#b3c2dc'), ('--muted-2', '#93a6c6'))

blocks, report = [], []
for name, (accent, ghue, sat, why) in FIELDS.items():
    rgb = ' '.join(str(int(accent.lstrip('#')[i:i + 2], 16)) for i in (0, 2, 4))
    # Two selectors, because a page and a section need different amounts of this.
    # data-field is the whole scheme, ground included, and goes on a sub-page's
    # <body>. data-accent is the field marker alone, and goes on a section of a
    # page that spans every field: the homepage keeps one ground throughout, and
    # only its eyebrows and rules change from section to section.
    lines = [
        '/* %s */' % why,
        '[data-field="%s"],' % name,
        '[data-accent="%s"] {' % name,
        '  --field: %s;' % accent,
        '  --field-line: rgb(%s / 0.34);' % rgb,
        '  --field-dot: rgb(%s / 0.13);' % rgb,
        '}',
        '',
        '[data-field="%s"] {' % name,
    ]
    worst, worst_pair = 99.0, ''
    for tok, base_hex in BASE.items():
        new = recolour(base_hex, ghue, sat)
        lines.append('  %s: %s;' % (tok, new))
        if not tok.startswith('--line'):
            for ink_name, ink in INKS:
                r = ratio(ink, new)
                if r < worst:
                    worst, worst_pair = r, '%s on %s' % (ink_name, tok)
    # The accent has to clear AA as text on this scheme's own grounds too.
    for tok in ('--bg', '--band', '--surface'):
        r = ratio(accent, recolour(BASE[tok], ghue, sat))
        if r < worst:
            worst, worst_pair = r, 'accent on %s' % tok
    lines.append('}')
    blocks.append('\n'.join(lines))
    report.append((name, ghue, worst, worst_pair))

path = os.path.join(ROOT, 'src/styles/fields.css')
with io.open(path, 'w', encoding='utf-8') as f:
    f.write(__doc__.replace('"""', '').strip().replace('\n', '\n   '))
    f.write('\n\n   GENERATED by scripts/gen-field-palettes.py. Do not hand-edit.\n')
    f.write('   Verified by etl/check_contrast.py. */\n\n')
    f.write('\n\n'.join(blocks) + '\n')

# Put the docstring inside a comment properly.
txt = io.open(path, encoding='utf-8').read()
io.open(path, 'w', encoding='utf-8').write('/* ' + txt)

print('%-12s %-6s %-8s %s' % ('field', 'hue', 'worst', 'limiting pair'))
ok = True
for name, ghue, worst, pair in report:
    ok &= worst >= 4.5
    print('  %-12s %-6s %.2f:1  %-22s %s' % (name, ghue, worst, pair, 'OK' if worst >= 4.5 else 'FAIL'))
print('\nwritten: src/styles/fields.css', '| ALL PASS' if ok else '| FAILURES')
