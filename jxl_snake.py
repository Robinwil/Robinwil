#!/usr/bin/env python3
"""Build a tiny native JPEG XL artwork: a frontal viper head.

Authored at 256x256 and decoder-upsampled to 512x512. A zero-residual Modular
MA tree generates the silhouette and green-to-teal gradient. Native JXL splines
add two closed-loop eyes, nested scales, fangs, a forked tongue, face details,
and a compact chaotic background. No raster source exists.
"""

from pathlib import Path

S = 2
W = H = 256


def n(v: float) -> str:
    return "0" if not v else f"{v:.4g}"


def qpts(pts):
    return tuple((round(x / S), round(y / S)) for x, y in pts)


def spline(rgb, sigma, pts, harmonics=None, sigma_h=None):
    c = [[0.0] * 32 for _ in range(4)]
    c[0][0], c[1][0], c[2][0], c[3][0] = *rgb, sigma / S
    for i, v in (harmonics or {}).items():
        c[0][i], c[1][i], c[2][i] = v
    for i, v in (sigma_h or {}).items():
        c[3][i] = v / S
    coeff = " ".join(n(v) for ch in c for v in ch)
    points = " ".join(f"{x} {y}" for x, y in qpts(pts))
    return f"Spline {coeff} {points} EndSpline"


