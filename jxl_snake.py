#!/usr/bin/env python3
"""Design a tiny native JPEG XL artwork: a close-up scaled snake head."""

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


# Six narrow overlapping bands make a broad wedge-shaped viper head with much
# less decoder coverage than three enormous Gaussian strokes.
HEAD_ROWS = (
    ((178, 216), (251, 181), (337, 174), (413, 202), (459, 235)),
    ((145, 239), (235, 211), (338, 204), (430, 226), (482, 254)),
    ((123, 264), (225, 241), (344, 235), (446, 251), (495, 272)),
    ((117, 290), (229, 274), (350, 267), (451, 274), (496, 282)),
    ((128, 316), (237, 310), (353, 301), (443, 292), (489, 286)),
    ((157, 341), (249, 342), (350, 330), (427, 309), (476, 292)),
)

SCALE_ROWS = (
    (214, 202, 399, 0),
    (233, 171, 438, 1),
    (252, 148, 467, 0),
    (271, 134, 484, 1),
    (290, 132, 486, 0),
    (309, 148, 466, 1),
    (328, 178, 430, 0),
)

BROW = ((307, 226), (349, 210), (395, 215))
EYE = ((340, 239), (367, 230), (395, 240))
PUPIL = ((368, 225), (368, 245))
MOUTH = ((248, 329), (336, 322), (420, 305), (486, 282))
NOSTRIL = ((454, 263), (462, 261))
CHEEK = ((202, 302), (279, 294), (349, 287))


def program() -> str:
    p = [f"Width {W}", f"Height {H}", "Bitdepth 8", "GroupShift 3"]

    for i, path in enumerate(HEAD_ROWS):
        # Compact dark border and a colored inner band. Sigma stays low enough
        # for conservative decoders while the overlapping rows still read solid.
        p.append(spline((-0.78, -0.84, -0.62), 4.15, path,
                        sigma_h={1: -0.32, 4: 0.10}))
        base = ((0.08, 0.66, 0.13), (0.07, 0.82, 0.16),
                (0.08, 0.94, 0.19), (0.07, 0.86, 0.16),
                (0.06, 0.70, 0.12), (0.05, 0.54, 0.09))[i]
        p.append(spline(base, 3.15, path,
                        harmonics={3: (0.09, -0.13, 0.06),
                                   8: (-0.06, 0.11, -0.04),
                                   15: (0.04, -0.07, 0.03)},
                        sigma_h={2: -0.20, 7: 0.07}))

    # Staggered scalloped rows imply dozens of overlapping scales.
    for i, (y, x0, x1, phase) in enumerate(SCALE_ROWS):
        color = (0.34, 0.56, 0.07) if i & 1 else (0.12, 0.43, 0.20)
        p.append(spline(color, 0.30, wave(y, x0, x1, phase=phase),
                        harmonics={6: (0.035, 0.05, 0.015),
                                   12: (-0.025, -0.035, 0.01)}))

    p.append(spline((0.44, 0.72, 0.10), 1.05, BROW,
                    harmonics={4: (0.10, 0.12, 0.02)}))
    p.append(spline((-0.58, -0.65, -0.34), 2.10, EYE))
    p.append(spline((1.25, 0.92, 0.08), 1.28, EYE))
    p.append(spline((-1.05, -1.05, -0.72), 0.40, PUPIL))
    p.append(spline((-0.34, -0.42, -0.20), 0.46, MOUTH))
    p.append(spline((0.18, 0.30, 0.04), 0.32, CHEEK,
                    harmonics={5: (0.05, 0.07, 0.01)}))
    p.append(spline((-0.92, -0.94, -0.72), 0.54, NOSTRIL))

    return "\n".join(p) + "\n\n- Set 0\n"


if __name__ == "__main__":
    s = program()
    Path("snake.tree").write_text(s)
    print(f"wrote snake.tree ({len(s.encode())} source bytes)")
