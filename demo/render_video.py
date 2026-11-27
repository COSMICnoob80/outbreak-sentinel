"""Render the hackathon demo video as footage of the operations console.

V-5 merges the two approved ancestors: the motion pipeline of the v1 cut
(v1-backup: progressive reveal at ``REVEAL_SPAN``, one cut-to-detail
magnification move, its ramp and hold) renders the console-mirrored scene skin
of v2. Where a v1 behaviour did not fit a v2 scene the scene was adapted to the
motion, not the reverse — v2's second mid-scene cut (scene 2's cited-stories
plate) was the drift and is gone: all five cited reports now render inline on
the card, so scene 2 is one uninterrupted reveal like every v1 scene.

Every string, number, hash and path on screen is read from
``state/video-capture/snapshot.json`` (produced by ``capture_video_data.py``).
Nothing is hand-written: captions interpolate captured values, and scenes draw
card fields, receipt rows and settlement facts verbatim.

The look is not a cousin of the console — it is the console's design system.
The tokens below are transcribed from ``dashboard/index.html`` ``:root``
(OKLCH, converted to sRGB with the same L/C/h values), and every scene reuses
that page's anatomy: near-black ground, one lime accent for verified state, a
severity ramp (red 22 -> orange 44 -> amber 92 -> neutral 146), a 3px severity
left edge on risk cards, instrument strip, mono telemetry, chips, and the
"Top open signal" hero with its severity top edge.

Type is Inter (OFL) from ``demo/assets/fonts/`` — the console's UI face. Inter
ships no monospace companion, so telemetry uses DejaVu Sans Mono, exactly the
role the console's ``--font-mono`` stack plays. There is no audio track, on
purpose: the cut is caption-driven, so no licensed music enters a public
submission.

Frames are built with Pillow at 1920x1080 and piped as raw rgb24 straight into
ffmpeg — no PNGs on disk.

    env -u PYTHONPATH .venv/bin/python demo/render_video.py
    env -u PYTHONPATH .venv/bin/python demo/render_video.py --montage /tmp/m.png
    env -u PYTHONPATH .venv/bin/python demo/render_video.py --stills demo/screenshots

The camera never leaves the frame: two scenes end on a detail hold — scene 2 on
the LA card's cited-stories block, scene 5 on the whole evidence panel. Each
block is fitted first and then eases up to a layout that is itself laid out
inside the frame — so nothing is ever cropped, zoomed past, or panned past the
edge.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT = ROOT / "state" / "video-capture" / "snapshot.json"
OUT_DIR = ROOT / "demo"
OUT_VIDEO = OUT_DIR / "outbreak-sentinel-demo-v3.mp4"

W, H, FPS = 1920, 1080, 30

ASSETS = OUT_DIR / "assets" / "fonts"
FONT_UI = ASSETS / "InterVariable.ttf"
OFL = ASSETS / "OFL.txt"
MONO_DIR = Path("/usr/share/fonts/truetype/dejavu")
MONO = MONO_DIR / "DejaVuSansMono.ttf"
MONO_BOLD = MONO_DIR / "DejaVuSansMono-Bold.ttf"

# ── palette: dashboard/index.html :root, OKLCH -> sRGB ───────────────────────
# surfaces: charcoal tinted toward the phosphor hue (L 0.155 .. 0.392)
BG = (10, 13, 10)            # --bg          oklch(0.155 0.008 146)
SURFACE1 = (18, 22, 18)      # --surface-1        0.196 0.010 146
SURFACE2 = (25, 30, 25)      # --surface-2        0.228 0.012 146
SURFACE3 = (34, 40, 34)      # --surface-3        0.268 0.014 146
LINE = (43, 48, 43)          # --line             0.302 0.012 146
LINE_STRONG = (64, 72, 64)   # --line-strong      0.392 0.016 146
# ink ladder
INK = (242, 246, 242)        # --ink        0.968 0.006 146
INK_MID = (227, 233, 227)    # --ink-mid    0.928 0.010 146
INK_DIM = (217, 223, 217)    # --ink-dim    0.898 0.011 146
INK_FAINT = (207, 213, 207)  # --ink-faint  0.866 0.011 146
# accent: phosphor signal green, used only for verified/live state
ACCENT = (173, 232, 79)      # --accent         0.862 0.190 128
ACCENT_STRONG = (149, 209, 28)  # --accent-strong  0.790 0.200 128
ACCENT_INK = (11, 15, 6)     # --accent-ink     0.160 0.020 128
# severity ramp: hue travels 22 -> 44 -> 92 -> 146
SEV_CRITICAL = (255, 154, 153)  # 0.845 0.172 22
SEV_HIGH = (255, 169, 118)      # 0.845 0.152 44
SEV_MODERATE = (244, 210, 105)  # 0.872 0.130 92
SEV_LOW = (182, 193, 182)       # 0.800 0.020 146
SEV_EDGE_LOW = LINE_STRONG      # LOW takes the shared hairline, as in the console

LEVEL_COLOR = {
    "LOW": SEV_LOW,
    "MODERATE": SEV_MODERATE,
    "HIGH": SEV_HIGH,
    "CRITICAL": SEV_CRITICAL,
}
LEVEL_EDGE = {
    "LOW": SEV_EDGE_LOW,
    "MODERATE": SEV_MODERATE,
    "HIGH": SEV_HIGH,
    "CRITICAL": SEV_CRITICAL,
}

MARGIN_X = 120
SHELL_W = W - 2 * MARGIN_X
MAST_DIVIDER_Y = 150
BODY_TOP = 170
CAPTION_TOP = 956
BODY_BOT = 916
# Each scene finishes revealing its items by this fraction of its runtime, then
# holds a fully-drawn frame so the later captions land on complete content.
# v1's pacing, restored after v2 stretched it to 0.58.
REVEAL_SPAN = 0.55

# The cut's single move: scene 5 ends on a detail hold of the dense evidence
# panel. The block is laid out once at ZOOM_MAX; the push-in eases from the
# 1.0x layout to that fitted one, so the widest framing IS the layout — the
# camera can never pass the frame edge, and no column or glyph can be clipped.
# Ramp and hold are v1's numbers, unchanged.
ZOOM_MAX = 1.5
ZOOM_RAMP_S = 0.5
ZOOM_HOLD_S = 4.0
ZOOM_TOTAL_S = ZOOM_RAMP_S + ZOOM_HOLD_S
ZOOM_BOX = (MARGIN_X, 162, W - MARGIN_X, BODY_BOT)

# Bottom caption strip: one size step above v2's 26 (readability on a projector
# and on a phone), still inside the margins with the same 2-line clamp.
CAPTION_SIZE = 30
CAPTION_LEAD = 42


def mix(a, b, f):
    f = max(0.0, min(1.0, f))
    return tuple(int(a[i] + (b[i] - a[i]) * f) for i in range(3))


# ── type: Inter (UI) + DejaVu Sans Mono (telemetry) ──────────────────────────

_FONT_CACHE: dict[tuple, ImageFont.FreeTypeFont] = {}


def ui(size: int, weight: int = 450) -> ImageFont.FreeTypeFont:
    """Inter Variable, optical size tracking the render size (14..32 axis)."""
    key = ("ui", size, weight)
    fnt = _FONT_CACHE.get(key)
    if fnt is None:
        fnt = ImageFont.truetype(str(FONT_UI), size)
        opsz = min(32, max(14, round(size * 0.62)))
        fnt.set_variation_by_axes([opsz, weight])
        _FONT_CACHE[key] = fnt
    return fnt


def mono(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    key = ("mono", size, bold)
    fnt = _FONT_CACHE.get(key)
    if fnt is None:
        fnt = ImageFont.truetype(str(MONO_BOLD if bold else MONO), size)
        _FONT_CACHE[key] = fnt
    return fnt


def wrap(text: str, fnt, max_w: int) -> list[str]:
    words, lines, cur = (text or "").split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if fnt.getlength(trial) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def wrap_sep(text: str, fnt, max_w: int, sep: str = " · "):
    """Break on field separators first, so a clause is never orphaned."""
    parts = (text or "").split(sep)
    lines, cur = [], ""
    for part in parts:
        trial = part if not cur else f"{cur}{sep}{part}"
        if fnt.getlength(trial) <= max_w:
            cur = trial
            continue
        if cur:
            lines.append(cur)
        if fnt.getlength(part) > max_w:
            sub = wrap(part, fnt, max_w)
            lines.extend(sub[:-1])
            cur = sub[-1]
        else:
            cur = part
    if cur:
        lines.append(cur)
    return lines or [""]


def trunc(s: str, fnt, max_w: int) -> str:
    s = s or ""
    if fnt.getlength(s) <= max_w:
        return s
    while s and fnt.getlength(s + "...") > max_w:
        s = s[:-1]
    return s.rstrip() + "..."


def wrap_clamped(text: str, fnt, max_w: int, max_lines: int) -> list[str]:
    """Word-wrap, then ellipsize the last kept line if the text overruns."""
    lines = wrap(text, fnt, max_w)
    if len(lines) <= max_lines:
        return lines
    kept = lines[:max_lines]
    tail = " ".join(lines[max_lines - 1:])
    kept[-1] = trunc(tail, fnt, max_w)
    return kept


# Current scene index, so Frame can read its measured reveal count.
_CURRENT = {"i": 0}
_SCENE_N: dict[int, int] = {}


class Frame:
    """Draw onto a supplied image with a stable layout and fades in place.

    Layout never depends on reveal progress: callers advance their y-cursor by
    a fixed row height whether or not a line is visible yet, so content fades in
    without shoving the rest of the layout around. ``_counting`` mode tallies
    draw calls so each scene's reveal pacing matches how much it actually draws.
    """

    _counting = False
    _count = 0

    def __init__(self, img, p: float):
        self.img = img
        self.d = ImageDraw.Draw(img)
        self.p = p
        self.n = max(1, _SCENE_N.get(_CURRENT["i"], 16))
        self._shown = 0

    def _reveal(self) -> float:
        idx = self._shown
        self._shown += 1
        if Frame._counting:
            Frame._count += 1
            return 1.0
        step = 1.0 / (self.n + 1)
        start = idx * step
        pe = min(1.0, self.p / REVEAL_SPAN)
        if pe < start:
            return 0.0
        return min(1.0, (pe - start) / max(step * 0.6, 1e-6))

    def _visible(self, a: float) -> bool:
        return (not Frame._counting) and a > 0

    # -- primitives ---------------------------------------------------------
    def text(self, xy, s, size=25, color=INK, weight=450, mono_bold=False,
             telemetry=False, anchor="la"):
        a = self._reveal()
        if self._visible(a):
            fnt = mono(size, mono_bold) if telemetry else ui(size, weight)
            self.d.text(xy, s, font=fnt, fill=mix(BG, color, a), anchor=anchor)
        return size

    def panel(self, box, border=LINE, fill=SURFACE1, radius=16, width=2,
              top_edge=None, left_edge=None, edge_w=6, edge_inset=2):
        a = self._reveal()
        if not self._visible(a):
            return
        x0, y0, x1, y1 = box
        self.d.rounded_rectangle([(x0, y0), (x1, y1)], radius=radius,
                                 outline=mix(BG, border, a),
                                 fill=mix(BG, fill, a), width=width)
        if top_edge is not None:
            self.d.line([(x0 + radius + edge_inset, y0 + edge_w / 2 - 1),
                         (x1 - radius - edge_inset, y0 + edge_w / 2 - 1)],
                        fill=mix(BG, top_edge, a), width=edge_w)
        if left_edge is not None:
            self.d.line([(x0 + edge_w / 2 - 1, y0 + radius),
                         (x0 + edge_w / 2 - 1, y1 - radius)],
                        fill=mix(BG, left_edge, a), width=edge_w)

    def rect(self, box, color, radius=0):
        a = self._reveal()
        if not self._visible(a):
            return
        if radius:
            self.d.rounded_rectangle(box, radius=radius, fill=mix(BG, color, a))
        else:
            self.d.rectangle(box, fill=mix(BG, color, a))

    def line(self, pts, color, width=2):
        a = self._reveal()
        if not self._visible(a):
            return
        self.d.line(pts, fill=mix(BG, color, a), width=width)

    def hline(self, x0, x1, y, color=LINE, width=1):
        self.line([(x0, y), (x1, y)], color, width)

    def spark(self, box, values, color, alpha):
        """The captured 7-day series, drawn through this frame's own surface."""
        spark(self.d, box, values, color, alpha)

    def chip(self, xy, s, fg=INK_DIM, bg=None, border=LINE, size=17,
             padx=10, pady=4, telemetry=True, draw=True):
        """A console .tag/.chip: 1px hairline, 6px radius, mono label.

        ``draw=False`` measures the chip without painting it or consuming a
        reveal slot, so callers can wrap a row of chips to a width.
        """
        fnt = mono(size) if telemetry else ui(size)
        x, y = xy
        h = size + 2 * pady + 4
        w = int(fnt.getlength(s)) + 2 * padx
        if not draw:
            return w, h
        a = self._reveal()
        if self._visible(a):
            fill = bg if bg is not None else SURFACE1
            self.d.rounded_rectangle([(x, y), (x + w, y + h)], radius=6,
                                     outline=mix(BG, border, a),
                                     fill=mix(BG, fill, a), width=1)
            self.d.text((x + padx, y + pady + 1), s, font=fnt,
                        fill=mix(BG, fg, a))
        return w, h

    def sev_chip(self, xy, level, size=17, draw=True):
        """Console .level/.sev-chip: wash fill, 6px dot, mono label.

        ``draw=False`` measures the chip without painting it or consuming a
        reveal slot, so callers can lay text out to its right.
        """
        sev = LEVEL_COLOR.get(level, SEV_LOW)
        fnt = mono(size, bold=True)
        x, y = xy
        h = size + 10
        w = int(fnt.getlength(level)) + 30
        if not draw:
            return w, h
        a = self._reveal()
        if self._visible(a):
            wash = mix(SURFACE1, sev, 0.12)
            self.d.rounded_rectangle([(x, y), (x + w, y + h)], radius=6,
                                     outline=mix(BG, wash, a),
                                     fill=mix(BG, wash, a), width=1)
            self.d.ellipse([(x + 9, y + h / 2 - 3), (x + 15, y + h / 2 + 3)],
                           fill=mix(BG, sev, a))
            self.d.text((x + 20, y + 4), level, font=fnt, fill=mix(BG, sev, a))
        return w, h


