#!/usr/bin/env python3
"""Build a tiny native JPEG XL artwork: a frontal scaled snake head.

Authored at 256x256 and decoder-upsampled to 512x512. A zero-residual Modular
tree generates a smooth-ish viper silhouette and hue-shifting gradient. Native
splines create two eyes, diamond scales and a chaotic textured background.
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


def chevrons(y, x0, x1, step=30, amp=9, phase=0, direction=1):
    """One half of a row of diamonds; pair directions +1 and -1."""
    x = x0 + (step // 2 if phase else 0)
    pts = [(x, y)]
    while x + step <= x1:
        pts.extend(((x + step // 2, y + direction * amp), (x + step, y)))
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
        f"{indent}if y > {y0}", branch, band_tree(bands, i + 1, indent + "  "),
    ))


def head_bands():
    """6-output-pixel slices: broad eye region, sharply tapered muzzle."""
    bands = [(388, 0, 0, 0)]
    for y in range(382, 165, -6):
        if y <= 250:
            half = 40 + (y - 166) * 165 / 84
        elif y <= 278:
            half = 205 - (y - 250) * 0.45
        else:
            half = 192 - (y - 278) * 1.48
        half = max(24, int(half))
        # Green field is brightest around brow/temples, darker at crown/chin.
        value = int(46 + 68 * max(0.0, 1.0 - abs(y - 252) / 126))
        bands.append((y, 256 - half, 256 + half, value))
    return tuple(bands)


HEAD_BANDS = head_bands()

# Six double-chevron rows form actual closed diamond/rhombus scales.
SCALE_ROWS = (
    (202, 154, 358, 30, 7, 0),
    (228, 102, 410, 30, 9, 1),
    (254, 72, 440, 30, 10, 0),
    (280, 84, 428, 30, 10, 1),
    (306, 118, 394, 30, 9, 0),
    (332, 166, 346, 30, 7, 1),
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

# Large central head plates, separate from the smaller cheek scales.
FOREHEAD_PLATES = (
    ((256, 173), (225, 199), (256, 225), (287, 199), (256, 173)),
    ((256, 225), (229, 250), (256, 275), (283, 250), (256, 225)),
    ((256, 275), (237, 293), (256, 311), (275, 293), (256, 275)),
)

BG_PATHS = (
    ((8, 76), (72, 34), (136, 82), (200, 42), (264, 80), (328, 36), (392, 76), (504, 28)),
    ((5, 126), (70, 104), (135, 140), (205, 96), (276, 136), (350, 102), (505, 82)),
    ((8, 430), (72, 384), (140, 434), (208, 390), (278, 432), (350, 388), (504, 430)),
    ((18, 480), (88, 448), (154, 486), (224, 446), (296, 482), (372, 444), (496, 476)),
    ((34, 24), (16, 98), (48, 164), (18, 234), (50, 306), (20, 382), (53, 500)),
    ((478, 18), (496, 96), (465, 166), (495, 238), (463, 312), (494, 392), (468, 504)),
)


def delta_green(indent):
    """Quantize channel-0 brightness into four green differences."""
    return "\n".join([
        f"{indent}if PrevAbs > 100", leaf(80, indent + "  "),
        f"{indent}  if PrevAbs > 85", leaf(70, indent + "    "),
        f"{indent}    if PrevAbs > 65", leaf(58, indent + "      "),
        leaf(46, indent + "      "),
    ])


def delta_blue(indent):
    """Channel 2 sees the quantized green delta, so it can shift hue cheaply."""
    return "\n".join([
        f"{indent}if PrevAbs > 75", leaf(16, indent + "  "),
        f"{indent}  if PrevAbs > 65", leaf(4, indent + "    "),
        f"{indent}    if PrevAbs > 52", leaf(-8, indent + "      "),
        leaf(-20, indent + "      "),
    ])


def modular_tree() -> str:
    return "\n".join([
        "if c > 1",
        "  if PrevAbs > 0",
        delta_blue("    "),
        leaf(0, "    "),
        "  if c > 0",
        "    if PrevAbs > 0",
        delta_green("      "),
        leaf(0, "      "),
        band_tree(HEAD_BANDS, indent="    "),
    ])


def program() -> str:
    p = [
        f"Width {W}", f"Height {H}", "Bitdepth 8", "GroupShift 3",
        "Upsample 2", "RCT 0", "Gaborish",
        "Noise 0.03 0.06 0.12 0.18 0.14 0.09 0.05 0.025",
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
        bright = (0.42, 0.70, 0.08) if i & 1 else (0.08, 0.50, 0.28)
        dark = (-0.14, -0.20, -0.08)
        p.append(spline(bright, 0.27, chevrons(y, x0, x1, step, amp, phase, 1),
                        harmonics={5: (0.05, 0.07, 0.018),
                                   10: (-0.03, -0.045, 0.012)}))
        p.append(spline(dark, 0.20, chevrons(y, x0, x1, step, amp, phase, -1)))

    for i, path in enumerate(FOREHEAD_PLATES):
        colour = (0.50, 0.76, 0.09) if i != 1 else (0.08, 0.53, 0.30)
        p.append(spline(colour, 0.28, path,
                        harmonics={3: (0.05, 0.065, 0.015)}))

    for top, low in ((LEFT_EYE_TOP, LEFT_EYE_LOW), (RIGHT_EYE_TOP, RIGHT_EYE_LOW)):
        p.append(spline((-0.76, -0.84, -0.46), 1.58, top))
        p.append(spline((-0.76, -0.84, -0.46), 1.58, low))
        p.append(spline((1.20, 0.92, 0.07), 0.84, top,
                        harmonics={3: (0.10, 0.03, -0.02)}))
        p.append(spline((1.20, 0.92, 0.07), 0.84, low,
                        harmonics={3: (0.10, 0.03, -0.02)}))
    for pupil in (LEFT_PUPIL, RIGHT_PUPIL):
        p.append(spline((-1.14, -1.14, -0.82), 0.43, pupil))
    p.append(spline((1.28, 1.08, 0.24), 0.27, LEFT_GLINT))
    p.append(spline((1.28, 1.08, 0.24), 0.27, RIGHT_GLINT))

    p.append(spline((0.15, 0.34, 0.05), 0.34, NOSE_RIDGE,
                    harmonics={4: (0.05, 0.08, 0.01)}))
    p.append(spline((-0.98, -1.00, -0.78), 0.56, LEFT_NOSTRIL))
    p.append(spline((-0.98, -1.00, -0.78), 0.56, RIGHT_NOSTRIL))
    p.append(spline((-0.44, -0.52, -0.26), 0.47, MOUTH))
    p.append(spline((0.18, 0.32, 0.04), 0.33, CHIN))

    return "\n".join(p) + "\n\n" + modular_tree() + "\n"


if __name__ == "__main__":
    source = program()
    Path("snake.tree").write_text(source)
    print(f"wrote snake.tree ({len(source.encode())} source bytes)")
