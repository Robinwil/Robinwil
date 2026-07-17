#!/usr/bin/env python3
"""Design a tiny native JPEG XL artwork: a snake head with a coiled body.

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


# The body leads the eye toward a large head at upper right.
BODY = (
    (52, 438), (104, 462), (164, 448), (206, 407), (216, 356),
    (188, 318), (132, 300), (84, 270), (82, 222), (124, 188),
    (184, 188), (238, 218), (286, 254), (338, 258), (379, 229),
    (399, 188), (403, 151),
)
BODY_HI = tuple((x - 3, y - 3) for x, y in BODY)

# Shorter paths can use wider Gaussian splines without exceeding decoder limits.
# Together these make a viper-like wedge, jaw and raised brow.
HEAD_CORE = ((402, 153), (414, 126), (438, 104), (465, 91), (486, 94))
HEAD_TOP = ((407, 146), (428, 112), (459, 91), (488, 94))
HEAD_LOW = ((406, 154), (431, 145), (461, 130), (487, 101))
BROW = ((438, 108), (456, 99), (474, 98))
JAW = ((431, 137), (458, 132), (484, 108))
EYE_GLOW = ((455, 105), (459, 104))
EYE_PUPIL = ((458, 104), (461, 103))
TONGUE_A = ((486, 99), (499, 91), (508, 79))
TONGUE_B = ((486, 99), (500, 92), (510, 101))


def program() -> str:
    p = [
        f"Width {W}", f"Height {H}", "Bitdepth 8", "GroupShift 3",

        # Coiled body: dark rim, green fill, then an oscillating highlight.
        spline((-0.62, -0.70, -0.48), 2.0, BODY,
               sigma_h={1: -0.24, 4: 0.10}),
        spline((0.15, 0.92, 0.18), 1.35, BODY,
               harmonics={3: (0.12, -0.19, 0.08),
                          7: (-0.10, 0.17, -0.07),
                          13: (0.07, -0.12, 0.05),
                          21: (-0.05, 0.09, -0.04)},
               sigma_h={2: -0.15, 9: 0.07}),
        spline((0.30, 0.54, 0.06), 0.52, BODY_HI,
               harmonics={6: (0.12, 0.15, 0.02),
                          12: (-0.08, -0.11, 0.02),
                          24: (0.05, 0.08, -0.02)}),

        # Distinct head silhouette. The short under-stroke gives a broad wedge.
        spline((-0.86, -0.90, -0.68), 6.2, HEAD_CORE,
               sigma_h={1: -1.1, 2: 0.35}),
        spline((0.18, 1.08, 0.22), 4.7, HEAD_CORE,
               harmonics={2: (0.10, 0.18, -0.03),
                          5: (0.16, -0.20, 0.08),
                          9: (-0.10, 0.15, -0.06)},
               sigma_h={1: -0.65, 4: 0.24}),

        # Upper skull and lower cheek create a triangular/viper profile.
        spline((0.26, 0.72, 0.08), 2.2, HEAD_TOP,
               harmonics={4: (0.11, 0.14, 0.02)}),
        spline((0.10, 0.48, 0.05), 2.0, HEAD_LOW),
        spline((0.46, 0.72, 0.10), 1.0, BROW),

        # Face cues: jaw, bright eye, dark slit pupil, forked tongue.
        spline((-0.32, -0.38, -0.20), 0.42, JAW),
        spline((1.20, 0.95, 0.12), 0.75, EYE_GLOW),
        spline((-0.95, -0.95, -0.70), 0.24, EYE_PUPIL),
        spline((1.10, 0.03, 0.02), 0.28, TONGUE_A),
        spline((1.10, 0.03, 0.02), 0.28, TONGUE_B),
    ]

    # A single zero-predictor leaf makes the canvas. No source pixels exist.
    return "\n".join(p) + "\n\n- Set 0\n"


if __name__ == "__main__":
    s = program()
    Path("snake.tree").write_text(s)
    print(f"wrote snake.tree ({len(s.encode())} source bytes)")
