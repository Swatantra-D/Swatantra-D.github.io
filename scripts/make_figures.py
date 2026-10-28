"""Generate the code-drawn research illustrations in _includes/figures/.

Every figure is an *illustrative schematic*, not real data. They share one
400x250 canvas, one stroke vocabulary and CSS-variable colours (see the
"Figures" section of assets/css/main.css), so they follow the light/dark theme.

Usage:  python scripts/make_figures.py
"""
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_includes" / "figures"
W, H = 400, 250


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def svg(fid, title, body, defs=""):
    d = f"<defs>{defs}</defs>" if defs else ""
    return (f'<svg class="fig fig--{fid}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-labelledby="fig-{fid}-t" xmlns="http://www.w3.org/2000/svg">'
            f'<title id="fig-{fid}-t">Illustrative schematic: {title}</title>{d}{body}</svg>\n')


def label(x, y, text, cls="fx-label", anchor="start"):
    return f'<text x="{f(x)}" y="{f(y)}" class="{cls}" text-anchor="{anchor}">{text}</text>'


def dot_grid(fid, x0=10, y0=10, x1=390, y1=240, step=20):
    """(defs, body) for a faint dot grid drawn with one SVG pattern."""
    pid = f"fig-{fid}-dots"
    defs = (f'<pattern id="{pid}" width="{step}" height="{step}" patternUnits="userSpaceOnUse">'
            f'<circle cx="{step / 2}" cy="{step / 2}" r="0.9" class="fx-dot"/></pattern>')
    return defs, f'<rect x="{x0}" y="{y0}" width="{x1 - x0}" height="{y1 - y0}" fill="url(#{pid})"/>'


def arrow(x1, y1, x2, y2, cls="fx-arrow"):
    a = math.atan2(y2 - y1, x2 - x1)
    h1 = (x2 - 7 * math.cos(a - 0.45), y2 - 7 * math.sin(a - 0.45))
    h2 = (x2 - 7 * math.cos(a + 0.45), y2 - 7 * math.sin(a + 0.45))
    return (f'<path d="M{f(x1)} {f(y1)} L{f(x2)} {f(y2)} M{f(h1[0])} {f(h1[1])} '
            f'L{f(x2)} {f(y2)} L{f(h2[0])} {f(h2[1])}" class="{cls}"/>')


def catmull_rom_closed(pts):
    n = len(pts)
    d = f"M{f(pts[0][0])} {f(pts[0][1])}"
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{f(c1[0])} {f(c1[1])} {f(c2[0])} {f(c2[1])} {f(p2[0])} {f(p2[1])}"
    return d + " Z"


# 1 ─ State-space trajectory (brain-state transitions) ─────────────────────────
def state_space():
    rng = random.Random(4)
    basins = [(96, 82, "S1"), (300, 70, "S2"), (314, 180, "S3"), (110, 182, "S4")]
    defs, grid = dot_grid("state-space")
    body = [grid]
    for cx, cy, name in basins:
        for rx, ry, o in ((56, 38, 0.08), (39, 27, 0.13), (22, 15, 0.22)):
            body.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" class="fx-basin" style="--o:{o}"/>')
        body.append(label(cx - 44, cy - 30, name, "fx-label fx-strong"))
    pts = []
    for cx, cy, _ in basins:
        a0 = rng.uniform(0, 2 * math.pi)
        for k in range(5):
            a = a0 + k * 2 * math.pi / 4.6
            r = rng.uniform(9, 19)
            pts.append((cx + 1.45 * r * math.cos(a), cy + r * math.sin(a)))
    d = catmull_rom_closed(pts)
    body.append(f'<path d="{d}" class="fx-traj-glow"/>')
    body.append(f'<path d="{d}" class="fx-traj" pathLength="1"/>')
    body.append(f'<circle r="4.2" class="fx-traveller" style="offset-path:path(\'{d}\')"/>')
    body.append(arrow(22, 236, 74, 236) + arrow(22, 236, 22, 190))
    body.append(label(80, 239, "dimension 1") + label(28, 188, "dimension 2"))
    return svg("state-space", "a trajectory of brain activity dwelling in four recurring states and moving between them",
               "".join(body), defs)


