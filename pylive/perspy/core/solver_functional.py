from typing import Tuple
import glm

from pylive.perspy.core.solver import (
    compute_orientation_from_two_vanishing_points
)


def orientation_from_one_vanishing_point(viewport, vp1, f, P)->Tuple[glm.mat4, glm.mat3]:
    ...

def orientation_from_two_vanishing_points(viewport, vp1, vp2, P)->Tuple[glm.mat4, glm.mat3]:
    ...

def orientation_from_three_vanishing_points(viewport, vp1, vp2, vp3)->Tuple[glm.mat4, glm.mat3]:
    ...

def adjust_position_to_origin(
        viewport, 
        projection_matrix:glm.mat4, 
        O:glm.vec2, 
        view_matrix:glm.mat4
    )->glm.mat4:
    ...

def adjust_scale_to_reference_distance(
        viewport, 
        projection_matrix:glm.mat4,
        reference_world_size:float, 
        reference_axis:ReferenceAxis,
        reference_distance_segment:Tuple[float, float],
        view_matrix:glm.mat4, 
    )->glm.mat4:
    ...

def adjust_axis_assignment(
        first_axis, 
        second_axis, 
        view_matrix:glm.mat4
    )->glm.mat4:
    ...