def chevrons(y, x0, x1, step=38, amp=9, phase=0):
    x = x0 + (step // 2 if phase else 0)
    pts = [(x, y)]
    while x + step <= x1:
        pts.extend(((x + step // 2, y + amp), (x + step, y)))
        x += step
    return tuple(pts)


def mirror(pts):
    return tuple((512 - x, y) for x, y in pts)


def leaf(value: int, indent="") -> str:
    return f"{indent}- Set - {abs(value)}" if value < 0 else f"{indent}- Set {value}"


def x_range(x0: int, x1: int, value: int, indent: str) -> str:
    x0, x1 = round(x0 / S), round(x1 / S)
    return "\n".join([
        f"{indent}if x > {x1}", leaf(0, indent + "  "),
        f"{indent}  if x > {x0}", leaf(value, indent + "    "),
        leaf(0, indent + "    "),
    ])


def band_tree(bands, i=0, indent="") -> str:
    if i == len(bands):
        return leaf(0, indent)
    y0, x0, x1, value = bands[i]
    y0 = round(y0 / S)
    branch = leaf(0, indent + "  ") if not value else x_range(x0, x1, value, indent + "  ")
    return "\n".join((f"{indent}if y > {y0}", branch, band_tree(bands, i + 1, indent + "  ")))


def head_bands():
    bands = [(388, 0, 0, 0)]
    for y in range(382, 165, -8):
        if y <= 250:
            half = 40 + (y - 166) * 165 / 84
        elif y <= 278:
            half = 205 - (y - 250) * 0.45
        else:
            half = 192 - (y - 278) * 1.48
        half = max(24, int(half))
        value = int(48 + 68 * max(0.0, 1.0 - abs(y - 252) / 126)) & ~3
        bands.append((y, 256 - half, 256 + half, value))
    return tuple(bands)


HEAD_BANDS = head_bands()
SCALE_ROWS = (
    (204, 158, 354, 0), (230, 108, 404, 1), (256, 78, 434, 0),
    (282, 92, 420, 1), (308, 124, 388, 0), (334, 170, 342, 1),
)

# One continuous outline replaces three separate rim splines.
RIM = (
    (180, 336), (116, 307), (72, 276), (61, 239), (105, 205),
    (169, 181), (214, 161), (256, 156), (298, 161), (343, 181),
    (407, 205), (451, 239), (440, 276), (396, 307), (332, 336),
)

# Three forehead diamonds connected by the central plate seam.
PLATES = (
    (256, 173), (225, 199), (256, 225), (287, 199), (256, 173),
    (256, 225), (229, 250), (256, 275), (283, 250), (256, 225),
    (256, 275), (237, 293), (256, 311), (275, 293), (256, 275),
)

LEFT_EYE = ((106, 237), (151, 207), (208, 229), (154, 257), (106, 237))
LEFT_PUPIL = ((157, 214), (157, 253))
LEFT_GLINT = ((147, 220), (153, 217))
LEFT_BROW = ((205, 216), (238, 200))
LEFT_PIT = ((211, 290), (219, 295))
LEFT_FANG = ((213, 340), (221, 372), (227, 396))

NOSE_RIDGE = ((256, 211), (256, 274), (256, 323))
LEFT_NOSTRIL = ((223, 318), (235, 314))
MOUTH = ((188, 345), (224, 355), (256, 359), (288, 355), (324, 345))
CHIN = ((221, 372), (256, 380), (291, 372))
TONGUE_A = ((256, 366), (255, 406), (240, 448))
TONGUE_B = ((255, 406), (274, 448))

BG_PATHS = (
    ((8, 76), (110, 30), (210, 86), (310, 34), (410, 80), (504, 30)),
    ((5, 130), (105, 100), (210, 144), (320, 96), (430, 132), (505, 84)),
    ((8, 430), (110, 386), (214, 436), (320, 388), (424, 432), (504, 428)),
    ((18, 482), (120, 446), (226, 488), (330, 444), (430, 484), (496, 476)),
    ((34, 22), (14, 140), (54, 260), (18, 380), (52, 502)),
    ((478, 20), (498, 140), (462, 260), (496, 380), (470, 502)),
)


def delta_green(indent):
    return "\n".join([
        f"{indent}if PrevAbs > 100", leaf(80, indent + "  "),
        f"{indent}  if PrevAbs > 70", leaf(60, indent + "    "),
        leaf(46, indent + "    "),
    ])


def delta_blue(indent):
    return "\n".join([
        f"{indent}if PrevAbs > 75", leaf(42, indent + "  "),
        f"{indent}  if PrevAbs > 55", leaf(16, indent + "    "),
        leaf(-4, indent + "    "),
    ])


def modular_tree() -> str:
    return "\n".join([
        "if c > 1", "  if PrevAbs > 0", delta_blue("    "), leaf(0, "    "),
        "  if c > 0", "    if PrevAbs > 0", delta_green("      "), leaf(0, "      "),
        band_tree(HEAD_BANDS, indent="    "),
    ])


def program() -> str:
    p = [
        f"Width {W}", f"Height {H}", "Bitdepth 8", "GroupShift 3",
        "Upsample 2", "RCT 0", "Gaborish",
        "Noise 0.04 0.08 0.13 0.18 0.13 0.08 0.04 0.02",
    ]

    bg_colours = (
        (0.08, 0.38, 0.52), (0.34, 0.08, 0.52), (0.04, 0.46, 0.28),
        (0.46, 0.10, 0.18), (0.08, 0.30, 0.48), (0.38, 0.06, 0.44),
    )
    for colour, path in zip(bg_colours, BG_PATHS):
        p.append(spline(colour, 0.30, path,
                        harmonics={3: (0.10, -0.06, 0.11),
                                   7: (-0.07, 0.10, -0.05)}))

    p.append(spline((-0.36, -0.44, -0.22), 0.58, RIM))

    for i, (y, x0, x1, phase) in enumerate(SCALE_ROWS):
        colour = (0.40, 0.70, 0.08) if i & 1 else (0.06, 0.46, 0.36)
        p.append(spline(colour, 0.26, chevrons(y, x0, x1, phase=phase),
                        harmonics={5: (0.04, 0.06, 0.015)}))

    p.append(spline((0.50, 0.76, 0.10), 0.29, PLATES,
                    harmonics={3: (0.04, 0.05, 0.012)}))

    for eye in (LEFT_EYE, mirror(LEFT_EYE)):
        p.append(spline((-0.78, -0.86, -0.48), 1.55, eye))
        p.append(spline((1.18, 0.90, 0.06), 0.80, eye,
                        harmonics={3: (0.09, 0.03, -0.02)}))
    for brow in (LEFT_BROW, mirror(LEFT_BROW)):
        p.append(spline((-0.52, -0.58, -0.32), 0.50, brow))
    for pupil in (LEFT_PUPIL, mirror(LEFT_PUPIL)):
        p.append(spline((-1.15, -1.15, -0.85), 0.44, pupil))
    for glint in (LEFT_GLINT, mirror(LEFT_GLINT)):
        p.append(spline((1.30, 1.10, 0.30), 0.26, glint))
    for pit in (LEFT_PIT, mirror(LEFT_PIT)):
        p.append(spline((-0.90, -0.95, -0.70), 0.30, pit))

    p.append(spline((0.10, 0.38, 0.16), 0.34, NOSE_RIDGE,
                    harmonics={4: (0.05, 0.08, 0.03)}))
    for nostril in (LEFT_NOSTRIL, mirror(LEFT_NOSTRIL)):
        p.append(spline((-0.98, -1.00, -0.78), 0.56, nostril))
    p.append(spline((-0.44, -0.52, -0.26), 0.47, MOUTH))
    p.append(spline((0.12, 0.38, 0.12), 0.33, CHIN))

    for fang in (LEFT_FANG, mirror(LEFT_FANG)):
        p.append(spline((0.95, 0.98, 0.90), 0.42, fang,
                        sigma_h={1: 0.18}))
    p.append(spline((1.05, 0.06, 0.36), 0.30, TONGUE_A,
                    harmonics={3: (0.08, 0.0, 0.05)}))
    p.append(spline((1.05, 0.06, 0.36), 0.30, TONGUE_B))

    return "\n".join(p) + "\n\n" + modular_tree() + "\n"


if __name__ == "__main__":
    source = program()
    Path("snake.tree").write_text(source)
    print(f"wrote snake.tree ({len(source.encode())} source bytes)")
