#!/usr/bin/env python3
"""Build a tiny native JPEG XL artwork: a frontal scaled snake head.

The codestream is authored at 256x256 and decoder-upsampled to 512x512. A
zero-residual Modular tree creates the head and colour gradient; native splines
create the eyes, scale mesh and chaotic background. No raster source exists.
"""

from pathlib import Path

S = 2
W = H = 256


def n(v: float) -> str:
    return "0" if not v else f"{v:.5g}"


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


def scallops(y, x0, x1, step=22, amp=7, phase=0):
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
    y0 = round(y0 / S)
    branch = leaf(0, indent + "  ") if not value else x_range(x0, x1, value, indent + "  ")
    return "\n".join((
        f"{indent}if y > {y0}",
        branch,
        band_tree(bands, i + 1, indent + "  "),
    ))


# Front-facing viper silhouette. Broad temples taper into a compact muzzle.
HEAD_BANDS = (
    (386, 0, 0, 0),
    (378, 234, 278, 44), (370, 225, 287, 48), (362, 216, 296, 52),
    (354, 206, 306, 56), (346, 194, 318, 60), (338, 181, 331, 65),
    (330, 167, 345, 70), (322, 152, 360, 75), (314, 137, 375, 80),
    (306, 122, 390, 85), (298, 108, 404, 90), (290, 94, 418, 95),
    (282, 82, 430, 100), (274, 72, 440, 104), (266, 64, 448, 108),
    (258, 58, 454, 112), (250, 56, 456, 114), (242, 58, 454, 114),
    (234, 62, 450, 112), (226, 70, 442, 108), (218, 82, 430, 102),
    (210, 96, 416, 94), (202, 114, 398, 84), (194, 136, 376, 74),
    (186, 162, 350, 64), (178, 190, 322, 54), (170, 218, 294, 46),
)

SCALE_ROWS = (
    (187, 194, 318, 24, 5, 0), (205, 154, 358, 24, 6, 1),
    (223, 118, 394, 24, 6, 0), (241, 88, 424, 24, 7, 1),
    (259, 74, 438, 24, 8, 0), (277, 82, 430, 24, 8, 1),
    (295, 102, 410, 24, 7, 0), (313, 130, 382, 24, 7, 1),
    (331, 166, 346, 24, 6, 0), (349, 202, 310, 24, 5, 1),
)

TOP_EDGE = ((169, 181), (214, 161), (256, 156), (298, 161), (343, 181))
LEFT_EDGE = ((169, 181), (105, 205), (61, 239), (72, 276), (116, 307), (180, 336))
RIGHT_EDGE = mirror(LEFT_EDGE)

LEFT_EYE_TOP = ((106, 237), (151, 209), (208, 229))
LEFT_EYE_LOW = ((106, 237), (154, 255), (208, 229))
RIGHT_EYE_TOP = mirror(LEFT_EYE_TOP)
RIGHT_EYE_LOW = mirror(LEFT_EYE_LOW)
LEFT_PUPIL = ((157, 216), (157, 250))
RIGHT_PUPIL = mirror(LEFT_PUPIL)
LEFT_GLINT = ((148, 222), (153, 219))
RIGHT_GLINT = mirror(LEFT_GLINT)

NOSE_RIDGE = ((256, 211), (256, 274), (256, 323))
LEFT_NOSTRIL = ((223, 318), (235, 314))
RIGHT_NOSTRIL = mirror(LEFT_NOSTRIL)
MOUTH = ((188, 345), (224, 355), (256, 359), (288, 355), (324, 345))
CHIN = ((221, 372), (256, 380), (291, 372))

# Diagonal cheek lines cross the scallops and turn them into a scale lattice.
LEFT_MESH = (
    ((86, 236), (132, 277), (177, 321)),
    ((102, 215), (151, 264), (201, 315)),
    ((123, 198), (174, 247), (224, 298)),
    ((148, 184), (197, 228), (241, 274)),
)
RIGHT_MESH = tuple(mirror(path) for path in LEFT_MESH)

FOREHEAD_DIAMONDS = (
    ((256, 174), (229, 198), (256, 222), (283, 198), (256, 174)),
    ((256, 220), (231, 243), (256, 266), (281, 243), (256, 220)),
    ((256, 264), (237, 282), (256, 300), (275, 282), (256, 264)),
)

BG_PATHS = (
    ((8, 76), (72, 34), (136, 82), (200, 42), (264, 80), (328, 36), (392, 76), (504, 28)),
    ((5, 126), (70, 104), (135, 140), (205, 96), (276, 136), (350, 102), (505, 82)),
    ((8, 430), (72, 384), (140, 434), (208, 390), (278, 432), (350, 388), (504, 430)),
    ((18, 480), (88, 448), (154, 486), (224, 446), (296, 482), (372, 444), (496, 476)),
    ((34, 24), (16, 98), (48, 164), (18, 234), (50, 306), (20, 382), (53, 500)),
    ((478, 18), (496, 96), (465, 166), (495, 238), (463, 312), (494, 392), (468, 504)),
)


