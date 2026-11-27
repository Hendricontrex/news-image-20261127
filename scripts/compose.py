#!/usr/bin/env python3
"""Draw the 27 November 2026 world-news broadsheet (1024x1024 PNG).

Own implementation: cream broadsheet, serif masthead, lead story, big-number
stat strip, 2x2 story grid, schematic world map, reported-date timeline,
source footer. All facts are the five verified stories of the day; no other
numbers appear. Output is deterministic: same input always writes the same
PNG bytes (Pillow writes no timestamps).
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
CREAM = (247, 241, 222)
INK = (24, 24, 24)
FAINT = (90, 84, 70)
RED = (143, 29, 24)
MAP_FILL = (214, 203, 175)
MAP_LINE = (120, 110, 88)
BAND = (238, 230, 204)

FONT_DIR = "/usr/share/fonts/truetype/noto"


class Fonts:
    """Small cache so each TTF is loaded once."""

    def __init__(self):
        self._cache = {}

    def get(self, name, size):
        key = (name, size)
        if key not in self._cache:
            self._cache[key] = ImageFont.truetype(
                os.path.join(FONT_DIR, name), size)
        return self._cache[key]

    def serif_black(self, size):
        return self.get("NotoSerif-Black.ttf", size)

    def serif_bold(self, size):
        return self.get("NotoSerif-Bold.ttf", size)

    def serif(self, size):
        return self.get("NotoSerif-Regular.ttf", size)

    def sans_bold(self, size):
        return self.get("NotoSans-Bold.ttf", size)

    def sans(self, size):
        return self.get("NotoSans-Regular.ttf", size)


F = Fonts()


def wrap(draw, text, font, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    lines, cur = [], ""
    for word in text.split():
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(draw, text, font, x, y, max_w, leading, fill=INK):
    """Draw a wrapped paragraph; return the y just below it."""
    for line in wrap(draw, text, font, max_w):
        draw.text((x, y), line, font=font, fill=fill)
        y += leading
    return y


def rule(draw, x0, y, x1, width=2, fill=INK):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


def centered(draw, text, font, cx, y, fill=INK):
    w = draw.textlength(text, font=font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


# ---------------------------------------------------------------- stories
LEAD = {
    "kicker": "KUWAIT  •  DRONE STRIKE",
    "head": ["DRONE STRIKE KILLS 2 ITALIANS", "AT KUWAIT AIR-DEFENCE STATION"],
    "body": ("Two Italian technicians, aged 36 and 65 and working for "
             "Rheinmetall Italia, were killed on Thursday when a drone "
             "struck a Kuwaiti air-defence detection station. Kuwait's "
             "defence ministry said several hostile drones were detected "
             "and engaged; falling shrapnel wounded two more people, a "
             "Kuwaiti national and a Pakistani national. Kuwait and Italy "
             "blame Iran. Iran denies any involvement."),
}

STATS = [
    ("2", "KILLED", "ITALIANS IN KUWAIT"),
    ("100,000", "RESERVISTS", "CALLED UP BY BRITAIN"),
    ("$49BN", "UKRAINE LOAN", "BLOCKED AT EU SUMMIT"),
    ("THOUSANDS", "PRISONERS", "IN PLANNED SWAP"),
    ("9", "INJURED", "IN BANGKOK BLAST"),
]

GRID = [
    {"kicker": "UNITED KINGDOM",
     "head": "BRITAIN CALLS UP 100,000 RESERVISTS",
     "body": ("The Ministry of Defence has written to about 100,000 "
              "strategic reservists — the first such call-up since the Cold "
              "War — asking them to update contact details and skills, and "
              "offering voluntary training including NATO's Steadfast "
              "Defender exercise next spring. Defence Secretary Wes "
              "Streeting called it a \u201cnecessary precaution\u201d amid the "
              "Russia threat. Last week Russia fired cruise missiles and a "
              "drone into eastern Poland.")},
    {"kicker": "EUROPEAN UNION  •  BRUSSELS",
     "head": "EU SUMMIT SPLITS ON $49BN UKRAINE LOAN",
     "body": ("EU leaders failed after more than 12 hours of talks in "
              "Brussels to agree the 2028–2034 long-term budget, set at "
              "1–1.2% of GNI, and a new 45 billion euro ($49 billion) loan "
              "for Ukraine — 20 billion euros for the economy and 25 "
              "billion for the armed forces. Leaders will try again on "
              "17–18 December; President Macron set an end-of-year "
              "deadline.")},
    {"kicker": "RUSSIA  •  UKRAINE",
     "head": "KUSHNER: BIGGEST PRISONER SWAP BEFORE CHRISTMAS",
     "body": ("US envoy Jared Kushner said Russia and Ukraine will carry "
              "out the largest prisoner exchange of the war before the "
              "holidays, with \u201cthousands\u201d returning home, the first "
              "stage possibly in late November or early December. Formats "
              "discussed are 1,000-for-1,000 or 1,500-for-1,500. The last "
              "big exchange, on 23 October, returned 270 Ukrainians.")},    {"kicker": "THAILAND  •  BANGKOK",
     "head": "BANGKOK REFINERY BLAST INJURES 9",
     "body": ("An explosion and fire at Bangchak's Phra Khanong refinery in "
              "Bangkok on Thursday at about 14:45 local time injured at "
              "least nine people, three of them critically with burns. The "
              "fire was out within an hour and all production was halted. "
              "Residents within 5 km were warned of air pollution. The "
              "refinery's capacity is 120,000 barrels a day.")},
]

# Rough continent outlines (lon, lat) — schematic only, for the map strip.
CONTINENTS = [
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 80), (-85, 70),
     (-75, 62), (-60, 55), (-55, 47), (-70, 42), (-75, 35), (-80, 26),
     (-90, 21), (-97, 16), (-105, 20), (-115, 28), (-125, 40), (-125, 48),
     (-140, 60), (-155, 58), (-165, 60)],
    [(-80, 10), (-75, 5), (-60, 0), (-50, -5), (-35, -8), (-40, -20),
     (-48, -28), (-58, -35), (-65, -45), (-70, -54), (-73, -40), (-73, -25),
     (-80, -15), (-81, -5)],
    [(-17, 15), (-10, 30), (0, 35), (10, 37), (20, 32), (32, 31), (35, 28),
     (43, 12), (51, 11), (48, 0), (40, -10), (35, -20), (32, -28),
     (20, -35), (15, -27), (12, -18), (9, -1), (9, 4), (-8, 5)],
    [(-10, 36), (-9, 43), (-2, 48), (0, 51), (5, 53), (8, 57), (10, 59),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (40, 68), (55, 69),
     (70, 72), (90, 75), (110, 76), (130, 72), (150, 70), (170, 67),
     (178, 65), (170, 60), (162, 56), (158, 52), (142, 50), (140, 40),
     (135, 35), (130, 32), (122, 30), (120, 22), (110, 20), (105, 10),
     (100, 8), (98, 12), (95, 16), (90, 22), (85, 19), (80, 15), (75, 10),
     (72, 20), (66, 25), (60, 25), (57, 27), (52, 28), (50, 30), (48, 30),
     (44, 29), (40, 31), (36, 36), (30, 36), (27, 37), (23, 36), (19, 40),
     (15, 44), (12, 44), (8, 44), (3, 43), (0, 40), (-2, 37), (-6, 36)],
    [(113, -22), (114, -30), (115, -35), (124, -33), (130, -32), (137, -35),
     (140, -38), (145, -38), (150, -37), (153, -32), (153, -27), (150, -23),
     (146, -19), (142, -15), (142, -11), (137, -12), (135, -15), (132, -12),
     (130, -13), (126, -14), (122, -17), (118, -20)],
]

MARKERS = [
    # name, lon, lat, label dx, label dy (staggered so London/Brussels
    # do not collide at this scale)
    ("KUWAIT", 47.5, 29.4, 8, -7),
    ("LONDON", -0.1, 51.5, 8, -20),
    ("BRUSSELS", 4.4, 50.9, 8, 7),
    ("KYIV", 30.5, 50.5, 8, -7),
    ("BANGKOK", 100.5, 13.8, -9, -7),
]


def draw_map(draw, box):
    """Schematic world map with the five story locations marked."""
    x0, y0, x1, y1 = box
    lon0, lon1, lat0, lat1 = -180, 180, -35, 75

    def proj(lon, lat):
        return (x0 + (lon - lon0) / (lon1 - lon0) * (x1 - x0),
                y0 + (lat1 - lat) / (lat1 - lat0) * (y1 - y0))

    for poly in CONTINENTS:
        pts = [proj(lon, lat) for lon, lat in poly]
        draw.polygon(pts, fill=MAP_FILL, outline=MAP_LINE, width=1)
    lab_font = F.sans_bold(13)
    for name, lon, lat, dx, dy in MARKERS:
        px, py = proj(lon, lat)
        draw.ellipse([px - 4, py - 4, px + 4, py + 4], fill=RED,
                     outline=INK, width=1)
        tw = draw.textlength(name, font=lab_font)
        # Bangkok's label goes left of its dot; the rest go right.
        lx = px - tw + dx if name == "BANGKOK" else px + dx
        draw.text((lx, py + dy), name, font=lab_font, fill=INK)


def build():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    mx, rx = 30, W - 30  # page margins

    # ---- masthead ------------------------------------------------------
    rule(d, mx, 22, rx, 4)
    centered(d, "WORLD NEWS", F.serif_black(80), W // 2, 30)
    centered(d, "FRIDAY 27 NOVEMBER 2026", F.sans_bold(20), W // 2, 118)
    rule(d, mx, 146, rx, 2)
    rule(d, mx, 151, rx, 1)

    # ---- lead story ----------------------------------------------------
    y = 162
    d.text((mx, y), LEAD["kicker"], font=F.sans_bold(16), fill=RED)
    y += 24
    for line in LEAD["head"]:
        d.text((mx, y), line, font=F.serif_black(38), fill=INK)
        y += 44
    y += 6
    y = para(d, LEAD["body"], F.serif(18), mx, y, rx - mx, 23)
    rule(d, mx, y + 8, rx, 2)

    # ---- big-number stat strip -----------------------------------------
    sy = y + 18
    cell_w = (rx - mx) / len(STATS)
    d.rectangle([mx, sy, rx, sy + 66], fill=BAND, outline=INK, width=1)
    for i, (num, word, sub) in enumerate(STATS):
        cx = mx + cell_w * i + cell_w / 2
        if i:
            d.line([(mx + cell_w * i, sy + 7),
                    (mx + cell_w * i, sy + 59)], fill=FAINT, width=1)
        centered(d, num, F.serif_black(30), cx, sy + 3)
        centered(d, word, F.sans_bold(13), cx, sy + 36)
        centered(d, sub, F.sans(11), cx, sy + 50, fill=FAINT)
    gy = sy + 78

    # ---- 2x2 story grid -------------------------------------------------
    col_w = (rx - mx - 24) // 2
    row_h = 190
    for idx, story in enumerate(GRID):
        cx0 = mx + (idx % 2) * (col_w + 24)
        cy = gy + (idx // 2) * (row_h + 10)
        d.text((cx0, cy), story["kicker"], font=F.sans_bold(14), fill=RED)
        hy = cy + 20
        head_lines = wrap(d, story["head"], F.serif_bold(21), col_w)
        for line in head_lines:
            d.text((cx0, hy), line, font=F.serif_bold(21), fill=INK)
            hy += 26
        para(d, story["body"], F.serif(14), cx0, hy + 2, col_w, 18)
        if idx % 2 == 0:
            d.line([(cx0 + col_w + 12, cy),
                    (cx0 + col_w + 12, cy + row_h)], fill=FAINT, width=1)
    my = gy + 2 * row_h + 10

    # ---- map strip ------------------------------------------------------
    rule(d, mx, my, rx, 2)
    d.text((mx, my + 7), "THE DAY ON THE MAP",
           font=F.sans_bold(15), fill=RED)
    draw_map(d, (mx, my + 28, rx, my + 82))

    # ---- reported-date timeline -----------------------------------------
    ty = my + 88
    rule(d, mx, ty, rx, 1, fill=FAINT)
    d.text((mx, ty + 6), "REPORTED 25 NOV", font=F.sans_bold(13), fill=RED)
    d.text((mx + 148, ty + 6),
           "Kushner: biggest prisoner swap before Christmas",
           font=F.sans(13), fill=INK)
    d.text((mx, ty + 24), "REPORTED 26 NOV", font=F.sans_bold(13), fill=RED)
    d.text((mx + 148, ty + 24),
           "Kuwait strike  •  UK reservists  •  EU summit splits  •  "
           "Bangkok blast",
           font=F.sans(13), fill=INK)

    # ---- footer ---------------------------------------------------------
    fy = ty + 46
    rule(d, mx, fy, rx, 2)
    centered(d, "Sources: Reuters  •  BBC  •  CNN  •  Wall Street Journal"
                "  •  The Times  •  The Telegraph  •  Fox News  •  AP  •  "
                "Al Jazeera  •  MD MEETS  —  Built by an AI agent for "
                "make.fun",
             F.sans(11), W // 2, fy + 8, fill=FAINT)
    return img


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "entry.png"
    img = build()
    img.save(out, "PNG")
    print(f"wrote {out} {img.size[0]}x{img.size[1]} "
          f"{os.path.getsize(out)} bytes")


if __name__ == "__main__":
    main()
