#!/usr/bin/env python3
"""Generate a zero-residual JPEG XL art program for a serpentine image.

The Python does not rasterize the artwork. It emits a jxl_from_tree program:
- a tiny MA prediction tree generates the full background;
- native JPEG XL splines draw a coiled, banded snake;
- jxl_from_tree compiles that description directly into a JXL codestream.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

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


BODY: tuple[tuple[float, float], ...] = (
    (42, 430), (82, 458), (138, 454), (190, 421), (225, 375),
    (214, 330), (166, 304), (111, 304), (72, 276), (73, 229),
    (117, 197), (178, 194), (229, 220), (276, 259), (329, 268),
    (379, 242), (410, 194), (413, 143), (394, 100), (414, 69),
    (455, 60),
)
INNER: tuple[tuple[float, float], ...] = tuple((x - 2, y - 3) for x, y in BODY)
TONGUE_A = ((454, 61), (478, 54), (494, 42))
TONGUE_B = ((454, 61), (478, 54), (496, 59))


def build_program() -> str:
    declarations = [
        f"Width {SIZE}",
        f"Height {SIZE}",
        "Bitdepth 8",
        "GroupShift 3",
        spline(
            (-0.72, -0.78, -0.55),
            2.0,
            BODY,
            radius_harmonics={1: -0.30, 2: 0.16, 9: 0.10},
        ),
        spline(
            (0.20, 1.00, 0.25),
            1.40,
            BODY,
            rgb_harmonics={
                1: (0.08, 0.16, -0.03),
                5: (0.18, -0.28, 0.12),
                10: (-0.13, 0.21, -0.09),
                15: (0.09, -0.14, 0.07),
            },
            radius_harmonics={1: -0.22, 3: 0.13, 11: 0.08},
        ),
        spline(
            (0.34, 0.58, 0.07),
            0.55,
            INNER,
            rgb_harmonics={
                4: (0.13, 0.18, 0.03),
                8: (-0.09, -0.14, 0.02),
                16: (0.06, 0.10, -0.03),
            },
            radius_harmonics={7: 0.10, 14: -0.06},
        ),
        spline((1.0, 0.035, 0.02), 0.24, TONGUE_A),
        spline((1.0, 0.035, 0.02), 0.24, TONGUE_B),
    ]

    # The codestream still has a zero residual stream. A single prediction-tree
    # leaf supplies the neutral canvas; all visible geometry comes from native
    # JXL spline features rather than a raster input.
    tree = "- Set 0"
    return "\n".join(declarations) + "\n\n" + tree + "\n"


def main() -> None:
    program = build_program()
    output = Path("snake.tree")
    output.write_text(program, encoding="utf-8")
    print(f"wrote {output} ({len(program.encode('utf-8'))} source bytes)")


if __name__ == "__main__":
    main()