# 2 ─ Network graph, young vs older ────────────────────────────────────────────
def network_ageing():
    modules = {
        "a": [(62, 96), (106, 74), (138, 112), (112, 156), (66, 146)],
        "b": [(246, 52), (296, 40), (334, 76), (300, 108), (252, 98)],
        "c": [(256, 170), (302, 152), (342, 190), (304, 222), (258, 214)],
    }
    centre = (205, 128)
    shift = {}
    for m, nodes in modules.items():
        mx = sum(p[0] for p in nodes) / len(nodes)
        my = sum(p[1] for p in nodes) / len(nodes)
        shift[m] = ((centre[0] - mx) * 0.22, (centre[1] - my) * 0.22)
    rng = random.Random(9)
    jitter = {(m, i): (rng.uniform(-5, 5), rng.uniform(-5, 5)) for m in modules for i in range(5)}

    def pos(m, i, older):
        x, y = modules[m][i]
        if not older:
            return x, y
        return x + shift[m][0] + jitter[m, i][0], y + shift[m][1] + jitter[m, i][1]

    ring = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0)]
    chords = [(0, 2), (1, 3), (2, 4), (1, 4)]
    young_inter = [("a", 2, "b", 4), ("b", 3, "c", 1)]
    older_inter = [("a", 2, "b", 4), ("b", 3, "c", 1), ("a", 1, "b", 0), ("a", 3, "c", 0),
                   ("a", 2, "c", 4), ("b", 2, "c", 2), ("a", 4, "c", 4), ("b", 4, "c", 0), ("a", 0, "b", 0)]

    def line(p, q, cls):
        return f'<line x1="{f(p[0])}" y1="{f(p[1])}" x2="{f(q[0])}" y2="{f(q[1])}" class="{cls}"/>'

    young, older = [], []
    for m in modules:
        for i, j in ring + chords:
            young.append(line(pos(m, i, False), pos(m, j, False), "fx-edge"))
        for i, j in ring[::2]:
            older.append(line(pos(m, i, True), pos(m, j, True), "fx-edge fx-edge--thin"))
    for m1, i, m2, j in young_inter:
        young.append(line(pos(m1, i, False), pos(m2, j, False), "fx-edge fx-edge--inter"))
    for m1, i, m2, j in older_inter:
        older.append(line(pos(m1, i, True), pos(m2, j, True), "fx-edge fx-edge--inter"))

    nodes = []
    for m, pts in modules.items():
        for i in range(5):
            x, y = pos(m, i, False)
            ox, oy = pos(m, i, True)
            nodes.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="6" class="fx-node fx-node--{m}" '
                         f'style="--dx:{f(ox - x)}px;--dy:{f(oy - y)}px"/>')
    defs, grid = dot_grid("network-ageing")
    body = (grid + f'<g class="net-young">{"".join(young)}</g>'
            f'<g class="net-older">{"".join(older)}</g><g class="net-nodes">{"".join(nodes)}</g>'
            '<g class="net-tags"><text x="22" y="236" class="fx-tag net-tag-young">young: segregated modules</text>'
            '<text x="22" y="236" class="fx-tag net-tag-older">older: modules blur together</text></g>')
    return svg("network-ageing", "a brain network whose three modules become less segregated in the older state", body, defs)


