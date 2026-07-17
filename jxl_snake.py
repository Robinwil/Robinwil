#!/usr/bin/env python3
"""Generate a zero-residual JPEG XL art program for a serpentine image.

The Python does not rasterize the artwork. It emits a jxl_from_tree program:
- a tiny MA prediction tree generates the full background;
- native JPEG XL splines draw a coiled, banded snake;
- jxl_from_tree compiles that description directly into a JXL codestream.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

SIZE = 512


def compact(value: float) -> str:
    if value == 0:
        return "0"
    return f"{value:.6g}"


def spline(
    rgb: tuple[float, float, float],
    radius: float,
    points: Sequence[tuple[float, float]],
    *,
    rgb_harmonics: dict[int, tuple[float, float, float]] | None = None,
    radius_harmonics: dict[int, float] | None = None,
) -> str:
    """Return one native JXL spline declaration.

    Each of the four 32-value blocks is a 1-D DCT series along the curve:
    R, G, B, then blur radius/thickness. Sparse harmonics create a lot of
    visible banding/tapering while adding very little entropy to the file.
    """
    channels = [[0.0] * 32 for _ in range(4)]
    channels[0][0], channels[1][0], channels[2][0] = rgb
    channels[3][0] = radius

    for frequency, values in (rgb_harmonics or {}).items():
        channels[0][frequency] = values[0]
        channels[1][frequency] = values[1]
        channels[2][frequency] = values[2]
    for frequency, value in (radius_harmonics or {}).items():
        channels[3][frequency] = value

    coefficients = " ".join(compact(v) for block in channels for v in block)
    controls = " ".join(f"{compact(x)} {compact(y)}" for x, y in points)
    return f"Spline {coefficients} {controls} EndSpline"


# A long asymmetric S-curve. Repeated near-turns make the body read as a coil,
# while the final short segment rises into a head/neck silhouette.
BODY: tuple[tuple[float, float], ...] = (
    (42, 430),
    (82, 458),
    (138, 454),
    (190, 421),
    (225, 375),
    (214, 330),
    (166, 304),
    (111, 304),
    (72, 276),
    (73, 229),
    (117, 197),
    (178, 194),
    (229, 220),
    (276, 259),
    (329, 268),
    (379, 242),
    (410, 194),
    (413, 143),
    (394, 100),
    (414, 69),
    (455, 60),
)

# A near-identical inner path gives a crisp illuminated spine inside the broad
# body without storing any pixels.
INNER: tuple[tuple[float, float], ...] = tuple((x - 2, y - 3) for x, y in BODY)

# A forked tongue: two tiny red splines share the root and diverge at the tip.
TONGUE_A = ((454, 61), (478, 54), (494, 42))
TONGUE_B = ((454, 61), (478, 54), (496, 59))


def build_program() -> str:
    declarations = [
        f"Width {SIZE}",
        f"Height {SIZE}",
        "Bitdepth 8",
        "GroupShift 3",
        # Broad dark rim. Negative spline colours subtract from the procedural
        # background and make the silhouette remain legible across bright areas.
        spline(
            (-0.42, -0.48, -0.34),
            24,
            BODY,
            radius_harmonics={1: -7.5, 2: 2.5, 9: 1.8},
        ),
        # Main body. Sparse colour DCT coefficients generate scales/bands along
        # the complete snake at decoder time.
        spline(
            (0.12, 0.78, 0.18),
            17,
            BODY,
            rgb_harmonics={
                1: (0.04, 0.10, -0.02),
                5: (0.11, -0.16, 0.07),
                10: (-0.08, 0.12, -0.05),
                15: (0.05, -0.08, 0.04),
            },
            radius_harmonics={1: -5.5, 3: 1.8, 11: 1.1},
        ),
        # Thin golden-green highlight, itself modulated into repeating scales.
        spline(
            (0.18, 0.32, 0.035),
            5.2,
            INNER,
            rgb_harmonics={
                4: (0.07, 0.10, 0.015),
                8: (-0.05, -0.08, 0.01),
                16: (0.035, 0.06, -0.015),
            },
            radius_harmonics={7: 1.1, 14: -0.7},
        ),
        spline((0.92, 0.035, 0.02), 1.8, TONGUE_A),
        spline((0.92, 0.035, 0.02), 1.8, TONGUE_B),
    ]

    # The residual stream is forced to all zeroes by jxl_from_tree. This tiny
    # tree therefore *is* the background program. The three channels use
    # different self-feeding predictors. Their wraparound, gradients and
    # predictor-error feedback create a dense iridescent field from a few nodes.
    tree = """
if c > 1
  if y > 0
    if WGH > 2
      - AvgN+NW + 1
      - Weighted + 1
    - W + 5
  if c > 0
    if y > 0
      if WGH > 0
        - AvgN+NE - 1
        - Weighted + 0
      - W + 3
    if y > 0
      if WGH > 1
        - AvgN+NW + 1
        - Gradient + 0
      - W + 1
""".strip()

    return "\n".join(declarations) + "\n\n" + tree + "\n"


def main() -> None:
    program = build_program()
    output = Path("snake.tree")
    output.write_text(program, encoding="utf-8")
    print(f"wrote {output} ({len(program.encode('utf-8'))} source bytes)")


if __name__ == "__main__":
    main()
