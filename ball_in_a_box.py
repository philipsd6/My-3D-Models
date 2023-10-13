#!/usr/bin/env python3
"""
Build the classic ball-in-a-box puzzle, parametrically in build123d style!
"""

import copy
from build123d import *
from ocp_vscode import *

box_size = 2 * CM  # Change this one parameter to change the whole model!
ball_radius = box_size / 2
space_radius = ball_radius * 1.25

with BuildPart() as ball_in_box:
    box = Box(*[box_size] * 3)
    gap = Sphere(space_radius, mode=Mode.SUBTRACT)
    sphere = Sphere(ball_radius)

# Display the model in the VSCode 3D viewer
show(ball_in_box, reset_camera=Camera.KEEP)

# Export an STL file for 3D printing
exporter = Mesher()
exporter.add_shape(ball_in_box.part)
exporter.write("ball-in-box.stl")
