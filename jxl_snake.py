#!/usr/bin/env python3
"""Build a tiny native JPEG XL artwork: a frontal snake head.

No raster image is encoded. A zero-residual Modular tree generates the head
silhouette and its vertical colour field. Native JPEG XL splines add two eyes,
scale rows, facial anatomy and a low-cost chaotic background.
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


def zigzag(y, x0, x1, step=20, amp=6, phase=0):
    """One continuous interlocking scale row."""
    pts, x, high = [], x0, phase & 1
    while x <= x1:
        pts.append((x, y - amp if high else y + amp))
        x += step // 2
        high ^= 1
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
    return "\n".join([
        f"{indent}if y > {y0}",
        branch,
        band_tree(bands, i + 1, indent + "  "),
    ])


# A front-facing viper head: broad temples, then a tapered muzzle.
HEAD_BANDS = (
    (382, 0, 0, 0),
    (370, 205, 307, 42),
    (358, 180, 332, 48),
    (346, 158, 354, 54),
    (334, 137, 375, 60),
    (322, 120, 392, 66),
    (310, 105, 407, 72),
    (298, 92, 420, 78),
    (286, 82, 430, 84),
    (274, 76, 436, 88),
    (262, 72, 440, 92),
    (250, 76, 436, 94),
    (238, 84, 428, 92),
    (226, 98, 414, 88),
    (214, 116, 396, 80),
    (202, 142, 370, 70),
    (190, 176, 336, 58),
    (178, 214, 298, 46),
)

SCALE_ROWS = (
    (199, 196, 316, 0, 5),
    (217, 155, 357, 1, 6),
    (235, 122, 390, 0, 6),
    (253, 101, 411, 1, 7),
    (271, 91, 421, 0, 7),
    (289, 96, 416, 1, 7),
    (307, 112, 400, 0, 6),
    (325, 139, 373, 1, 6),
    (343, 176, 336, 0, 5),
)

# Edge and face paths.
TOP_EDGE = ((177, 191), (220, 174), (256, 169), (292, 174), (335, 191))
LEFT_BROW = ((127, 241), (166, 220), (211, 224))
RIGHT_BROW = ((301, 224), (346, 220), (385, 241))
LEFT_EYE = ((132, 251), (170, 235), (211, 251))
RIGHT_EYE = ((301, 251), (342, 235), (380, 251))
LEFT_PUPIL = ((171, 235), (171, 258))
RIGHT_PUPIL = ((341, 235), (341, 258))
NOSE_RIDGE = ((256, 225), (256, 286), (256, 322))
LEFT_NOSTRIL = ((225, 318), (234, 316))
RIGHT_NOSTRIL = ((278, 316), (287, 318))
MOUTH = ((186, 346), (227, 354), (256, 356), (285, 354), (326, 346))
CHIN = ((218, 371), (256, 377), (294, 371))

# Thin background paths: high visual variation for low spline area.
BG_PATHS = (
    ((12, 92), (92, 42), (184, 75), (270, 36), (368, 73), (500, 32)),
    ((4, 140), (86, 116), (154, 144), (240, 100), (334, 136), (506, 92)),
    ((8, 432), (98, 390), (188, 430), (278, 394), (376, 435), (505, 390)),
    ((25, 476), (116, 450), (205, 479), (305, 444), (399, 480), (492, 447)),
    ((35, 45), (18, 170), (47, 274), (20, 380), (52, 500)),
    ((476, 18), (493, 139), (466, 264), (494, 386), (470, 505)),
)


def modular_tree() -> str:
    # Channel 0 is the luminance-like head field. RCT 0 then combines two cheap
    # conditional channels with it, yielding a green/teal vertical gradient.
    return "\n".join([
        "if c > 1",
        "  if PrevAbs > 0",
        leaf(-24, "    "),
        leaf(0, "    "),
        "  if c > 0",
        "    if PrevAbs > 0",
        leaf(38, "      "),
        leaf(0, "      "),
        band_tree(HEAD_BANDS, indent="    "),
    ])


def program() -> str:
    p = [f"Width {W}", f"Height {H}", "Bitdepth 8", "GroupShift 3", "RCT 0"]

    # Chaotic spectral background. Sparse DCT harmonics vary colour along each
    # line, making the six paths read as a much denser nebula/lattice.
    bg_colours = [
        (0.04, 0.24, 0.34), (0.20, 0.05, 0.35), (0.02, 0.30, 0.18),
        (0.28, 0.06, 0.12), (0.05, 0.18, 0.30), (0.22, 0.04, 0.28),
    ]
    for i, path in enumerate(BG_PATHS):
        p.append(spline(bg_colours[i], 0.32, path,
                        harmonics={3: (0.08, -0.05, 0.09),
                                   7: (-0.06, 0.08, -0.04),
                                   15: (0.04, -0.03, 0.05)},
                        sigma_h={5: 0.05, 11: -0.035}))

    # Silhouette edges and repeated scale rows.
    p.append(spline((-0.34, -0.42, -0.21), 0.62, TOP_EDGE))
    for i, (y, x0, x1, phase, amp) in enumerate(SCALE_ROWS):
        colour = (0.43, 0.68, 0.08) if i & 1 else (0.08, 0.44, 0.28)
        p.append(spline(colour, 0.27, zigzag(y, x0, x1, amp=amp, phase=phase),
                        harmonics={5: (0.055, 0.075, 0.018),
                                   10: (-0.035, -0.05, 0.014),
                                   20: (0.022, 0.032, -0.008)}))

    # Two eyes and symmetric facial anatomy.
    for brow in (LEFT_BROW, RIGHT_BROW):
        p.append(spline((0.52, 0.82, 0.10), 0.85, brow,
                        harmonics={4: (0.10, 0.13, 0.02)}))
    for eye in (LEFT_EYE, RIGHT_EYE):
        p.append(spline((-0.70, -0.78, -0.42), 1.85, eye))
        p.append(spline((1.20, 0.92, 0.08), 1.02, eye,
                        harmonics={3: (0.12, 0.04, -0.02)}))
    for pupil in (LEFT_PUPIL, RIGHT_PUPIL):
        p.append(spline((-1.10, -1.10, -0.78), 0.34, pupil))

    p.append(spline((0.18, 0.34, 0.05), 0.34, NOSE_RIDGE,
                    harmonics={4: (0.05, 0.08, 0.01)}))
    p.append(spline((-0.94, -0.96, -0.74), 0.50, LEFT_NOSTRIL))
    p.append(spline((-0.94, -0.96, -0.74), 0.50, RIGHT_NOSTRIL))
    p.append(spline((-0.40, -0.48, -0.24), 0.42, MOUTH))
    p.append(spline((0.16, 0.30, 0.04), 0.30, CHIN))

    return "\n".join(p) + "\n\n" + modular_tree() + "\n"


if __name__ == "__main__":
    source = program()
    Path("snake.tree").write_text(source)
    print(f"wrote snake.tree ({len(source.encode())} source bytes)")