class Measure(Frame):
    """A Frame that draws nothing and takes no reveal slot — it only records the
    extent of what would be drawn.

    Panels are sized to their content (v1's behaviour: a card is as tall as what
    it says, never padded out to a fixed height). Sizing needs the content's
    bottom edge before the panel can be painted behind it, so scenes lay their
    content out once here, then once for real.
    """

    def __init__(self):
        self.img = None
        self.d = None
        self.p = 1.0
        self._shown = 0
        self.bottom = 0
        self.right = 0

    def text(self, xy, s, size=25, color=INK, weight=450, mono_bold=False,
             telemetry=False, anchor="la"):
        self.bottom = max(self.bottom, xy[1] + int(size * 1.3))
        return size

    def panel(self, box, border=LINE, fill=SURFACE1, radius=16, width=2,
              top_edge=None, left_edge=None, edge_w=6, edge_inset=2):
        self.bottom = max(self.bottom, box[3])
        self.right = max(self.right, box[2])

    def rect(self, box, color, radius=0):
        self.bottom = max(self.bottom, box[3])

    def line(self, pts, color, width=2):
        self.bottom = max(self.bottom, max(p[1] for p in pts))

    def spark(self, box, values, color, alpha):
        self.bottom = max(self.bottom, box[1] + box[3])

    def chip(self, xy, s, fg=INK_DIM, bg=None, border=LINE, size=17,
             padx=10, pady=4, telemetry=True, draw=True):
        fnt = mono(size) if telemetry else ui(size)
        x, y = xy
        h = size + 2 * pady + 4
        w = int(fnt.getlength(s)) + 2 * padx
        if draw:
            self.bottom = max(self.bottom, y + h)
        return w, h

    def sev_chip(self, xy, level, size=17, draw=True):
        w, h = Frame.sev_chip(self, xy, level, size, draw=False)
        if draw:
            self.bottom = max(self.bottom, xy[1] + h)
        return w, h


