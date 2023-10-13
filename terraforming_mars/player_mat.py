#!/usr/bin/env python3
"""
Build a minimal Terraforming Mars Player Mat from scratch, based on values extracted from
- https://www.thingiverse.com/thing:3581186 (ChiDragon)
- https://www.thingiverse.com/thing:2988374 (aimfeld)
"""

import copy
from build123d import *
from ocp_vscode import *

# Body Variables
body_vars = {
    "long_side": 213.3,
    "short_side": 60.5,
    "height": 3.0,
    "corner_radius": 2.0,
    "hole_sizes": [(19.0, 26.8), (120.5, 10.5)],
    "hole_positions": [(-91.0, 13.4), (42.2, 0.0)],
    "hole_corner_radius": 1.0,
    "bin_sizes": [
        (57.8, 19.5),
        (57.8, 19.5),
        (57.8, 19.5),
        (57.8, 19.5),
        (57.8, 19.5),
        (57.8, 28.8),
    ],
    "bin_positions": [
        (68.3, -18.0),
        (1.5, -18.0),
        (73.1, 18.0),
        (-66.8, -18.0),
        (12.9, 18.0),
        (-49.9, 13.3),
    ],
    "bin_depth": 2.6,
}

# Big Grid Variables
big_grid_vars = {
    "long_side": 57.8,
    "short_side": 28.8,
    "height": 2.4,
    "left_area_long_side": 47.4,
    "right_area_long_side": 10.2,
    "bottom_offset": 0.4,
    "x_count": 6,
    "y_count": 3,
    "x_spacing": 9.3,
    "y_spacing": 9.3,
    "cell_size": 8.4,
}

# Small Grid Variables
small_grid_vars = copy.copy(big_grid_vars)
small_grid_vars.update(
    {
        "short_side": 19.5,
        "y_count": 2,
    }
)


def make_body(
    long_side,
    short_side,
    height,
    corner_radius,
    hole_sizes,
    hole_positions,
    hole_corner_radius,
    bin_sizes,
    bin_positions,
    bin_depth,
):
    with BuildPart() as body:
        with BuildSketch() as sketch:
            base = RectangleRounded(long_side, short_side, radius=corner_radius)
            locs = Locations(*hole_positions)
            for size, loc in zip(hole_sizes, locs):
                with Locations(loc):
                    RectangleRounded(
                        *size, radius=hole_corner_radius, mode=Mode.SUBTRACT
                    )
        extrude(amount=height)
        hole_wires = (
            body.faces().sort_by(Axis.Z)[-1].wires().sort_by(SortBy.LENGTH)[:-1]
        )
        fillet(
            [edge for wire in [wire.edges() for wire in hole_wires] for edge in wire],
            radius=hole_corner_radius,
        )
        fillet(
            body.faces().sort_by(Axis.Z)[-1].wires().sort_by(SortBy.LENGTH)[-1].edges(),
            radius=corner_radius,
        )
        with BuildSketch(Plane.XY.offset(height)) as bins_sketch:
            locs = Locations(*bin_positions)
            for size, loc in zip(bin_sizes, locs):
                with Locations(loc):
                    Rectangle(*size)
        extrude(amount=-bin_depth, mode=Mode.SUBTRACT)
    return body.part


def make_grid(
    long_side,
    height,
    short_side,
    left_area_long_side,
    right_area_long_side,
    bottom_offset,
    x_count,
    y_count,
    x_spacing,
    y_spacing,
    cell_size,
):
    with BuildPart() as grid:
        with BuildSketch(Plane.XY.offset(height)) as top_sk:
            # Create the top face of the entire grid
            rect = Rectangle(long_side, short_side)
            # Get the lower left and upper right corners of the grid for use in creating the
            # inner grid areas
            lower_left = rect.vertices().sort_by(Axis.X)[0]
            upper_right = rect.vertices().sort_by(Axis.X)[-1]
            # We need to create the left and right areas just to use as location references
            # for the GridLocations below
            with Locations(lower_left):
                left_rect = Rectangle(
                    left_area_long_side, short_side, align=Align.MIN, mode=Mode.PRIVATE
                )
            with Locations(upper_right):
                right_rect = Rectangle(
                    right_area_long_side, short_side, align=Align.MAX, mode=Mode.PRIVATE
                )
            with Locations(left_rect.center()):
                with GridLocations(
                    x_spacing, y_spacing, x_count - 1, y_count
                ) as l_locs:
                    cells = Rectangle(cell_size, cell_size, mode=Mode.SUBTRACT)
            with Locations(right_rect.center()):
                with GridLocations(x_spacing, y_spacing, 1, y_count) as r_locs:
                    cells = Rectangle(cell_size, cell_size, mode=Mode.SUBTRACT)
        extrude(amount=-height)
        chamfer(
            grid.faces().sort_by(Axis.Z)[0].outer_wire().edges(),
            length=height - 0.1,
            length2=bottom_offset,
        )
    return grid.part


body = make_body(**body_vars)
grid_big = make_grid(**big_grid_vars)
grid_small = make_grid(**small_grid_vars)

body.label = "Body"
grid_big.label = "Big Grid"
grid_small.label = "Small Grid 1"

# show(body, grid_big, grid_small, names=["body", "big grid", "small grid"])

# Layout all the parts

# Leave the body in the center, and put three small grids on the -Y side, and the big
# grid + two small grids on the +Y side.
grids = [grid_big, grid_small]
for i in range(4):
    grid = copy.copy(grid_small)
    grid.label = f"Small Grid {i+2}"
    grids.append(grid)


x_locs = [
    body.bounding_box().min.X + small_grid_vars["long_side"] / 2,
    body.bounding_box().center().X,
    body.bounding_box().max.X - big_grid_vars["long_side"] / 2,
] * 2  # x val is same for upper and lower grids
y_locs = (
    [body.bounding_box().max.Y + small_grid_vars["short_side"]]
    + [
        body.bounding_box().max.Y
        + small_grid_vars["short_side"]
        + (big_grid_vars["short_side"] - small_grid_vars["short_side"]) / 2
    ]
    * 2  # The upper small grids placements need to be adjusted to match the short_side of the big grid.
    + [body.bounding_box().min.Y - small_grid_vars["short_side"]] * 3
)

locs = [Pos(x, y) for x, y in zip(x_locs, y_locs)]
for i, grid in enumerate(grids):
    grid.locate(locs[i])

show(body, grids, reset_camera=Camera.KEEP)

# Export the parts
exporter = Mesher()
exporter.add_shape(grids[-1])
# Export just one small grid for a test print
exporter.write("terraforming_mars_player_mat_small_grid.stl")
# Then export the the body and all the grids in one file
exporter.add_shape(body)
for grid in grids[:-1]:
    exporter.add_shape(grid)
exporter.write("terraforming_mars_player_mat_with_grids.stl")