def modular_tree() -> str:
    # RCT 0 uses channel 0 as red plus two colour differences. A large positive
    # green delta and a small negative blue delta produce a saturated green head.
    return "\n".join([
        "if c > 1",
        "  if PrevAbs > 0",
        leaf(-8, "    "),
        leaf(0, "    "),
        "  if c > 0",
        "    if PrevAbs > 0",
        leaf(68, "      "),
        leaf(0, "      "),
        band_tree(HEAD_BANDS, indent="    "),
    ])


def program() -> str:
    p = [
        f"Width {W}", f"Height {H}", "Bitdepth 8", "GroupShift 3",
        "Upsample 2", "RCT 0", "Gaborish",
        "Noise 0.015 0.03 0.06 0.09 0.07 0.045 0.025 0.012",
    ]

    bg_colours = (
        (0.04, 0.24, 0.34), (0.20, 0.05, 0.35), (0.02, 0.30, 0.18),
        (0.28, 0.06, 0.12), (0.05, 0.18, 0.30), (0.22, 0.04, 0.28),
    )
    for colour, path in zip(bg_colours, BG_PATHS):
        p.append(spline(colour, 0.28, path,
                        harmonics={3: (0.08, -0.05, 0.09),
                                   7: (-0.06, 0.08, -0.04),
                                   15: (0.04, -0.03, 0.05)},
                        sigma_h={5: 0.04, 11: -0.025}))

    p.append(spline((-0.36, -0.44, -0.22), 0.58, TOP_EDGE))
    p.append(spline((-0.36, -0.44, -0.22), 0.58, LEFT_EDGE))
    p.append(spline((-0.36, -0.44, -0.22), 0.58, RIGHT_EDGE))

    for i, (y, x0, x1, step, amp, phase) in enumerate(SCALE_ROWS):
        colour = (0.40, 0.68, 0.07) if i & 1 else (0.06, 0.46, 0.25)
        p.append(spline(colour, 0.28, scallops(y, x0, x1, step, amp, phase),
                        harmonics={5: (0.055, 0.075, 0.018),
                                   10: (-0.035, -0.05, 0.014),
                                   20: (0.022, 0.032, -0.008)}))

    for path in LEFT_MESH + RIGHT_MESH:
        p.append(spline((0.12, 0.32, 0.18), 0.22, path,
                        harmonics={4: (0.04, 0.055, 0.01)}))
    for i, path in enumerate(FOREHEAD_DIAMONDS):
        colour = (0.48, 0.72, 0.08) if i != 1 else (0.08, 0.50, 0.28)
        p.append(spline(colour, 0.26, path,
                        harmonics={3: (0.05, 0.06, 0.015)}))

    for top, low in ((LEFT_EYE_TOP, LEFT_EYE_LOW), (RIGHT_EYE_TOP, RIGHT_EYE_LOW)):
        p.append(spline((-0.74, -0.82, -0.45), 1.55, top))
        p.append(spline((-0.74, -0.82, -0.45), 1.55, low))
        p.append(spline((1.18, 0.90, 0.07), 0.82, top,
                        harmonics={3: (0.10, 0.03, -0.02)}))
        p.append(spline((1.18, 0.90, 0.07), 0.82, low,
                        harmonics={3: (0.10, 0.03, -0.02)}))
    for pupil in (LEFT_PUPIL, RIGHT_PUPIL):
        p.append(spline((-1.12, -1.12, -0.80), 0.42, pupil))
    p.append(spline((1.25, 1.05, 0.22), 0.26, LEFT_GLINT))
    p.append(spline((1.25, 1.05, 0.22), 0.26, RIGHT_GLINT))

    p.append(spline((0.15, 0.34, 0.05), 0.34, NOSE_RIDGE,
                    harmonics={4: (0.05, 0.08, 0.01)}))
    p.append(spline((-0.96, -0.98, -0.76), 0.55, LEFT_NOSTRIL))
    p.append(spline((-0.96, -0.98, -0.76), 0.55, RIGHT_NOSTRIL))
    p.append(spline((-0.42, -0.50, -0.25), 0.46, MOUTH))
    p.append(spline((0.18, 0.32, 0.04), 0.32, CHIN))

    return "\n".join(p) + "\n\n" + modular_tree() + "\n"


if __name__ == "__main__":
    source = program()
    Path("snake.tree").write_text(source)
    print(f"wrote snake.tree ({len(source.encode())} source bytes)")