class Captions:
    """Bottom caption bar; the visible sub changes at progress thresholds."""

    def __init__(self, subs):
        self.subs = subs

    def draw(self, img, p):
        text = ""
        for start, s in self.subs:
            if p >= start:
                text = s
        d = ImageDraw.Draw(img)
        d.rectangle([(0, CAPTION_TOP - 18), (W, H)], fill=BG)
        d.line([(MARGIN_X, CAPTION_TOP - 18), (W - MARGIN_X, CAPTION_TOP - 18)],
               fill=LINE, width=1)
        if not text:
            return
        fnt = ui(CAPTION_SIZE, 450)
        y = CAPTION_TOP
        for ln in wrap(text, fnt, SHELL_W - 60)[:2]:
            d.text((W // 2, y), ln, font=fnt, fill=INK_MID, anchor="ma")
            y += CAPTION_LEAD


# ── console chrome ───────────────────────────────────────────────────────────


def chrome(img, snap, scene_label, overall_p, scene_i):
    """The console masthead, drawn as page furniture above every scene."""
    d = ImageDraw.Draw(img)
    st = snap["telegraph_status"]
    x, y = MARGIN_X, 44
    # brand mark: accent square with the wash ring, as .brand-mark
    d.rounded_rectangle([(x - 4, y - 4), (x + 18, y + 18)], radius=7,
                        outline=mix(BG, ACCENT, 0.35), width=2)
    d.rounded_rectangle([(x, y), (x + 14, y + 14)], radius=4, fill=ACCENT)
    title = "Outbreak Sentinel"
    d.text((x + 34, y - 10), title, font=ui(34, 650), fill=INK)

    # live status badge (console .status-badge.sys-live)
    bx = x + 34 + int(ui(34, 650).getlength(title)) + 24
    bw, bh = 96, 30
    d.rounded_rectangle([(bx, y + 2), (bx + bw, y + 2 + bh)], radius=15,
                        outline=mix(BG, ACCENT, 0.40), fill=SURFACE1, width=1)
    d.ellipse([(bx + 12, y + 14), (bx + 18, y + 20)], fill=ACCENT)
    d.text((bx + 26, y + 10), "live", font=mono(16), fill=ACCENT)

    # right meta: mode / chain / network, then the capture stamp
    d.text((W - MARGIN_X, y - 2),
           f"mode {st['mode']} · chain {st['chain_id']} · {st['network_label']}",
           font=mono(17), fill=INK_FAINT, anchor="ra")
    d.text((W - MARGIN_X, y + 24), f"captured {snap['captured_at']}",
           font=mono(17), fill=INK_FAINT, anchor="ra")

    sub = ("Operations console · open bio-surveillance and hazard signals fused "
           "into calibrated risk cards, with on-chain settlement. "
           "Surveillance only, never diagnosis.")
    d.text((MARGIN_X, y + 40), trunc(sub, ui(19), SHELL_W), font=ui(19),
           fill=INK_DIM)
    d.line([(MARGIN_X, MAST_DIVIDER_Y), (W - MARGIN_X, MAST_DIVIDER_Y)],
           fill=LINE, width=1)

    # scene index + progress rule
    d.text((MARGIN_X, 1016),
           f"{scene_i + 1:02d} / {len(SCENES):02d}   {scene_label.upper()}",
           font=mono(17), fill=INK_FAINT)
    d.text((W - MARGIN_X, 1016), snap["live_base"], font=mono(17),
           fill=INK_FAINT, anchor="ra")
    d.rectangle([(MARGIN_X, 1048), (W - MARGIN_X, 1052)], fill=LINE)
    d.rectangle([(MARGIN_X, 1048),
                 (MARGIN_X + int(SHELL_W * overall_p), 1052)], fill=ACCENT)


# ── shared console components ────────────────────────────────────────────────


def instruments(f, snap, x0, x1, y, h=100):
    """Console .instruments: one component of five readings, hairline-divided."""
    grid, stats = snap["grid"], snap["telegraph_stats"]
    cells = [
        ("News signals", str(grid["signals"]["news"]),
         f"city-scoped {grid['signals']['news_city_scoped']}", True),
        ("Risk cards", str(grid["card_count"]), f"{grid['city_count']} cities", True),
        ("Fusion engine", grid["engine"], "rules + narrator", False),
        ("Settlements", str(stats["settled"]),
         f"of {stats['assessments']} assessments", True),
        ("Receipt integrity", f"{stats['integrity_pct']:g}%", "sha256 ledger", True),
    ]
    ratios = [1.45, 0.85, 1.30, 1.05, 1.00]
    f.panel((x0, y, x1, y + h))
    total = sum(ratios)
    cx = x0
    bounds = []
    for r in ratios:
        w = (x1 - x0) * r / total
        bounds.append((cx, w))
        cx += w
    for i, ((label, value, note, tel), (cx, cw)) in enumerate(zip(cells, bounds)):
        if i:
            f.line([(cx, y + 12), (cx, y + h - 12)], LINE, 1)
        pad = 22
        f.text((cx + pad, y + 14), label, 16, INK_FAINT, telemetry=True)
        if tel:
            f.text((cx + pad, y + 38 if h >= 100 else y + 36), value,
                   30 if h >= 100 else 26, INK, telemetry=True, mono_bold=True)
        else:
            f.text((cx + pad, y + 40),
                   trunc(value, ui(21, 600), cw - 2 * pad), 21, INK, 600)
        if h >= 96:
            f.text((cx + pad, y + 76), note, 15, INK_FAINT)


def rail_rows(f, x, y, w, rows, row_h=46):
    """Console .rail-row: key left, mono value right, hairline between."""
    for i, (k, v, col) in enumerate(rows):
        ry = y + i * row_h
        if i:
            f.hline(x, x + w, ry)
        f.text((x, ry + 12), k, 19, INK_DIM)
        f.text((x + w, ry + 12), str(v), 19, col, telemetry=True, anchor="ra")


def spark(d, box, values, color, alpha):
    """The console's 7-day spark: area fill, stroke, one tick per slot.

    Geometry is the captured series — one x-step per point, height by value.
    """
    x, y, w, h = box
    if not values:
        d.text((x, y + h // 2), "no series", font=mono(16), fill=INK_FAINT)
        return
    n = len(values)
    mx = max(values) or 1.0
    pts = []
    for i, v in enumerate(values):
        px = x + (w * i / max(1, n - 1))
        py = y + h - int((v / mx) * (h - 4))
        pts.append((px, py))
    if len(pts) > 1:
        d.polygon(pts + [(x + w, y + h), (x, y + h)],
                  fill=mix(BG, color, alpha * 0.10))
        d.line(pts, fill=mix(BG, color, alpha), width=2, joint="curve")
    for px, _py in pts:
        d.line([(px, y + h - 3), (px, y + h)],
               fill=mix(BG, color, alpha * 0.45), width=2)
    d.line([(x, y + h), (x + w, y + h)], fill=mix(BG, LINE, alpha), width=1)


def hazard_of(card):
    return card.get("disease") or card["vertical"]


def n_sources(n: int) -> str:
    """``1 source`` / ``0 sources`` / ``5 sources`` — one plural decision."""
    return f"{n} {'source' if n == 1 else 'sources'}"


def receipt_of(snap, city):
    for r in snap["receipts"]["receipts"]:
        if r["city"] == city:
            return r
    return None


# ── Scenes ──────────────────────────────────────────────────────────────────


def scene_cold_open(img, p, S):
    """v1's title card at v1's scale, in the console's skin.

    v2 opened on a full console page here; that is scene 2's job. The open is a
    mark, a claim, and the live URL — so the first frames land at the size the
    operator asked for.
    """
    snap = S["snapshot"]
    grid = snap["grid"]
    health = snap["health"]
    f = Frame(img, p)

    left_w = 1180
    y = BODY_TOP + 40
    y += f.text((MARGIN_X, y), "Outbreak Sentinel", 84, INK, 650) + 34
    for ln in wrap("autonomous early-warning agent, paid through Telegraph",
                   ui(32), left_w):
        y += f.text((MARGIN_X, y), ln, 32, INK_DIM) + 10
    y += 26

    pw, ph = f.chip((MARGIN_X, y), f"live · {snap['live_base']}", ACCENT,
                    bg=mix(SURFACE2, ACCENT, 0.10),
                    border=mix(SURFACE2, ACCENT, 0.40), size=22, padx=14,
                    pady=8, telemetry=False)
    y += ph + 34

    for ln in wrap(
        f"{grid['card_count']} risk cards · {grid['city_count']} cities · "
        f"{len(grid['verticals'])} verticals · engine {grid['engine']}",
        ui(28), left_w,
    ):
        y += f.text((MARGIN_X, y), ln, 28, INK) + 10
    y += 22
    y += f.text((MARGIN_X, y),
                "SURVEILLANCE ONLY — never diagnosis, never treatment advice",
                28, SEV_HIGH, 600) + 18
    f.text((MARGIN_X, y),
           "Every card is a cited early-warning signal with traceable sources.",
           22, INK_DIM)

    bx = MARGIN_X + 1220
    f.panel((bx, BODY_TOP + 40, W - MARGIN_X, BODY_TOP + 372), radius=16,
            top_edge=ACCENT, edge_w=4)
    f.text((bx + 26, BODY_TOP + 58), "GET /health", 15, INK_FAINT,
           telemetry=True)
    fy = BODY_TOP + 92
    for label, val, col, tel in (
        ("status", f"{health.get('status')} · v{health.get('version')}", ACCENT, True),
        ("service", health.get("service"), INK, False),
        ("captured (UTC)", snap["captured_at"], INK_FAINT, True),
        ("grid timestamp", grid["timestamp"], INK_FAINT, True),
    ):
        f.text((bx + 26, fy), label, 15, INK_FAINT, telemetry=True)
        fy += 24
        f.text((bx + 26, fy), str(val), 20, col, telemetry=tel)
        fy += 42

    return Captions([
        (0.0, "Outbreak Sentinel — an autonomous early-warning agent, live at a "
              "public URL."),
        (0.45, "This video is built from the deployment's real API responses, "
               "captured at build time."),
    ])


def console_card(f, snap, card_top):
    """The live-console hero card, laid out top-down; returns its bottom edge.

    v1's composition and type sizes are the ones the operator preferred, so they
    are restored here rather than the whole-page shrink v2 rendered; the skin is
    still v2's — console surfaces, severity left edge, Inter, mono telemetry,
    cite/anatomy chips. All five cited reports are drawn on the card, so the
    count-parity caption describes something already on screen.
    """
    hero = snap["hero_la_wildfire"]
    sev = LEVEL_COLOR.get(hero["risk_level"], SEV_LOW)

    lx = MARGIN_X + 40
    rx = W - MARGIN_X - 500
    left_w = rx - 40 - lx

    hy = card_top + 30
    f.text((lx, hy), hero["city"], 46, INK, 650)
    cx_ = lx + int(ui(46, 650).getlength(hero["city"])) + 22
    cw, ch = f.sev_chip((0, 0), hero["risk_level"], size=19, draw=False)
    f.sev_chip((cx_, hy + 12), hero["risk_level"], 19)
    f.text((cx_ + cw + 18, hy + 8), str(hero["risk_score"]), 32, sev,
           telemetry=True, mono_bold=True)
    f.text((cx_ + cw + 18, hy + 46), "/100", 15, INK_FAINT, telemetry=True)

    iy = hy + 84
    tx = lx
    tw, th = f.chip((tx, iy), hero["vertical"], INK_DIM, border=LINE)
    tx += tw + 8
    rec = receipt_of(snap, hero["city"])
    if rec:
        tw, _ = f.chip((tx, iy), f"receipt {rec['receipt_id']}", SEV_MODERATE,
                        bg=mix(SURFACE1, SEV_MODERATE, 0.12),
                        border=mix(SURFACE1, SEV_MODERATE, 0.12))
        tx += tw + 8
    f.chip((tx, iy), n_sources(hero["source_count"]), INK_FAINT, border=LINE)
    iy += th + 18

    for ln in wrap(hero["evidence_line"], ui(21), left_w)[:2]:
        f.text((lx, iy), ln, 21, INK_DIM)
        iy += 28
    iy += 12
    for drv in hero["drivers"]:
        f.text((lx, iy), trunc(f"• {drv['text']}", ui(26), left_w), 26, INK)
        iy += 34
    iy += 12

    f.text((lx, iy), f"sources ({hero['source_count']}) — verbatim from /risk",
           20, ACCENT)
    iy += 28
    for i, src in enumerate(hero["sources"], 1):
        f.text((lx + 6, iy), trunc(f"{i}. {src['title']}", ui(20), left_w),
               20, INK)
        iy += 26
        f.text((lx + 6, iy), f"{src['outlet']} · {src['published']}", 16,
               INK_FAINT, telemetry=True)
        iy += 24

    # right column: confidence, then the captured 7-day series
    vals = [pt["value"] for pt in hero["chart"]]
    ry = card_top + 32
    f.text((rx, ry), f"confidence {hero['confidence']:g}", 21, INK_FAINT,
           telemetry=True)
    ry += 44
    f.text((rx, ry), "7-day precipitation outlook", 20, INK_DIM)
    ry += 30
    f.spark((rx, ry, W - MARGIN_X - 40 - rx, 150), vals, sev, 1.0)
    ry += 168
    f.text((rx, ry), f"points {len(vals)} · peak {max(vals) if vals else 0:g} mm",
           18, INK_FAINT, telemetry=True)
    ry += 30
    last = hero["chart"][-1]["label"] if hero["chart"] else "—"
    f.text((rx, ry), f"through {last}", 18, INK_FAINT, telemetry=True)
    ry += 34
    f.text((rx, ry),
           f"evidence_count {hero['evidence_count']} == sources "
           f"{hero['source_count']}", 18, ACCENT, telemetry=True)
    ry += 28
    f.text((rx, ry), "count and links are one number", 18, INK_FAINT)

    return max(iy, ry) + 26


def console_base_body(img, p, snap):
    """The console page: header lines, then the hero card sized to its content."""
    grid = snap["grid"]
    hero = snap["hero_la_wildfire"]
    f = Frame(img, p)

    y = BODY_TOP
    y += f.text((MARGIN_X, y), "THE LIVE CONSOLE", 38, INK, 650) + 16
    lv = ", ".join(f"{k} {v}" for k, v in grid["levels"].items())
    y += f.text((MARGIN_X, y),
                f"/risk · {grid['card_count']} cards · {grid['city_count']} "
                f"cities · levels {lv}", 24, INK_DIM) + 10
    sig = grid["signals"]
    y += f.text((MARGIN_X, y),
                f"signals: news {sig['news']} (city-scoped "
                f"{sig['news_city_scoped']}) · social {sig['social']} · "
                f"weather cities {sig['cities']}", 21, INK_FAINT) + 26

    card_top = y
    m = Measure()
    card_bot = console_card(m, snap, card_top)
    if card_bot > BODY_BOT:
        raise SystemExit(
            f"console card content reaches {card_bot}, body ends {BODY_BOT} — "
            f"refusing to crop the cited reports")

    f.panel((MARGIN_X, card_top, W - MARGIN_X, card_bot), radius=16,
            left_edge=LEVEL_EDGE.get(hero["risk_level"], SEV_EDGE_LOW), edge_w=5)
    console_card(f, snap, card_top)


def scene_console(img, p, S):
    """One uninterrupted reveal, v1-style: the console page, then a hold.

    All five cited reports are drawn on the card itself (see
    ``console_base_body``), so the count-parity caption lands on the list it
    describes instead of on a second layout reached by a cut.
    """
    snap = S["snapshot"]
    grid = snap["grid"]
    hero = snap["hero_la_wildfire"]

    console_base_body(img, p, snap)
    return Captions([
        (0.0, f"One render of /risk returns the whole grid: {grid['card_count']} "
              "cards, every one computed in code."),
        (0.40, f"Los Angeles — wildfire {hero['risk_level']} {hero['risk_score']}: "
               f"{hero['evidence_count']} city-specific reports in seven days, "
               "plus a high-wind driver."),
        (0.68, f"The card counts {hero['source_count']} sources — every one of "
               "them cited below it. Same number."),
        (0.86, "Count the cited reports on the card: the driver's report count "
               "and the rendered sources are one list, not two claims."),
    ])


def integrity_card(f, snap, card, x0, y0, w, score_size=34, footer=None):
    """One evidence-gate card, laid out top-down; returns its bottom edge.

    v1's proportion — the card is only as tall as what it says — in v2's skin:
    severity left edge, chips for the anatomy, mono telemetry, Inter for prose.
    Type sizes are v1's, not v2's page-scale shrink. ``footer`` is an optional
    ``(label, prose)`` block owned by this card (the empty card's "why this
    matters"), so the explanation sits with the card it explains.
    """
    pad = 30
    sev = LEVEL_COLOR.get(card["risk_level"], SEV_LOW)

    hy = y0 + 22
    f.text((x0 + pad, hy), card["city"], 44, INK, 650)
    cx = x0 + pad + int(ui(44, 650).getlength(card["city"])) + 22
    cw, _ = f.sev_chip((0, 0), card["risk_level"], size=19, draw=False)
    f.sev_chip((cx, hy + 14), card["risk_level"], 19)
    f.text((cx + cw + 18, hy + 8), str(card["risk_score"]), score_size, sev,
           telemetry=True, mono_bold=True)
    f.text((cx + cw + 18, hy + 52), "/100", 16, INK_FAINT, telemetry=True)

    y = hy + 74
    tx = x0 + pad
    tw, _ = f.chip((tx, y), hazard_of(card), INK_DIM, border=LINE, size=17)
    tx += tw + 8
    tw, _ = f.chip((tx, y), n_sources(card["source_count"]), INK_FAINT,
                    border=LINE, size=17)
    tx += tw + 8
    f.chip((tx, y), f"confidence {card['confidence']*100:.0f}%", INK_FAINT,
           border=LINE, size=17)
    y += 40

    for ln in wrap(card["evidence_line"], ui(22), w - 2 * pad)[:2]:
        f.text((x0 + pad, y), ln, 22, INK_DIM)
        y += 30
    y += 6

    if card["drivers"]:
        f.hline(x0 + pad, x0 + w - pad, y)
        y += 14
        f.text((x0 + pad, y), f"CONTRIBUTING SIGNALS ({len(card['drivers'])})",
               15, INK_FAINT, telemetry=True)
        y += 28
        for i, drv in enumerate(card["drivers"]):
            f.text((x0 + pad, y), str(drv["kind"]).upper(), 15, INK_FAINT,
                   telemetry=True)
            f.rect((x0 + pad + 110, y + 5, x0 + pad + 270, y + 13), SURFACE3)
            f.rect((x0 + pad + 110, y + 5,
                    x0 + pad + 110 + int(160 * max(0.18, 1 - i * 0.17)),
                    y + 13), sev)
            f.text((x0 + pad + 290, y),
                   trunc(drv["text"], ui(19), w - pad - 290), 19, INK_MID)
            y += 34
        y += 4

    if card["summary"]:
        f.chip((x0 + pad, y), "AI", ACCENT, bg=mix(SURFACE2, ACCENT, 0.12),
               border=mix(SURFACE2, ACCENT, 0.40), size=15, padx=8, pady=2)
        bx = x0 + pad + 56
        bw = w - (bx - x0) - pad
        for ln in wrap_clamped(card["summary"], ui(19), bw, 3):
            f.text((bx, y), ln, 19, INK_DIM)
            y += 28
        y += 8

    if card["recommendation"]:
        aw_, _ = f.chip((x0 + pad, y), "ACTION", SEV_HIGH,
                        bg=mix(SURFACE2, SEV_HIGH, 0.12),
                        border=mix(SURFACE2, SEV_HIGH, 0.12), size=15, padx=8,
                        pady=2)
        bx = x0 + pad + aw_ + 16
        bw = w - (bx - x0) - pad
        for ln in wrap_clamped(card["recommendation"], ui(19), bw, 2):
            f.text((bx, y), ln, 19, INK_DIM)
            y += 28
        y += 12

    f.hline(x0 + pad, x0 + w - pad, y)
    y += 14
    f.text((x0 + pad, y), f"CITED SOURCES ({card['source_count']})", 15,
           INK_FAINT, telemetry=True)
    y += 30
    if card["sources"]:
        for src in card["sources"]:
            f.text((x0 + pad, y), trunc(src["title"], ui(20), w - 2 * pad - 20),
                   20, INK)
            y += 27
            f.text((x0 + pad + 20, y),
                   f"{src['outlet']} · {src['published']}", 16, INK_FAINT,
                   telemetry=True)
            y += 27
    else:
        f.text((x0 + pad, y), f"{card['source_count']} — none for this city",
               20, INK_MID, telemetry=True)
        y += 30
        f.text((x0 + pad, y), "no fabricated citation", 19, ACCENT)
        y += 30

    rec = receipt_of(snap, card["city"])
    if rec:
        y += 4
        f.hline(x0 + pad, x0 + w - pad, y)
        y += 14
        f.text((x0 + pad, y), "receipt", 15, INK_FAINT, telemetry=True)
        f.text((x0 + pad + 86, y), rec["receipt_id"], 16, INK_DIM,
               telemetry=True)
        f.text((x0 + w - pad, y), f"status {rec['status'].upper()}", 15,
               SEV_MODERATE, telemetry=True, anchor="ra")
        y += 28
        f.text((x0 + pad, y), rec["content_hash"], 15, INK_FAINT,
               telemetry=True)
        y += 22

    if footer:
        label, prose = footer
        f.hline(x0 + pad, x0 + w - pad, y)
        y += 14
        f.text((x0 + pad, y), label, 15, INK_FAINT, telemetry=True)
        y += 26
        for ln in wrap(prose, ui(19), w - 2 * pad):
            f.text((x0 + pad, y), ln, 19, INK_DIM)
            y += 27

    return y + pad


def scene_integrity(img, p, S):
    snap = S["snapshot"]
    lo = snap["london_dengue"]
    empty = snap["empty_bio"]

    y = BODY_TOP
    f = Frame(img, p)
    y += f.text((MARGIN_X, y), "THE EVIDENCE GATE", 38, INK, 650) + 14
    f.text((MARGIN_X, y),
           "a card may only cite reports for its own city and its own disease",
           24, INK_DIM)

    card_y = BODY_TOP + 86
    lw = 1010
    rx = MARGIN_X + lw + 24
    rw = W - MARGIN_X - rx

    note = ("Another disease's outbreak is never this card's evidence. No "
            "evidence in the window stays an honest low instead of a "
            "manufactured alert.")

    # Size each panel to its own content, the way v1 did: measure once, then
    # paint. No card carries a dead band under its last drawn line.
    m = Measure()
    london_bot = integrity_card(m, snap, lo, MARGIN_X, card_y, lw)
    empty_bot = integrity_card(m, snap, empty, rx, card_y, rw,
                               footer=("WHY THIS MATTERS", note))

    if max(london_bot, empty_bot) > BODY_BOT:
        raise SystemExit(
            f"evidence gate reaches {max(london_bot, empty_bot)}, body ends "
            f"{BODY_BOT} — refusing to crop a card")

    f.panel((MARGIN_X, card_y, MARGIN_X + lw, london_bot), radius=16,
            left_edge=LEVEL_EDGE.get(lo["risk_level"], SEV_EDGE_LOW), edge_w=5)
    integrity_card(f, snap, lo, MARGIN_X, card_y, lw)

    f.panel((rx, card_y, W - MARGIN_X, empty_bot), radius=16,
            left_edge=LEVEL_EDGE.get(empty["risk_level"], SEV_EDGE_LOW),
            edge_w=5)
    integrity_card(f, snap, empty, rx, card_y, rw,
                   footer=("WHY THIS MATTERS", note))

    # v1's payoff, stated under the card instead of parked in a dead band
    py = london_bot + 28
    f.text((MARGIN_X, py),
           "The one cited story is a local vector report — not another "
           "disease's outbreak.", 26, ACCENT)
    py += 40
    f.text((MARGIN_X, py),
           f"No city-specific evidence stays honest: e.g. {empty['city']} "
           f"{empty['risk_level']} {empty['risk_score']} with "
           f"{n_sources(empty['source_count'])}.", 23, INK_DIM)

    return Captions([
        (0.0, "The differentiator is the evidence gate."),
        (0.38, f"London dengue {lo['risk_level']} {lo['risk_score']} cites "
               "exactly one story — a local vector report, nothing else."),
        (0.72, "Another disease's outbreak is never this card's evidence. No "
               "evidence means an honest low, not a fabricated one."),
    ])


def scene_resilience(img, p, S):
    snap = S["snapshot"]
    live = snap["debug_weather"]
    fb = snap["weather_forces_fallback"]
    f = Frame(img, p)

    y = BODY_TOP
    y += f.text((MARGIN_X, y), "GRACEFUL DEGRADATION", 38, INK, 650) + 12
    f.text((MARGIN_X, y),
           "the weather grid survives a provider outage instead of blanking "
           "the cards", 24, INK_DIM)

    top = BODY_TOP + 88
    ph = 424
    lw = 812
    f.panel((MARGIN_X, top, MARGIN_X + lw, top + ph), radius=16,
            top_edge=ACCENT, edge_w=4)
    f.text((MARGIN_X + 26, top + 22), "GET /debug/weather — live today",
           16, ACCENT, telemetry=True)
    ok_chip = f"{live['ok']} / {live['attempted_cities']} ok"
    cw_, _ = f.chip((0, 0), ok_chip, ACCENT, size=15, padx=10, pady=3,
                     draw=False)
    f.chip((MARGIN_X + lw - 26 - cw_, top + 16), ok_chip, ACCENT,
           bg=mix(SURFACE1, ACCENT, 0.12), border=mix(SURFACE1, ACCENT, 0.40),
           size=15, padx=10, pady=3)
    providers = sorted({c["provider"] for c in live["cities"] if c.get("provider")})
    rail_rows(f, MARGIN_X + 26, top + 64, lw - 52, [
        ("configured cities", str(live["configured_cities"]), INK),
        ("attempted cities", str(live["attempted_cities"]), INK),
        ("ok", str(live["ok"]), ACCENT),
        ("failed", str(live["failed"]), INK),
        ("provider", ", ".join(providers), INK_MID),
        ("cache", f"{live['cache']['cities']} cities served "
                  f"({live['cache']['age_s']}s old)", INK),
        ("generated", live["generated_at"], INK_FAINT),
    ], row_h=48)

    rx = MARGIN_X + lw + 24
    rw = W - MARGIN_X - rx
    f.panel((rx, top, rx + rw, top + ph), radius=14, top_edge=SEV_MODERATE,
            edge_w=4)
    f.text((rx + 26, top + 22), "FALLBACK PATH — PRIMARY 429", 16, SEV_MODERATE,
           telemetry=True)
    f.chip((rx + rw - 26 - 122, top + 16), "met-norway", SEV_MODERATE,
           bg=mix(SURFACE1, SEV_MODERATE, 0.12),
           border=mix(SURFACE1, SEV_MODERATE, 0.12), size=15, padx=10, pady=3)
    fy = top + 62
    f.text((rx + 26, fy), "replayed condition", 15, INK_FAINT, telemetry=True)
    fy += 22
    for ln in wrap_clamped(fb["condition_replayed"], mono(16), rw - 52, 2):
        f.text((rx + 26, fy), ln, 16, INK_DIM, telemetry=True)
        fy += 22
    fy += 10
    days = sorted({c["forecast_days"] for c in fb["cities"]})
    rail_rows(f, rx + 26, fy, rw - 52, [
        ("cities attempted", str(fb["attempted_cities"]), INK),
        ("served ok", f"{fb['ok']}/{fb['attempted_cities']}", ACCENT),
        ("failed", str(fb["failed"]), INK),
        ("served by", ", ".join(fb["served_by"]), INK_MID),
        ("forecast days / city", ", ".join(str(d) for d in days), INK),
        ("configured cities", str(fb["configured_cities"]), INK),
    ], row_h=46)

    note_y = top + ph + 18
    f.text((MARGIN_X, note_y),
           "Primary hard-fails with a daily-quota 429 — the same code path "
           "serves real forecasts from an independent provider.",
           22, INK_MID)

    return Captions([
        (0.0, "Resilience: weather is three providers deep."),
        (0.36, f"Today the live grid is served cleanly — /debug/weather shows "
               f"{live['ok']} of {live['attempted_cities']} cities answered."),
        (0.70, "When the primary returns a daily-quota 429, the same code path "
               "serves real MET Norway forecasts instead of blanking the card."),
    ])


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


_PLATE: dict[str, Image.Image] = {}


def money_evidence_plate(snap):
    """The dense evidence block laid out at ``ZOOM_MAX`` inside ZOOM_BOX.

    This plate is the widest framing the camera ever reaches, so it doubles as
    the fit check. Type sizes are fixed at ``ZOOM_MAX`` — the "1.5x" label is
    literal — and only the whitespace between blocks is compressed if the
    natural layout is taller than the box. If the text alone cannot fit, the
    build fails instead of drawing a clipped column.
    """
    st = snap["telegraph_status"]
    sett = st["last_settlement"]
    s = sett["settlement"]
    rec = snap["receipts"]
    chain = snap["onchain_settlement"]

    x0, y0, x1, y1 = ZOOM_BOX
    bw, bh = x1 - x0, y1 - y0
    img = Image.new("RGB", (bw, bh), BG)
    d = ImageDraw.Draw(img)

    k = ZOOM_MAX
    sz = lambda v: int(round(v * k))
    pad = sz(26)
    inner = bw - 2 * pad
    lh = lambda size: int(round(size * 1.34))
    indent = sz(24)

    label = "LAST SETTLEMENT — SEEDED FROM THE LEDGER"
    tx_lines = wrap(sett["tx_hash"], mono(sz(23)), inner)
    rail_lines = wrap_sep(
        f"rail {s['rail']} · mocked {s['mocked']} · {sett['amount_usd']} USDC · "
        f"{sett['amount_uusdc']} µUSDC · {sett['time_pkt']}", mono(sz(22)), inner)
    chain_lines = wrap_sep(
        f"on-chain receipt: status {chain['status']} · block "
        f"{chain['block_number']} · to {chain['to']}", mono(sz(20)), inner)
    head = f"RECEIPTS — {rec['count']} filed from HIGH/CRITICAL cards"
    rows = []
    for r in rec["receipts"]:
        row = (f"{r['receipt_id']} · {r['city']} · {r['risk_level']} "
               f"{r['score']} · {r['status']} · {r['drivers'][0]}")
        rows.append((wrap_sep(row, ui(sz(21)), inner - indent), sz(21),
                     wrap(r["content_hash"], mono(sz(16)), inner - indent),
                     sz(16), LEVEL_COLOR.get(r["risk_level"], SEV_LOW)))

    panel_pad = sz(18)
    panel_tail = sz(30)
    gaps = sz(12) + sz(10) + sz(12) + sz(18)
    text_h = (lh(sz(18)) + len(tx_lines) * lh(sz(23))
              + len(rail_lines) * lh(sz(22)) + len(chain_lines) * lh(sz(20))
              + lh(sz(20)) + sum(len(a) * lh(s1) + len(b) * lh(s2)
                                 for a, s1, b, s2, _ in rows))
    fixed_h = sz(16) + panel_pad + sz(20) + panel_tail
    budget = bh - text_h - fixed_h
    if budget < 0:
        raise SystemExit(
            f"evidence text alone is {text_h}px, box {bh}px — cannot fit at "
            f"{ZOOM_MAX}x without shrinking type; refusing to crop")
    gap_scale = min(1.0, budget / gaps) if gaps else 1.0
    g = lambda v: int(round(v * gap_scale))

    panel_h = (panel_pad + lh(sz(18)) + g(12) + len(tx_lines) * lh(sz(23)) + g(10)
               + len(rail_lines) * lh(sz(22)) + g(12)
               + len(chain_lines) * lh(sz(20)) + sz(20))

    panel_top = sz(16)
    d.rounded_rectangle([(1, panel_top), (bw - 2, panel_top + panel_h)],
                        radius=sz(14), outline=ACCENT, fill=SURFACE1, width=2)
    d.line([(sz(14), panel_top + 2), (bw - sz(14), panel_top + 2)],
           fill=ACCENT, width=sz(4))
    y = panel_top + panel_pad

    def block(lines, size, colour, ind=0, gap=0, fnt=None):
        nonlocal y
        fnt = fnt or ui(size)
        for ln in lines:
            d.text((pad + ind, y), ln, font=fnt, fill=colour)
            y += lh(size)
        y += gap

    d.text((pad, y), label, font=mono(sz(18)), fill=ACCENT)
    y += lh(sz(18)) + g(12)
    block(tx_lines, sz(23), INK, 0, g(10), mono(sz(23)))
    block(rail_lines, sz(22), INK_DIM, 0, g(12), mono(sz(22)))
    block(chain_lines, sz(20), INK_FAINT, 0, 0, mono(sz(20)))

    y = panel_top + panel_h + sz(20)
    d.text((pad, y), head, font=mono(sz(20)), fill=INK_MID)
    y += lh(sz(20)) + g(18)
    for i, (row_lines, row_size, hash_lines, hash_size, sev) in enumerate(rows):
        d.line([(pad, y + 2),
                (pad, y + lh(row_size) * max(1, len(row_lines)) + sz(8))],
               fill=sev, width=sz(5))
        d.line([(pad + sz(18), y + 2), (bw - pad, y + 2)], fill=LINE, width=1)
        for ln in row_lines:
            d.text((pad + indent, y), ln, font=ui(row_size), fill=INK)
            y += lh(row_size)
        y += g(6) if i < len(rows) - 1 else g(10)
        for ln in hash_lines:
            d.text((pad + indent, y), ln, font=mono(hash_size), fill=INK_FAINT)
            y += lh(hash_size)
        y += g(18)

    if y > bh:
        raise SystemExit(
            f"evidence plate bottom {y} exceeds box {bh} — refusing to crop")
    return img


def money_detail_frame(img, snap, elapsed):
    """Ease from the whole fitted panel to the 1:1 (1.5x) layout, then hold.

    A fitting plate is only ever scaled down and back up to 1:1, so no column,
    edge or glyph can leave the frame at any instant of the push-in.
    """
    plate = _PLATE.get("img")
    if plate is None:
        plate = _PLATE["img"] = money_evidence_plate(snap)
    x0, y0, x1, y1 = ZOOM_BOX
    start = 1.0 / ZOOM_MAX
    f = start + (1.0 - start) * ease(elapsed / ZOOM_RAMP_S)
    if f >= 0.999:
        img.paste(plate, (x0, y0))
        return
    w, h = int(round(plate.width * f)), int(round(plate.height * f))
    img.paste(plate.resize((w, h), Image.LANCZOS),
              (x0 + ((x1 - x0) - w) // 2, y0 + ((y1 - y0) - h) // 2))


def money_base_body(img, p, snap):
    """The wide money layout, exactly as it reads before the push-in."""
    st = snap["telegraph_status"]
    stats = snap["telegraph_stats"]
    rec = snap["receipts"]
    chain = snap["onchain_settlement"]
    sett = st["last_settlement"]
    s = sett["settlement"]

    f = Frame(img, p)
    y = BODY_TOP
    y += f.text((MARGIN_X, y), "ON-CHAIN SETTLEMENT", 34, INK, 650) + 10
    f.text((MARGIN_X, y),
           f"x402 · {st['network_label']} · a paid assessment, read back from "
           f"the chain", 21, INK_DIM)

    top = BODY_TOP + 88
    lw = 780
    ph = 452
    f.panel((MARGIN_X, top, MARGIN_X + lw, top + ph), radius=16, top_edge=ACCENT,
            edge_w=4)
    f.text((MARGIN_X + 26, top + 22), "LAST SETTLEMENT", 15, ACCENT,
           telemetry=True)
    f.chip((MARGIN_X + lw - 26 - 186, top + 16), "live settlement proven",
           ACCENT, bg=mix(SURFACE1, ACCENT, 0.12),
           border=mix(SURFACE1, ACCENT, 0.40), size=14, padx=10, pady=3)
    ty = top + 58
    f.text((MARGIN_X + 26, ty), "tx hash", 14, INK_FAINT, telemetry=True)
    ty += 22
    for ln in wrap(sett["tx_hash"], mono(17), lw - 52):
        f.text((MARGIN_X + 26, ty), ln, 17, INK, telemetry=True)
        ty += 22
    ty += 10
    for ln in wrap_sep(
            f"rail {s['rail']} · mocked {s['mocked']} · {sett['amount_usd']} "
            f"USDC · {sett['amount_uusdc']} µUSDC · {sett['time_pkt']}",
            mono(17), lw - 52):
        f.text((MARGIN_X + 26, ty), ln, 17, INK_DIM, telemetry=True)
        ty += 22
    ty += 10
    f.hline(MARGIN_X + 26, MARGIN_X + lw - 26, ty)
    ty += 16
    rail_rows(f, MARGIN_X + 26, ty, lw - 52, [
        ("status", chain["status"], ACCENT),
        ("block", str(chain["block_number"]), INK),
        ("to (USDC)", chain["to"], INK_MID),
        ("from", chain["from"], INK_MID),
        ("logs", str(chain["log_count"]), INK),
        ("rpc", chain["rpc_url"], INK_FAINT),
    ], row_h=42)

    # receipts panel
    rx = MARGIN_X + lw + 24
    rw = W - MARGIN_X - rx
    f.panel((rx, top, rx + rw, top + ph), radius=14)
    f.text((rx + 26, top + 20),
           f"RECEIPTS — {rec['count']} filed from HIGH/CRITICAL cards", 15,
           INK_MID, 650)
    f.text((rx + rw - 26, top + 20),
           f"{snap['scoreboard']['resolved']} resolved", 15, INK_FAINT,
           telemetry=True, anchor="ra")
    ry = top + 56
    for r in rec["receipts"]:
        rh = 182
        f.panel((rx + 20, ry, rx + rw - 20, ry + rh), radius=10,
                left_edge=LEVEL_EDGE.get(r["risk_level"], SEV_EDGE_LOW),
                edge_w=5, fill=SURFACE2)
        f.text((rx + 46, ry + 18), r["receipt_id"], 18, INK, telemetry=True,
               mono_bold=True)
        f.text((rx + rw - 46, ry + 20), "OPEN", 15, SEV_MODERATE,
               telemetry=True, anchor="ra")
        f.text((rx + 46, ry + 46), r["city"], 24, INK, 650)
        f.text((rx + 46, ry + 78), trunc(r["drivers"][0], ui(17), rw - 220),
               17, INK_DIM)
        cw, _ = f.sev_chip((0, 0), r["risk_level"], size=14, draw=False)
        f.sev_chip((rx + rw - 46 - cw, ry + 72), r["risk_level"], 14)
        f.text((rx + rw - 46 - cw - 18, ry + 66), f"{r['score']}/100", 20,
               LEVEL_COLOR.get(r["risk_level"], SEV_LOW), telemetry=True,
               mono_bold=True, anchor="ra")
        f.text((rx + 46, ry + 110), "content hash", 13, INK_FAINT,
               telemetry=True)
        f.text((rx + 46, ry + 128), trunc(r["content_hash"], mono(14), rw - 92),
               14, INK_FAINT, telemetry=True)
        ry += rh + 14

    # ledger strip — sized to its own content, not stretched to the body floor
    sy = top + ph + 20
    sy_bot = sy + 96
    f.panel((MARGIN_X, sy, W - MARGIN_X, sy_bot), radius=14)
    pad = 26
    verdicts = ", ".join(f"{k} {v}" for k, v in stats["verdicts"].items() if v)
    cols = [
        ("assessments", str(stats["assessments"]), INK, True),
        ("settled", str(stats["settled"]), ACCENT, True),
        ("total", f"{stats['total_usdc']} USDC", INK, True),
        ("integrity", f"{stats['integrity_pct']:g}%", ACCENT, True),
        ("verdicts", verdicts or "none", INK_MID, False),
        ("ledger", "sha256, append-only", INK_MID, False),
    ]
    cw_ = (W - 2 * MARGIN_X - 2 * pad) // len(cols)
    for i, (k, v, col, tel) in enumerate(cols):
        cx = MARGIN_X + pad + i * cw_
        if i:
            f.line([(cx - 16, sy + 14), (cx - 16, sy_bot - 14)], LINE, 1)
        f.text((cx, sy + 16), k, 14, INK_FAINT, telemetry=True)
        if tel:
            f.text((cx, sy + 38), v, 22, col, telemetry=True, mono_bold=True)
        else:
            f.text((cx, sy + 40), trunc(v, ui(18, 600), cw_ - 24), 18, col, 600)


def scene_money(img, p, S):
    snap = S["snapshot"]
    st = snap["telegraph_status"]
    chain = snap["onchain_settlement"]
    sett = st["last_settlement"]
    s = sett["settlement"]

    zoom_start = 1.0 - ZOOM_TOTAL_S / S["dur"]
    subs = [
        (0.0, "The money is first-class data, not a claim."),
        (0.34, f"Mode {st['mode']} on {st['network_label']}: a real "
               f"transaction, mocked {s['mocked']}."),
        (0.62, f"Read back from the chain: status {chain['status']}, block "
               f"{chain['block_number']}, to the USDC contract."),
        (0.82, "Every paid assessment is notarized, and every HIGH card that "
               "finalizes files a receipt."),
        (zoom_start, "Full transaction hash and both receipts — fitted to the "
                     "frame, never cropped."),
    ]
    # The counting pass measures the base layout's draw count, so reveal pacing
    # still matches what a viewer sees before the push-in.
    if Frame._counting or p < zoom_start:
        money_base_body(img, p, snap)
        return Captions(subs)

    # Cut to the detail view, then push: the plate starts at its whole-panel
    # fit (every line whole and inside the frame) and eases to 1:1, which is
    # the 1.5x layout. Blending the base over the plate would double-expose two
    # different layouts, so this is a cut followed by the move itself.
    money_detail_frame(img, snap, (p - zoom_start) * S["dur"])
    ImageDraw.Draw(img).text(
        (MARGIN_X, 124), "settlement detail — full ledger record",
        font=mono(19), fill=ACCENT)
    return Captions(subs)


def scene_close(img, p, S):
    snap = S["snapshot"]
    grid = snap["grid"]
    f = Frame(img, p)
    y = BODY_TOP + 40
    y += f.text((MARGIN_X, y), "Outbreak Sentinel", 72, INK, 650) + 26
    y += f.text((MARGIN_X, y), snap["live_base"], 32, ACCENT, 500) + 30
    y += f.text((MARGIN_X, y), "Track 01 — Apps & Agents", 26, INK_MID) + 12
    y += f.text((MARGIN_X, y),
                "Mission 06 — Resources & Agriculture (fire-risk signal stack)",
                21, INK_DIM) + 8
    y += f.text((MARGIN_X, y),
                "Mission 11 — Autonomous Systems (an autonomous unit buying "
                "fire-risk)", 21, INK_DIM) + 30
    y += f.text((MARGIN_X, y),
                "Surveillance only — never diagnosis, never treatment advice.",
                24, SEV_HIGH) + 20
    f.text((MARGIN_X, y),
           f"{grid['card_count']} live cards across {grid['city_count']} "
           f"cities; every claim traceable to a source; receipt ledger "
           f"append-only.", 21, INK_DIM)

    # closing readings, console instrument style
    instruments(f, snap, MARGIN_X, W - MARGIN_X, BODY_BOT - 100, 100)
    return Captions([
        (0.0, "Outbreak Sentinel — cited early-warning intelligence, bought "
              "and settled on-chain."),
        (0.5, "Everything shown came from the live deployment. The URL is open "
              "— try it."),
    ])


SCENES = [
    ("cold open", 20.0, scene_cold_open),
    ("the live console", 56.0, scene_console),
    ("the evidence gate", 44.0, scene_integrity),
    ("graceful degradation", 36.0, scene_resilience),
    ("the money story", 56.0, scene_money),
    ("close", 20.0, scene_close),
]


def measure(snap):
    """One counting pass per scene so reveal pacing matches draw count exactly."""
    Frame._counting = True
    for i, (_label, dur, fn) in enumerate(SCENES):
        _CURRENT["i"] = i
        Frame._count = 0
        fn(Image.new("RGB", (W, H), BG), 1.0, {"snapshot": snap, "dur": dur})
        _SCENE_N[i] = Frame._count
    Frame._counting = False
    return _SCENE_N


def render_frame(snap, scene_idx, p, overall_p):
    label, dur, fn = SCENES[scene_idx]
    _CURRENT["i"] = scene_idx
    img = Image.new("RGB", (W, H), BG)
    captions = fn(img, p, {"snapshot": snap, "dur": dur})
    chrome(img, snap, label, overall_p, scene_idx)
    captions.draw(img, p)
    return img


# Submission-form stills: each point lands where its scene's claim is fully
# made, and scene 5 lands inside the 1.5x evidence hold.
STILLS = [
    ("01-title", 0, 0.55),
    ("02-console-grid", 1, 0.55),
    ("03-la-card", 1, 0.97),
    ("04-evidence-gate", 2, 0.97),
    ("05-weather-resilience", 3, 0.97),
    ("06-money-story", 4, 0.97),
]


def build_stills(snap, out_dir):
    """Six full-resolution PNGs through the same render path the video uses."""
    measure(snap)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name, si, p in STILLS:
        path = out / f"{name}.png"
        render_frame(snap, si, p, 0.5).save(path, "PNG")
        print(f"wrote {path} ({path.stat().st_size} bytes)")
    return out


def build_video(snap):
    counts = measure(snap)
    total_frames = sum(int(d * FPS) for _, d, _ in SCENES)
    print(f"reveal counts: {counts}")
    print(f"rendering {total_frames} frames "
          f"({sum(d for _, d, _ in SCENES):.0f}s @ {FPS}fps) -> {OUT_VIDEO}")
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
        "-i", "-",
        "-an",  # caption-driven cut: no audio stream, no licensed music
        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
        "-movflags", "+faststart", str(OUT_VIDEO),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    done = 0
    try:
        for si, (_label, dur, _fn) in enumerate(SCENES):
            n = int(dur * FPS)
            for i in range(n):
                p = i / max(1, n - 1)
                overall = (done + i) / max(1, total_frames - 1)
                proc.stdin.write(render_frame(snap, si, p, overall).tobytes())
                done += 1
            print(f"  scene {si + 1}/{len(SCENES)} done ({done}/{total_frames})")
    finally:
        proc.stdin.close()
        proc.wait()
    if proc.returncode != 0:
        raise SystemExit(f"ffmpeg failed with {proc.returncode}")
    print(f"wrote {OUT_VIDEO} ({OUT_VIDEO.stat().st_size} bytes)")
    return OUT_VIDEO


def build_montage(snap, out_path):
    """Six representative frames into one contact sheet, for human review.

    One frame per scene, no scene twice: with scene 2 now a single uninterrupted
    reveal there is no second layout to show, and a sheet that repeats the same
    page at two reveal stages reads as a duplicate frame. The money slot lands
    inside the 1.5x hold, which is the cut's one move.
    """
    measure(snap)
    picks = [(0, 0.95), (1, 0.95), (2, 0.95), (3, 0.95), (4, 0.99), (5, 0.95)]
    thumbs = []
    for si, p in picks:
        thumbs.append(render_frame(snap, si, p, 0.5).resize((640, 360),
                                                           Image.LANCZOS))
    sheet = Image.new("RGB", (640 * 2, 360 * 3), BG)
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % 2) * 640, (i // 2) * 360))
    sheet.save(out_path)
    print(f"wrote montage {out_path} ({len(picks)} frames)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--montage",
                    help="write a 6-frame contact sheet instead of the video")
    ap.add_argument("--stills", metavar="DIR",
                    help="write the 6 submission PNGs at 1920x1080 instead of "
                         "the video")
    args = ap.parse_args()
    for path, what in ((FONT_UI, "Inter (OFL) from demo/assets/fonts"),
                       (OFL, "OFL license text"),
                       (MONO, "DejaVu Sans Mono")):
        if not path.exists():
            raise SystemExit(f"missing {what}: {path}")
    if not SNAPSHOT.exists():
        raise SystemExit(f"missing {SNAPSHOT} — run demo/capture_video_data.py first")
    snap = json.loads(SNAPSHOT.read_text())
    if args.montage:
        build_montage(snap, args.montage)
    elif args.stills:
        build_stills(snap, args.stills)
    else:
        build_video(snap)
    return 0


if __name__ == "__main__":
    sys.exit(main())
