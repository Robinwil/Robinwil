#!/usr/bin/env python3
"""Design a tiny native JPEG XL artwork: a close-up scaled snake head.

The head silhouette and fill are produced by the zero-residual Modular tree.
Native JPEG XL splines are used only for the visible scales and facial details.
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


def wave(y, x0, x1, step=18, amp=7, phase=0):
    pts, x, up = [], x0, phase & 1
    while x <= x1:
        pts.append((x, y - amp if up else y + 1))
        x += step // 2
        up ^= 1
    return tuple(pts)


def leaf(value: int, indent: str = "") -> str:
    if value < 0:
        return f"{indent}- Set - {abs(value)}"
    return f"{indent}- Set {value}"


def x_range(x0: int, x1: int, value: int, indent: str) -> str:
    return "\n".join([
        f"{indent}if x > {x1}",
        leaf(0, indent + "  "),
        f"{indent}  if x > {x0}",
        leaf(value, indent + "    "),
        leaf(0, indent + "    "),
    ])


def band_tree(bands, index=0, indent="") -> str:
    if index == len(bands):
        return leaf(0, indent)
    y0, x0, x1, value = bands[index]
    true_branch = leaf(0, indent + "  ") if value == 0 else x_range(
        x0, x1, value, indent + "  "
    )
    return "\n".join([
        f"{indent}if y > {y0}",
        true_branch,
        band_tree(bands, index + 1, indent + "  "),
    ])


# The first slice is intentionally empty: it cuts the head off below y=350.
HEAD_BANDS = (
    (350, 0, 0, 0),
    (338, 154, 452, 42),
    (326, 137, 468, 46),
    (314, 124, 480, 50),
    (302, 116, 489, 54),
    (290, 111, 496, 58),
    (278, 109, 499, 62),
    (266, 112, 496, 66),
    (254, 120, 488, 68),
    (242, 134, 475, 66),
    (230, 151, 456, 62),
    (218, 174, 432, 56),
    (206, 205, 401, 48),
    (194, 242, 365, 40),
)

SCALE_ROWS = (
    (214, 205, 390, 0), (233, 174, 431, 1), (252, 148, 464, 0),
    (271, 132, 484, 1), (290, 130, 486, 0), (309, 145, 466, 1),
    (328, 173, 434, 0), (347, 205, 395, 1),
)

TOP_EDGE = ((192, 213), (246, 188), (315, 178), (381, 190), (446, 229))
LOW_EDGE = ((171, 353), (252, 359), (342, 347), (421, 322), (486, 288))
BROW = ((303, 231), (346, 213), (397, 218))
EYE = ((337, 244), (367, 233), (399, 244))
PUPIL = ((368, 227), (368, 249))
MOUTH = ((243, 337), (333, 328), (420, 308), (490, 282))
NOSTRIL = ((455, 263), (464, 261))
CHEEK = ((196, 307), (274, 299), (348, 291))


def modular_tree() -> str:
    return "\n".join([
        "if c > 1",
        "  if PrevAbs > 0",
        leaf(-18, "    "),
        leaf(0, "    "),
        "  if c > 0",
        "    if PrevAbs > 0",
        leaf(28, "      "),
        leaf(0, "      "),
        band_tree(HEAD_BANDS, indent="    "),
    ])


def program() -> str:
    p = [
        f"Width {W}", f"Height {H}", "Bitdepth 8", "GroupShift 3", "RCT 0"
    ]

    p.append(spline((-0.38, -0.46, -0.24), 0.70, TOP_EDGE))
    p.append(spline((-0.38, -0.46, -0.24), 0.70, LOW_EDGE))
    for i, (y, x0, x1, phase) in enumerate(SCALE_ROWS):
        color = (0.38, 0.62, 0.07) if i & 1 else (0.12, 0.46, 0.21)
        p.append(spline(color, 0.30, wave(y, x0, x1, phase=phase),
                        harmonics={6: (0.035, 0.05, 0.015),
                                   12: (-0.025, -0.035, 0.01)}))

    p.append(spline((0.48, 0.77, 0.10), 1.05, BROW,
                    harmonics={4: (0.10, 0.12, 0.02)}))
    p.append(spline((-0.62, -0.69, -0.37), 2.10, EYE))
    p.append(spline((1.28, 0.94, 0.08), 1.28, EYE))
    p.append(spline((-1.08, -1.08, -0.75), 0.40, PUPIL))
    p.append(spline((-0.36, -0.44, -0.21), 0.46, MOUTH))
    p.append(spline((0.18, 0.31, 0.04), 0.32, CHEEK,
                    harmonics={5: (0.05, 0.07, 0.01)}))
    p.append(spline((-0.94, -0.96, -0.74), 0.54, NOSTRIL))

    return "\n".join(p) + "\n\n" + modular_tree() + "\n"


if __name__ == "__main__":
    source = program()
    Path("snake.tree").write_text(source)
    print(f"wrote snake.tree ({len(source.encode())} source bytes)")