# 3 ─ OCT skin cross-section with segmentation overlay ─────────────────────────
def oct_skin():
    x0, x1, top, bottom = 24, 376, 24, 226
    xs = list(range(x0, x1 + 1, 4))

    def gauss(x, mu, s):
        return math.exp(-((x - mu) / s) ** 2)

    surf = [70 + 5 * math.sin(x / 37) + 30 * gauss(x, 205, 40) for x in xs]
    dej = [s + (24 + 3 * math.sin(x / 19)) * (1 - 0.75 * gauss(x, 205, 34)) for x, s in zip(xs, surf)]
    derm = [d + 74 + 6 * math.sin(x / 51) for x, d in zip(xs, dej)]

    def band(upper, lower):
        pts = [f"{x},{f(y)}" for x, y in zip(xs, upper)] + [f"{x},{f(y)}" for x, y in zip(reversed(xs), reversed(lower))]
        return " ".join(pts)

    def curve(ys):
        return "M" + " L".join(f"{x} {f(y)}" for x, y in zip(xs, ys))

    floor = [bottom] * len(xs)
    defs = ('<filter id="fig-oct-speckle" x="0" y="0" width="100%" height="100%">'
            '<feTurbulence type="fractalNoise" baseFrequency="0.9 0.42" numOctaves="2" seed="11" result="n"/>'
            '<feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  2.6 0 0 0 -0.9" result="s"/>'
            '<feComposite in="SourceGraphic" in2="s" operator="in"/></filter>'
            f'<clipPath id="fig-oct-frame"><rect x="{x0}" y="{top}" width="{x1 - x0}" height="{bottom - top}" rx="8"/></clipPath>')
    body = [f'<rect x="{x0}" y="{top}" width="{x1 - x0}" height="{bottom - top}" rx="8" class="fx-deep"/>',
            '<g clip-path="url(#fig-oct-frame)">',
            '<g filter="url(#fig-oct-speckle)">',
            f'<polygon points="{band(surf, dej)}" class="oct-tissue" style="--o:.95"/>',
            f'<polygon points="{band(dej, derm)}" class="oct-tissue" style="--o:.6"/>',
            f'<polygon points="{band(derm, floor)}" class="oct-tissue" style="--o:.28"/>',
            '</g>',
            '<g class="oct-seg">',
            f'<polygon points="{band(surf, dej)}" class="oct-seg-epi"/>',
            f'<polygon points="{band(dej, derm)}" class="oct-seg-derm"/>',
            f'<path d="{curve(surf)}" class="oct-line oct-line--epi"/>',
            f'<path d="{curve(dej)}" class="oct-line oct-line--dej"/>',
            f'<path d="{curve(derm)}" class="oct-line oct-line--derm"/>',
            '</g></g>',
            label(366, 44, "OCT B-scan", "fx-label fx-on-deep", "end")]
    i_epi, i_derm = xs.index(332), xs.index(332)
    body += [f'<path d="M332 {f((surf[i_epi] + dej[i_epi]) / 2)} h14" class="fx-leader"/>',
             label(349, (surf[i_epi] + dej[i_epi]) / 2 + 3.5, "epidermis", "fx-label fx-on-deep fx-small"),
             f'<path d="M332 {f((dej[i_derm] + derm[i_derm]) / 2)} h14" class="fx-leader"/>',
             label(349, (dej[i_derm] + derm[i_derm]) / 2 + 3.5, "dermis", "fx-label fx-on-deep fx-small"),
             label(205, 70, "wound", "fx-label fx-on-deep fx-small", "middle"),
             '<path d="M205 75 v14" class="fx-leader"/>']
    return svg("oct-skin", "an optical coherence tomography cross-section of skin with a wound, overlaid with a layer segmentation",
               "".join(body), defs)


# 4 ─ LFP trace with a sharp-wave ripple and a sleep-stage strip ───────────────
def lfp_ripple():
    rng = random.Random(21)
    n, dur, t0 = 640, 1.2, 0.70
    x0, x1 = 30, 380

    def X(i):
        return x0 + (x1 - x0) * i / (n - 1)

    ts = [dur * i / (n - 1) for i in range(n)]
    env = [math.exp(-((t - t0) / 0.016) ** 2) for t in ts]
    rip = [9 * e * math.sin(2 * math.pi * 165 * t) for t, e in zip(ts, env)]
    noise = 0.0
    lfp = []
    for t, r in zip(ts, rip):
        noise = 0.75 * noise + rng.gauss(0, 1.4)
        sharp = -16 * math.exp(-((t - t0) / 0.035) ** 2)
        lfp.append(100 - (12 * math.sin(2 * math.pi * 1.4 * t + 0.6) + 5 * math.sin(2 * math.pi * 3.3 * t) + noise + sharp + r))
    band = [196 - (r * 1.9 + rng.gauss(0, 0.35)) for r in rip]

    def poly(ys, cls):
        return f'<polyline points="{" ".join(f"{f(X(i))},{f(y)}" for i, y in enumerate(ys))}" class="{cls}"/>'

    rx = X(int(t0 / dur * (n - 1)))
    stages = [(0.00, 0.10, "wake"), (0.10, 0.36, "nrem"), (0.36, 0.43, "rem"), (0.43, 0.70, "nrem"),
              (0.70, 0.76, "wake"), (0.76, 0.93, "nrem"), (0.93, 1.00, "rem")]
    strip = "".join(f'<rect x="{f(x0 + (x1 - x0) * a)}" y="28" width="{f((x1 - x0) * (b - a))}" height="13" class="hyp hyp--{s}"/>'
                    for a, b, s in stages)
    zx = x0 + (x1 - x0) * 0.58
    body = [label(x0, 22, "sleep stage"),
            label(x1, 22, "<tspan class='k-nrem'>■</tspan> NREM  <tspan class='k-rem'>■</tspan> REM  <tspan class='k-wake'>■</tspan> wake", "fx-label fx-small", "end"),
            strip,
            f'<rect x="{f(zx - 3)}" y="25" width="6" height="19" rx="1.5" class="fx-window"/>',
            f'<path d="M{f(zx - 3)} 44 L{x0} 60 M{f(zx + 3)} 44 L{x1} 60" class="fx-zoom"/>',
            label(x0, 70, "LFP"),
            f'<rect x="{f(rx - 26)}" y="66" width="52" height="74" rx="6" class="fx-highlight"/>',
            label(rx, 64, "ripple", "fx-label fx-accent-text", "middle"),
            poly(lfp, "fx-trace"),
            label(x0, 166, "ripple band"),
            poly(band, "fx-trace fx-trace--accent"),
            '<path d="M318 236 h50" class="fx-scale"/>', label(343, 232, "100 ms", "fx-label fx-small", "middle")]
    return svg("lfp-ripple", "a local field potential trace with a sharp-wave ripple during non-REM sleep, and a sleep-stage strip",
               "".join(body))


