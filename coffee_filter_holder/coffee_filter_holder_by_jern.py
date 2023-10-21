#!/usr/bin/env python3
"""
This is Jern's version, which is much simpler than mine, and neater, but doesn't include my curvy design elements.
"""

from build123d import *
from ocp_vscode import *

filter_rad = 148.4924240491749
inside_depth = 30 * MM
outside_depth = inside_depth + 4
ms = Mode.SUBTRACT

with BuildSketch() as s_filter:
    with BuildLine() as l:  # Plane((0,-65))
        m1 = PolarLine((0, 0), filter_rad, 45)
        m3 = RadiusArc((0, filter_rad), m1 @ 1, filter_rad)
        # sagitta is a bit different but not relevant to this model
        mirror(about=Plane.YZ)
    make_face()

with BuildPart() as p:
    ofs = offset(s_filter.sketch, amount=2)
    extrude(amount=outside_depth / 2, both=True)
    # replace splits with nicer cuts (how??)
    split(bisect_by=Plane.XZ.offset(-50), keep=Keep.BOTTOM)
    split(bisect_by=Plane.XZ.offset(-80), keep=Keep.TOP)
    add(s_filter.sketch)
    extrude(amount=inside_depth / 2, both=True, mode=ms)

s_filter.label = "filter"
p.label = "filter-holder"

show(p, s_filter)
