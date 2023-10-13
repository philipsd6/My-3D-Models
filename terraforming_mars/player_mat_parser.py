#!/usr/bin/env python3
"""
This script extracts the values needed to create a minimal player mat for Terraforming Mars.

Based on the design of ChiDragon's https://www.thingiverse.com/thing:3581186, which in
turn is based on aimfeld's https://www.thingiverse.com/thing:2988374 which is what this
script uses as the source for the measurements.
"""

import statistics
from itertools import combinations
from pprint import pformat

from build123d import *
from ocp_vscode import *

# aimfeld models
source_files = dict(
    body_model="./files/aimfeld/player-mat-parts_-_body.stl",
    big_grid_model="./files/aimfeld/player-mat-parts_-_grid_big.stl",
    small_grid_model="./files/aimfeld/player-mat-parts_-_grid_small.stl",
)


def import_model(path):
    """Import an STL file and return the model(s) centered on x,y, with z=0.0"""
    importer = Mesher()
    models = importer.read(path)
    for model in models:
        c = model.center(CenterOf.BOUNDING_BOX)
        c.Z *= 2
        model.locate(Pos(-c))
        yield model


# The process_<obj> functions will take an imported model and reduce it to the essential
# form and yield it right away, then continue on and extract the necessary measurements
# and yield those as a dict for re-use.


def process_body(model):
    # The body has too many curves to be quickly merged, so we'll just focus on the
    # straight Axis faces.
    sk = (
        Sketch()
        + model.faces().filter_by(Axis.X)
        + model.faces().filter_by(Axis.Y)
        + model.faces().filter_by(Axis.Z)
    )
    yield sk

    grouped_by_z = sk.faces().group_by(Axis.Z)
    top = Sketch() + grouped_by_z[-1]
    bins = Sketch() + (grouped_by_z[1] + grouped_by_z[-2]).sort_by(SortBy.DISTANCE)[:-4]
    bottom = Sketch() + grouped_by_z[0]

    body_height = model.bounding_box().size.Z
    body_length = top.bounding_box().size.X

    # Since I'm essentially making up my own version of ChiDragon's minimal model, the
    # body_width is gooing to be trickier, and will take a few steps, starting with
    # getting the outlines of the bottom holes, sans the border around the whole bottom.
    bottom_inner_wires = bottom.wires().sort_by(SortBy.LENGTH)[:-1]

    # We'll grab the smallest of these which will be the hole over the TR icon, so we
    # can determine the corner radius of those inner holes.
    smallest_hole_wire_edges = bottom_inner_wires[0].edges()

    # The radius is the point of where the rounding starts, to where the outer edge
    # would be if there was no rounding.
    hole_corner_radius = (
        smallest_hole_wire_edges.filter_by(Axis.X)[-1].vertices().sort_by(Axis.X)[0].X
        - smallest_hole_wire_edges.filter_by(Axis.Y)[-1].vertices().sort_by(Axis.Y)[0].X
    )
    del smallest_hole_wire_edges  # we won't need this anymore.

    # Then we get the bounding boxes of those outlines
    bottom_inner_wires_bboxs = ShapeList(
        [wire.bounding_box() for wire in bottom_inner_wires]
    )
    # And then we can create rectangles from those bounding boxes and place them
    # correctly.
    bottom_rects = ShapeList(
        [
            Rectangle(bbox.size.X, bbox.size.Y).locate(Pos(bbox.center()))
            for bbox in bottom_inner_wires_bboxs
        ]
    )

    # The two inner holes are the smallest of the bunch by area.
    holes = ShapeList(list(bottom_rects.sort_by(SortBy.AREA))[:2])

    # Next two smallest happen to be the upper and lower middle holes, though there's
    # probably a better way to ensure we get them than this.
    t1, t2 = list(bottom_rects.sort_by(SortBy.AREA))[2:4]

    body_y_top = t2.edges().filter_by(Axis.X)[0].vertices()[0].Y
    body_y_bottom = t1.edges().filter_by(Axis.X)[-1].vertices()[0].Y
    body_width = body_y_top - body_y_bottom

    # Since we are creating a new body with different dimensions, we have to calculate
    # what the new center point will be to make sure the holes and bins we are measuring
    # on the original body are fixed to be in the appropriate place on the new body.
    body_center = Pos(
        (top.bounding_box().min.X + top.bounding_box().max.X) / 2,
        (body_y_top + body_y_bottom) / 2,
    )

    # These are all the same, but we get the median anyway. Why not!
    bin_depth = statistics.median(
        [face.length for face in bins.faces().filter_by(Axis.X)]
    )

    bin_z_faces = bins.faces().filter_by(Axis.Z).sort_by(SortBy.AREA)
    # The bins should all be the same length, but they vary in teensy ways.
    bin_length = statistics.median([face.length for face in bin_z_faces])

    # The heights however are consistent...
    small_bin_height = statistics.median([face.width for face in bin_z_faces][:-1])

    # The tall bin is just the last one, so no need to aggregate anything.
    large_bin_height = bin_z_faces[-1].width

    bin_lengths = [bin_length] * len(bin_z_faces)
    bin_heights = [small_bin_height] * (len(bin_z_faces) - 1) + [large_bin_height]
    bin_positions = [face.center() - body_center.position for face in bin_z_faces]

    yield {
        "long_side": body_length,
        "short_side": body_width,
        "height": body_height,
        "corner_radius": hole_corner_radius * 2,  # gotta make this up, but lgtm
        "hole_sizes": [(hole.width, hole.rectangle_height) for hole in holes],
        "hole_positions": [
            (pos.X, pos.Y)
            for pos in [hole.position - body_center.position for hole in holes]
        ],
        "hole_corner_radius": hole_corner_radius,
        "bin_sizes": list(zip(bin_lengths, bin_heights)),
        "bin_positions": [(pos.X, pos.Y) for pos in bin_positions],
        "bin_depth": bin_depth,
    }