# 5 ─ Peptide features → model → enzyme class ──────────────────────────────────
def peptide_class():
    seq = "MKVLATGE"
    beads = []
    for i, aa in enumerate(seq):
        x = 28 + i * 11.5
        y = 125 + 30 * math.sin(i * 0.95)
        beads.append((x, y, aa))
    chain = "M" + " L".join(f"{f(x)} {f(y)}" for x, y, _ in beads)
    body = [label(20, 52, "peptide", "fx-label fx-strong"), f'<path d="{chain}" class="fx-bond"/>']
    for x, y, aa in beads:
        body.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="9" class="fx-bead"/>' + label(x, y + 3.6, aa, "fx-label fx-bead-text", "middle"))
    body.append(arrow(122, 125, 140, 125))
    feats = [("MW", 0.8), ("pI", 0.55), ("charge", 0.35), ("% Ala", 0.62), ("% Lys", 0.44)]
    body.append(label(146, 52, "pepstats features", "fx-label fx-strong"))
    for k, (name, v) in enumerate(feats):
        y = 74 + k * 22
        body.append(label(146, y + 4, name, "fx-label fx-small"))
        body.append(f'<rect x="182" y="{y - 5}" width="44" height="9" rx="4.5" class="fx-track"/>')
        body.append(f'<rect x="182" y="{y - 5}" width="{f(44 * v)}" height="9" rx="4.5" class="fx-bar"/>')
    body.append(arrow(232, 125, 248, 125))
    layers = [[90, 125, 160], [78, 108, 142, 172], [96, 125, 154]]
    lx = [258, 282, 306]
    for a in range(2):
        for ya in layers[a]:
            for yb in layers[a + 1]:
                body.append(f'<line x1="{lx[a]}" y1="{ya}" x2="{lx[a + 1]}" y2="{yb}" class="fx-edge fx-edge--thin"/>')
    for li, ys in enumerate(layers):
        for y in ys:
            body.append(f'<circle cx="{lx[li]}" cy="{y}" r="5" class="fx-node fx-node--a"/>')
    body.append(label(282, 52, "ANN / forest", "fx-label fx-strong", "middle"))
    body.append(arrow(314, 125, 330, 125))
    probs = [0.14, 0.62, 0.32, 0.18, 0.22, 0.1]
    body.append(label(338, 52, "EC class", "fx-label fx-strong"))
    best = max(range(len(probs)), key=probs.__getitem__)
    for k, p in enumerate(probs):
        y = 70 + k * 21
        body.append(label(338, y + 4, f"EC {k + 1}", "fx-label fx-small"))
        cls = "fx-bar fx-bar--accent" if k == best else "fx-bar fx-bar--muted"
        body.append(f'<rect x="362" y="{y - 5}" width="{f(26 * p / max(probs))}" height="9" rx="4.5" class="{cls}"/>')
    return svg("peptide-class", "a peptide sequence summarised as physicochemical features, fed to a classifier that outputs enzyme-class scores",
               "".join(body))


