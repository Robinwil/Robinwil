#!/usr/bin/env python3
"""Build a tiny native JPEG XL artwork: a frontal scaled snake head.

No raster image is encoded. A zero-residual Modular tree generates the head
silhouette and green vertical colour field. Native JPEG XL splines add two eyes,
interlocking scales, facial anatomy and a chaotic spectral background.
"""

from pathlib import Path

W = H = 512


def n(v: float) -> str:
    return "0" if not v else f"{v:.5g}"


def spline(rgb, sigma, pts, harmonics=None, sigma_h=None):
    c = [[0.0] * 32 for _ in range(4)]
    c[0][0], c[1][0], c[2][0], c[3][0] = *rgb, sigma
    for i, v in (harmonics or {}).items():
        c[0][i], c[1][i], c[2][i] = v
    for i, v in (sigma_h or {}).items():
        c[3][i] = v
    coeff = " ".join(n(v) for ch in c for v in ch)
    points = " ".join(f"{x} {y}" for x, y in pts)
    return f"Spline {coeff} {points} EndSpline"


def scallops(y, x0, x1, step=22, amp=7, phase=0):
    """Repeated V-shaped scale boundaries on a common baseline."""
    pts = []
    x = x0 + (step // 2 if phase else 0)
    while x + step <= x1:
        pts.extend(((x, y), (x + step // 2, y + amp), (x + step, y)))
        x += step
    return tuple(pts)


def leaf(value: int, indent="") -> str:
    return f"{indent}- Set - {abs(value)}" if value < 0 else f"{indent}- Set {value}"


def x_range(x0: int, x1: int, value: int, indent: str) -> str:
    return "\n".join([
        f"{indent}if x > {x1}",
        leaf(0, indent + "  "),
        f"{indent}  if x > {x0}",
        leaf(value, indent + "    "),
        leaf(0, indent + "    "),
    ])


def band_tree(bands, i=0, indent="") -> str:
    if i == len(bands):
        return leaf(0, indent)
    y0, x0, x1, value = bands[i]
    branch = leaf(0, indent + "  ") if not value else x_range(x0, x1, value, indent + "  ")
    return "\n".join((
        f"{indent}if y > {y0}",
        branch,
        band_tree(bands, i + 1, indent + "  "),
    ))


# Broad temples around the eyes, then a narrow muzzle and chin.
HEAD_BANDS = (
    (384, 0, 0, 0),
    (372, 228, 284, 42),
    (360, 214, 298, 48),
    (348, 198, 314, 54),
    (336, 180, 332, 60),
    (324, 160, 352, 68),
    (312, 140, 372, 74),
    (300, 120, 392, 80),
    (288, 102, 410, 86),
    (276, 84, 428, 92),
    (264, 70, 442, 98),
    (252, 62, 450, 104),
    (240, 58, 454, 108),
    (228, 64, 448, 106),
    (216, 78, 434, 100),
    (204, 100, 412, 90),
    (192, 132, 380, 76),
    (180, 172, 340, 60),
    (168, 216, 296, 46),
)

SCALE_ROWS = (
    (187, 194, 318, 22, 5, 0),
    (205, 154, 358, 22, 6, 1),
    (223, 118, 394, 22, 6, 0),
    (241, 88, 424, 22, 7, 1),
    (259, 74, 438, 22, 8, 0),
    (277, 82, 430, 22, 8, 1),
    (295, 102, 410, 22, 7, 0),
    (313, 130, 382, 22, 7, 1),
    (331, 166, 346, 22, 6, 0),
    (349, 202, 310, 22, 5, 1),
)

TOP_EDGE = ((169, 181), (214, 161), (256, 156), (298, 161), (343, 181))
LEFT_EDGE = ((169, 181), (105, 205), (61, 239), (72, 276), (116, 307), (180, 336))
RIGHT_EDGE = tuple((512 - x, y) for x, y in LEFT_EDGE)

LEFT_EYE_TOP = ((107, 236), (151, 211), (207, 229))
LEFT_EYE_LOW = ((107, 236), (154, 252), (207, 229))
RIGHT_EYE_TOP = tuple((512 - x, y) for x, y in LEFT_EYE_TOP)
RIGHT_EYE_LOW = tuple((512 - x, y) for x, y in LEFT_EYE_LOW)
LEFT_PUPIL = ((157, 219), (157, 247))
RIGHT_PUPIL = ((355, 219), (355, 247))
LEFT_EYE_GLINT = ((151, 224), (155, 222))
RIGHT_EYE_GLINT = ((357, 222), (361, 224))

NOSE_RIDGE = ((256, 213), (256, 276), (256, 322))
LEFT_NOSTRIL = ((224, 318), (234, 315))
RIGHT_NOSTRIL = tuple((512 - x, y) for x, y in LEFT_NOSTRIL)
MOUTH = ((190, 345), (225, 354), (256, 357), (287, 354), (322, 345))
CHIN = ((222, 371), (256, 378), (290, 371))

# Background paths combine smooth waves with angular nested repetitions.
BG_PATHS = (
    ((8, 76), (72, 34), (136, 82), (200, 42), (264, 80), (328, 36), (392, 76), (504, 28)),
    ((5, 126), (70, 104), (135, 140), (205, 96), (276, 136), (350, 102), (505, 82)),
    ((8, 430), (72, 384), (140, 434), (208, 390), (278, 432), (350, 388), (504, 430)),
    ((18, 480), (88, 448), (154, 486), (224, 446), (296, 482), (372, 444), (496, 476)),
    ((34, 24), (16, 98), (48, 164), (18, 234), (50, 306), (20, 382), (53, 500)),
    ((478, 18), (496, 96), (465, 166), (495, 238), (463, 312), (494, 392), (468, 504)),
    ((30, 58), (84, 94), (126, 54), (174, 100), (218, 62), (256, 108), (298, 62), (342, 100), (390, 54), (444, 94), (494, 58)),
    ((28, 456), (80, 420), (126, 462), (174, 416), (216, 458), (256, 412), (298, 458), (340, 416), (388, 462), (438, 420), (494, 456)),
)


def modular_tree() -> str:
    # RCT 0 stores G, R-G, B-G. Negative chroma deltas therefore produce a
    # saturated green field whose brightness changes from forehead to muzzle.
    return "\n".join([
        "if c > 1",
        "  if PrevAbs > 0",
        leaf(-18, "    "),
        leaf(0, "    "),
        "  if c > 0",
        "    if PrevAbs > 0",
        leaf(-34, "      "),
        leaf(0, "      "),
        band_tree(HEAD_BANDS, indent="    "),
    ])


def program() -> str:
    p = [
        f"Width {W}", f"Height {H}", "Bitdepth 8", "GroupShift 3", "RCT 0",
        "Gaborish",
    ]

    bg_colours = (
        (0.04, 0.24, 0.34), (0.20, 0.05, 0.35), (0.02, 0.30, 0.18),
        (0.28, 0.06, 0.12), (0.05, 0.18, 0.30), (0.22, 0.04, 0.28),
        (0.05, 0.28, 0.24), (0.26, 0.05, 0.18),
    )
    for colour, path in zip(bg_colours, BG_PATHS):
        p.append(spline(colour, 0.25, path,
                        harmonics={3: (0.08, -0.05, 0.09),
                                   7: (-0.06, 0.08, -0.04),
                                   15: (0.04, -0.03, 0.05)},
                        sigma_h={5: 0.04, 11: -0.025}))

    # Fine contour strokes conceal the staircase edges of the Modular mask.
    p.append(spline((-0.36, -0.44, -0.22), 0.55, TOP_EDGE))
    p.append(spline((-0.36, -0.44, -0.22), 0.55, LEFT_EDGE))
    p.append(spline((-0.36, -0.44, -0.22), 0.55, RIGHT_EDGE))

    # Interlocking V rows, alternating phase and hue.
    for i, (y, x0, x1, step, amp, phase) in enumerate(SCALE_ROWS):
        colour = (0.40, 0.68, 0.07) if i & 1 else (0.06, 0.46, 0.25)
        p.append(spline(colour, 0.24, scallops(y, x0, x1, step, amp, phase),
                        harmonics={5: (0.055, 0.075, 0.018),
                                   10: (-0.035, -0.05, 0.014),
                                   20: (0.022, 0.032, -0.008)}))

    # Almond eyes are made from two arcs each, then slit pupils and glints.
    for top, low in ((LEFT_EYE_TOP, LEFT_EYE_LOW), (RIGHT_EYE_TOP, RIGHT_EYE_LOW)):
        p.append(spline((-0.74, -0.82, -0.45), 1.45, top))
        p.append(spline((-0.74, -0.82, -0.45), 1.45, low))
        p.append(spline((1.18, 0.90, 0.07), 0.75, top,
                        harmonics={3: (0.10, 0.03, -0.02)}))
        p.append(spline((1.18, 0.90, 0.07), 0.75, low,
                        harmonics={3: (0.10, 0.03, -0.02)}))
    for pupil in (LEFT_PUPIL, RIGHT_PUPIL):
        p.append(spline((-1.12, -1.12, -0.80), 0.38, pupil))
    p.append(spline((1.25, 1.05, 0.22), 0.24, LEFT_EYE_GLINT))
    p.append(spline((1.25, 1.05, 0.22), 0.24, RIGHT_EYE_GLINT))

    p.append(spline((0.15, 0.34, 0.05), 0.32, NOSE_RIDGE,
                    harmonics={4: (0.05, 0.08, 0.01)}))
    p.append(spline((-0.96, -0.98, -0.76), 0.52, LEFT_NOSTRIL))
    p.append(spline((-0.96, -0.98, -0.76), 0.52, RIGHT_NOSTRIL))
    p.append(spline((-0.42, -0.50, -0.25), 0.43, MOUTH))
    p.append(spline((0.18, 0.32, 0.04), 0.30, CHIN))

    return "\n".join(p) + "\n\n" + modular_tree() + "\n"


if __name__ == "__main__":
    source = program()
    Path("snake.tree").write_text(source)
    print(f"wrote snake.tree ({len(source.encode())} source bytes)")
