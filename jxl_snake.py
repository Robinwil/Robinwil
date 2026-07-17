#!/usr/bin/env python3
"""Design a tiny native JPEG XL artwork: a close-up snake head of scales.

This does not rasterize an image. It emits a jxl_from_tree program whose
zero-residual Modular frame and native JPEG XL splines generate the picture.
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
    """A staggered scallop row; neighbouring rows interlock like scales."""
    pts = []
    x = x0
    up = phase & 1
    while x <= x1:
        pts.append((x, y - amp if up else y + 1))
        x += step // 2
        up ^= 1
    return tuple(pts)


# Three broad, short strokes overlap into a single viper-like head. Their
# different centerlines create a wedge rather than a body-shaped tube.
TOP = ((118, 267), (182, 211), (278, 171), (376, 169), (463, 224))
MID = ((105, 302), (199, 264), (315, 239), (423, 244), (492, 276))
LOW = ((126, 341), (222, 344), (338, 329), (431, 310), (489, 286))

# Rows are deliberately bounded to the head silhouette instead of being clipped
# from a source image. Staggering and slightly changing their widths gives a
# dense field of apparent scales from only a few spline declarations.
SCALE_ROWS = (
    (204, 190, 393, 0),
    (224, 163, 432, 1),
    (244, 143, 459, 0),
    (264, 130, 478, 1),
    (284, 126, 486, 0),
    (304, 137, 475, 1),
    (324, 158, 445, 0),
    (344, 190, 405, 1),
)

BROW = ((309, 218), (347, 204), (390, 207))
EYE = ((344, 230), (366, 224), (388, 231))
PUPIL = ((367, 220), (367, 238))
MOUTH = ((251, 337), (340, 329), (424, 310), (487, 283))
NOSTRIL = ((454, 264), (461, 262))
CHEEK = ((203, 309), (277, 300), (346, 292))


def program() -> str:
    p = [f"Width {W}", f"Height {H}", "Bitdepth 8", "GroupShift 3"]

    # Dark silhouette first. Large Gaussian strokes overlap into a filled head.
    for path, sigma in ((TOP, 9.0), (MID, 10.0), (LOW, 8.2)):
        p.append(spline((-0.88, -0.93, -0.72), sigma, path,
                        sigma_h={1: -0.9, 3: 0.25}))

    # Iridescent fill: each layer has sparse DCT colour harmonics, so colour and
    # thickness change along the head without per-pixel data.
    p.append(spline((0.10, 0.72, 0.15), 7.0, TOP,
                    harmonics={2: (0.10, 0.16, -0.02),
                               7: (-0.08, 0.13, 0.05),
                               13: (0.06, -0.10, 0.04)},
                    sigma_h={1: -0.55, 5: 0.18}))
    p.append(spline((0.08, 0.93, 0.18), 8.0, MID,
                    harmonics={3: (0.12, -0.18, 0.08),
                               9: (-0.09, 0.16, -0.06),
                               17: (0.06, -0.11, 0.04)},
                    sigma_h={2: -0.45, 8: 0.16}))
    p.append(spline((0.06, 0.58, 0.10), 6.3, LOW,
                    harmonics={4: (0.08, 0.12, 0.03),
                               11: (-0.06, -0.09, 0.02)}))

    # Interlocking scale rows. Every second row is staggered. Alternating lime
    # and cool highlights make the pattern look denser than its encoded rules.
    for i, (y, x0, x1, phase) in enumerate(SCALE_ROWS):
        color = (0.32, 0.52, 0.06) if i & 1 else (0.12, 0.42, 0.20)
        p.append(spline(color, 0.34, wave(y, x0, x1, phase=phase),
                        harmonics={6: (0.035, 0.05, 0.015),
                                   12: (-0.025, -0.035, 0.01)}))

    # Face anatomy: brow ridge, eye with slit pupil, cheek, nostril and jaw.
    p.append(spline((0.42, 0.70, 0.10), 1.15, BROW,
                    harmonics={4: (0.10, 0.12, 0.02)}))
    p.append(spline((-0.58, -0.65, -0.34), 2.35, EYE))
    p.append(spline((1.25, 0.92, 0.08), 1.45, EYE))
    p.append(spline((-1.05, -1.05, -0.72), 0.42, PUPIL))
    p.append(spline((-0.34, -0.42, -0.20), 0.48, MOUTH))
    p.append(spline((0.18, 0.30, 0.04), 0.35, CHEEK,
                    harmonics={5: (0.05, 0.07, 0.01)}))
    p.append(spline((-0.92, -0.94, -0.72), 0.58, NOSTRIL))

    # One zero-predictor leaf creates the black canvas. No raster source exists.
    return "\n".join(p) + "\n\n- Set 0\n"


if __name__ == "__main__":
    s = program()
    Path("snake.tree").write_text(s)
    print(f"wrote snake.tree ({len(s.encode())} source bytes)")
