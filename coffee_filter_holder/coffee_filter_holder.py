#!/usr/bin/env python3
"""
This is a holder for Hario V60 coffee filters. With the given parameters, it's most
suitable for the 03 size filters, but can also hold 02 size filters as well. It works
well when installed inside a cupboard door with a command strip or other adhesive.
"""

import inspect
from build123d import *
from ocp_vscode import *

filter_chord = 210 * MM  # corner to corner at the top of the large filter
wall_thickness = 2 * MM
inside_depth = 30 * MM
height = 45 * MM
top_width = 180 * MM
bottom_width = (top_width / 2 - height) * 2

src_file_path = inspect.getfile(lambda: None)
hario_logo = Path.joinpath(Path(src_file_path).parent, "hario-logo.svg")

# These corners define the corners of the trapezoid.
corners = [
    (-top_width / 2, height / 2),  # top left
    (top_width / 2, height / 2),  # top right
    (bottom_width / 2, -height / 2),  # bottom right
    (-bottom_width / 2, -height / 2),  # bottom left
]
# As the top and bottom will be curvy, these lists define the corners and control points
# necessary to create the desired Bezier curves.
top_pts = [corners[0], (height * 1 / 3, height), (0, 0), corners[1]]
bottom_pts = [
    corners[3],
    (0, -height * 1 / 4),
    (height * 1 / 3, -height * 3 / 4),
    corners[2],
]

with BuildPart() as filter_holder:
    with BuildSketch() as back_sketch:
        with BuildLine() as back_line:
            l0 = Bezier(*top_pts)
            l1 = Line(corners[1], corners[2])
            l2 = Bezier(*bottom_pts)
            l3 = Line(corners[3], corners[0])
        make_face()
    # Add a flipped copy of the back sketch and loft between them
    add(back_sketch.face().offset(inside_depth).rotate(Axis.Y, 180))
    loft()

    # Insert a "coffee filter" shape to cut out the inside
    with BuildSketch(Plane.XY.offset(-wall_thickness)) as inside_sketch:
        with BuildLine() as filter_line:
            corners = [
                (
                    -filter_chord / 2,
                    -top_width / 2 + height / 2 + filter_chord / 2,
                ),  # top left
                (0, -top_width / 2 + height / 2),  # bottom_point
                (
                    filter_chord / 2,
                    -top_width / 2 + height / 2 + filter_chord / 2,
                ),  # top right
            ]
            # corners.append(corners[0])
            corners = [(x, y + wall_thickness * 2 ** (1 / 2)) for x, y in corners]
            l0 = Polyline(*corners)
            l1 = ThreePointArc(corners[0], (0, corners[0][-1] + 35 * MM), corners[-1])
        make_face()
    filter_block = extrude(
        amount=-inside_depth + wall_thickness * 2, mode=Mode.SUBTRACT
    )

    # Add the Hario logo to the front
    logo_svg = import_svg(hario_logo)
    with BuildSketch() as logo_sketch:
        add(logo_svg.faces())
        scale(by=1 / 4)  # original is way too big...
    extrude(amount=-wall_thickness / 2, mode=Mode.SUBTRACT)

# Display the part in the GUI as it would be used with filters
filter_holder.label = "filter-holder"
filter_block.label = "filters"

show(
    filter_holder,
    filter_block,
    colors=["goldenrod", "silver"],
    reset_camera=Camera.KEEP,
)

# Export the STL for printing
filter_holder.part.export_stl("coffee-filter-holder.stl")