def process_grid(model):
    # This model is small enough I can just stitch the whole thing together quickly and
    # work from that.
    sk = Sketch() + model.faces()
    yield (sk)

    grid_length, grid_width, grid_height = sk.bounding_box().size
    # There is a chamfer we'll need to calculate from the bottom to the top.

    top = sk.faces().sort_by(Axis.Z)[-1]
    bottom = sk.faces().sort_by(Axis.Z)[0]

    cells = (
        ShapeList(
            [
                Face.make_from_wires(cell)
                for cell in top.wires().sort_by(SortBy.LENGTH)[:-1]
            ]
        )
        .sort_by(SortBy.DISTANCE)
        .sort_by(Axis.X)
    )

    # Cells are preeeety much all dang close to the same size, so we'll just grab
    # the median.
    cell_size = statistics.median(
        [val for lw in [(cell.length, cell.width) for cell in cells] for val in lw]
    )

    # The grids are a perfect use case for GridLocations, although the last column
    # of cells is separated from the rest a bit. We'll figure that out as we go on.
    x_count = int(grid_length // cell_size)
    y_count = int(grid_width // cell_size)

    # Since the we want to compare the distances between the main cells and the
    # final column we grab them by y_count..
    first_column = Sketch() + cells[:y_count]
    second_column = Sketch() + cells[y_count : y_count * 2]

    x_cell_spacing = (
        second_column.bounding_box().min - first_column.bounding_box().max
    ).X

    # The y cell spacing is slightly different, so we need to calculate that from the
    # first two cells vertically
    first_cell, second_cell = cells.sort_by(Axis.Y).sort_by(Axis.X)[:2]
    y_cell_spacing = (second_cell.bounding_box().min - first_cell.bounding_box().max).Y

    # We'll need to treat the top as two separate areas for GridLocations, as that
    # last column is separated from the rest.
    left_grid_length = (cell_size + x_cell_spacing) * (x_count - 1) + x_cell_spacing
    right_grid_length = cell_size + x_cell_spacing * 2

    # Now we need the spacing, which is different for x and y
    x_spacing = cell_size + x_cell_spacing
    y_spacing = cell_size + y_cell_spacing

    yield {
        "long_side": grid_length,
        "short_side": grid_width,
        "height": grid_height,
        "left_area_long_side": left_grid_length,
        "right_area_long_side": right_grid_length,
        "bottom_offset": min([grid_length - bottom.length, grid_width - bottom.width]),
        "x_count": x_count,
        "y_count": y_count,
        "x_spacing": x_spacing,
        "y_spacing": y_spacing,
        "cell_size": cell_size,
    }


def round_data(data, precision=1):
    typ = type(data)
    try:
        return typ(round(data, precision))
    except TypeError:
        try:
            return typ({k: round_data(v, precision) for k, v in data.items()})
        except AttributeError:
            return typ([round_data(d, precision) for d in data])


def print_vars(vars, name=None):
    output = pformat(vars, width=88, sort_dicts=False, underscore_numbers=True)
    output = output[1:-1]  # strip off the first/last {}
    var_name = f"{name.lower().replace(' ', '_')}_vars"
    if name:
        print(f"# {name} Variables\n{var_name} = {{\n ", end="")
    else:
        print(f"vars = {{\n ", end="")
    print(f"{output}\n}}\n")


def print_all_vars():
    for name in ["Body", "Big Grid", "Small Grid"]:
        var_name = f"{name.lower().replace(' ', '_')}_vars"
        vars = round_data(globals()[var_name], precision=1)
        print_vars(vars, name=name)


body_model = next(import_model(source_files["body_model"]))
big_grid_model = next(import_model(source_files["big_grid_model"]))
small_grid_model = next(import_model(source_files["small_grid_model"]))

source_body, body_vars = list(process_body(body_model))
source_big_grid, big_grid_vars = list(process_grid(big_grid_model))
source_small_grid, small_grid_vars = list(process_grid(small_grid_model))

print_all_vars()