# 6 ─ Neural activity → image identity ─────────────────────────────────────────
def neural_decoding():
    rng = random.Random(5)
    body = [label(24, 30, "neurons × time", "fx-label fx-strong")]
    t0, t1, s0, s1 = 30, 168, 92, 132
    body.append(f'<rect x="{s0}" y="44" width="{s1 - s0}" height="160" rx="5" class="fx-highlight"/>')
    body.append(label((s0 + s1) / 2, 218, "stimulus", "fx-label fx-small fx-accent-text", "middle"))
    for r in range(12):
        y = 52 + r * 13
        body.append(f'<line x1="{t0}" y1="{y}" x2="{t1}" y2="{y}" class="fx-row"/>')
        rate_in = rng.choice([0.05, 0.12, 0.2])
        for t in range(t0, t1, 3):
            p = rate_in if s0 <= t <= s1 else 0.035
            if rng.random() < p:
                body.append(f'<line x1="{t}" y1="{y - 4.5}" x2="{t}" y2="{y + 4.5}" class="fx-spike"/>')
    body.append(arrow(176, 124, 196, 124))
    body.append(f'<rect x="202" y="96" width="58" height="56" rx="10" class="fx-box"/>')
    body.append(label(231, 128, "decoder", "fx-label fx-strong", "middle"))
    body.append(arrow(266, 124, 284, 124))
    body.append(label(292, 30, "image identity", "fx-label fx-strong"))
    glyphs = [
        '<circle cx="12" cy="12" r="6" class="fx-glyph"/>',
        '<path d="M3 20 L10 8 L15 15 L18 11 L22 20 Z" class="fx-glyph"/>',
        '<path d="M5 20 V10 L12 4 L19 10 V20 Z" class="fx-glyph"/>',
        '<path d="M12 4 C20 8 20 17 12 21 C4 17 4 8 12 4 Z M12 6 V20" class="fx-glyph"/>',
    ]
    probs = [0.18, 0.71, 0.24, 0.12]
    for k, (g, p) in enumerate(zip(glyphs, probs)):
        y = 50 + k * 44
        best = p == max(probs)
        body.append(f'<g transform="translate(292 {y})"><rect width="24" height="24" rx="6" class="fx-tile{" fx-tile--accent" if best else ""}"/>{g}</g>')
        body.append(f'<rect x="324" y="{y + 8}" width="52" height="8" rx="4" class="fx-track"/>')
        body.append(f'<rect x="324" y="{y + 8}" width="{f(52 * p)}" height="8" rx="4" class="fx-bar{" fx-bar--accent" if best else " fx-bar--muted"}"/>')
    return svg("neural-decoding", "spike trains from a population of neurons decoded into scores for four image categories",
               "".join(body))


# 7 ─ Video → neuro-inspired network → fMRI voxels ─────────────────────────────
def video_fmri():
    rng = random.Random(8)
    body = [label(22, 30, "video frames", "fx-label fx-strong")]
    for k in range(3):
        x, y = 24 + k * 12, 60 + k * 12
        body.append(f'<rect x="{x}" y="{y}" width="78" height="56" rx="6" class="fx-frame"/>')
    body.append('<circle cx="72" cy="104" r="9" class="fx-glyph"/><path d="M52 136 L70 118 L82 128 L92 120 L106 136" class="fx-glyph"/>')
    body.append(label(63, 160, "t → t+1", "fx-label fx-small", "middle"))
    body.append(arrow(120, 112, 140, 112))
    body.append(label(196, 30, "neuro-inspired network", "fx-label fx-strong", "middle"))
    for k, (w, h) in enumerate([(14, 92), (14, 72), (14, 54), (14, 38)]):
        x = 150 + k * 26
        y = 112 - h / 2
        body.append(f'<path d="M{x} {f(y)} l{w} -8 v{h} l-{w} 8 Z" class="fx-layer" style="--o:{0.18 + k * 0.12:.2f}"/>')
    body.append(arrow(258, 112, 276, 112))
    body.append(label(330, 30, "fMRI response", "fx-label fx-strong", "middle"))
    for r in range(6):
        for c in range(6):
            v = max(0.06, min(1, 0.55 + 0.4 * math.sin(c * 0.9 + r * 0.6) * math.cos(r * 0.4) + rng.uniform(-0.2, 0.2)))
            body.append(f'<rect x="{286 + c * 15}" y="{62 + r * 15}" width="13" height="13" rx="2.5" class="fx-voxel" style="--o:{v:.2f}"/>')
    body.append(label(330, 168, "voxels", "fx-label fx-small", "middle"))
    body.append("".join(f'<rect x="{286 + k * 8}" y="190" width="8" height="7" class="fx-ramp" style="--o:{0.08 + k * 0.092:.2f}"/>'
                        for k in range(11)))
    body.append(label(286, 210, "low", "fx-label fx-small") + label(374, 210, "high", "fx-label fx-small", "end"))
    return svg("video-fmri", "video frames passed through a layered neural network that predicts voxel-wise fMRI responses",
               "".join(body))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    figures = {
        "state-space": state_space, "network-ageing": network_ageing, "oct-skin": oct_skin,
        "lfp-ripple": lfp_ripple, "peptide-class": peptide_class, "neural-decoding": neural_decoding,
        "video-fmri": video_fmri,
    }
    for name, fn in figures.items():
        path = OUT / f"{name}.svg"
        path.write_text(fn(), encoding="utf-8")
        print(f"  {path.relative_to(ROOT)}  {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
