# standard library
from collections import namedtuple
from typing import List, Tuple, Literal, Final
from enum import IntEnum
import math
from dataclasses import dataclass
from textwrap import dedent
from abc import ABC, abstractmethod

# third party library
import glm
import numpy as np
from imgui_bundle import imgui
from pyparsing import Iterable # imgui for debugging
from pylive.perspy.demo import ui

import warnings

from . constants import (
    EPSILON, 
    DEFAULT_NEAR_PLANE, 
    DEFAULT_FAR_PLANE, 
    MAX_VANISHING_POINT_DISTANCE
)

from . utils import (
    Line2,
    Line3,
    Ray2,
    Ray3,
    Plane3
)

from . utils import (
    least_squares_intersection_of_lines,
    rotate_point_around_center,
    fov_from_focal_length,
    focal_length_from_fov,
    perspective_tiltshift,
    cast_ray,
    intersect_ray_with_plane,
    apply_gram_schmidt_orthogonalization,
    triangle_orthocenter,
    closest_point_between_lines,
    decompose_frustum, 
    decompose_perspective, 
    decompose_perspective_tiltshift
)

#########
# TYPES #
#########
class Axis(IntEnum):
    PositiveX = 0
    NegativeX = 1
    PositiveY = 2
    NegativeY = 3
    PositiveZ = 4
    NegativeZ = 5

class EulerOrder(IntEnum):
    XYZ = 0
    XZY = 1
    YZX = 2
    YXZ = 3
    ZXY = 4
    ZYX = 5

class ReferenceAxis(IntEnum):
    Screen = 0
    X_Axis = 1
    Y_Axis = 2
    Z_Axis = 3

class SolverMode(IntEnum):
    OneVP = 0
    TwoVP = 1
    ThreeVP = 2

@dataclass
class Rect:
    x: float
    y: float
    width: float
    height: float

    @property
    def size(self) -> glm.vec2:
        return glm.vec2(self.width, self.height)

    @property
    def center(self) -> glm.vec2:
        return glm.vec2(self.x + self.width / 2, self.y + self.height / 2)
    
    def __iter__(self):
        yield self.x
        yield self.y
        yield self.width
        yield self.height

@dataclass
class SolverResults:
    # initial parameters
    viewport: Rect

    # vanishing points
    first_vanishing_point: glm.vec2|None = None
    second_vanishing_point: glm.vec2|None = None
    third_vanishing_point: glm.vec2|None = None

    # projection
    projection: glm.mat4|None = None

    # transform
    view: glm.mat4|None = None   



    # @property
    # def principal_point(self)->glm.vec2|None:
    #     if self.projection is None:
    #         return None
    #     left, right, bottom, top, near, far = decompose_frustum(self.projection)
    #     Ppx = ((right + left) / (top - bottom)) * near
    #     Ppy = ((top + bottom) / (top - bottom)) * near
    #     P = glm.vec2(
    #         self.viewport.center.x - (Ppx / near) * (self.viewport.height / 2),
    #         self.viewport.center.y + (Ppy / near) * (self.viewport.height / 2)
    #     )
    #     return P

    principal_point: glm.vec2|None = None

    # orientation
    # orientation: glm.mat3|None = None

    # projection
    
    focal_length: float|None = None
    shift_x: float = 0.0
    shift_y: float = 0.0
    # near_plane: float = DEFAULT_NEAR_PLANE
    # far_plane: float = DEFAULT_FAR_PLANE

    # position
     
    # def get_projection(self)->glm.mat4|None:
    #     # Camera parameters

    #     top = self.near_plane * glm.tan(self.fovy / 2)
    #     bottom = -top
    #     right = top * self.aspect
    #     left = -right

    #     # Apply shifts
    #     width = right - left
    #     height = top - bottom

    #     left += self.shift_x * width / 2
    #     right += self.shift_x * width / 2
    #     bottom += self.shift_y * height / 2
    #     top += self.shift_y * height / 2

    #     # Create the projection matrix with lens shift
    #     return glm.frustum(left, right, bottom, top, self.near_plane, self.far_plane)
    
    # def get_fovx(self)->float:
    #     return 2.0 * math.atan(math.tan(self.fovy * 0.5) * self.aspect)

    # def get_position(self) -> glm.vec3|None:
    #     scale = glm.vec3()
    #     quat = glm.quat()  # This will be our quaternion
    #     translation = glm.vec3()
    #     skew = glm.vec3()
    #     perspective = glm.vec4()
    #     success = glm.decompose(self.transform, scale, quat, translation, skew, perspective)
    #     if not success:
    #         logger.error("Failed to decompose transformation matrix")
    #         return None
    #     return translation
    
    # def get_quaternion(self) -> glm.quat|None:
    #     scale = glm.vec3()
    #     quat = glm.quat()  # This will be our quaternion
    #     translation = glm.vec3()
    #     skew = glm.vec3()
    #     perspective = glm.vec4()
    #     success = glm.decompose(self.transform, scale, quat, translation, skew, perspective)
    #     if not success:
    #         logger.error("Failed to decompose transformation matrix")
    #         return None
    #     return quat

    def decompose_intrinsics(self)->Tuple[glm.vec2, float, glm.vec2]:
        """ Decomposes the projection matrix to retreive principal point, focal length and shift."""
        if self.projection is None:
            raise ValueError("Projection matrix is None, cannot decompose intrinsics.")
        
        left, right, top, bottom, near, far = decompose_frustum(self.projection)
        Ppx = ((right + left) / (top - bottom)) * near
        Ppy = ((top + bottom) / (top - bottom)) * near
        P = glm.vec2(
            self.viewport.center.x - (Ppx / near) * (self.viewport.height / 2),
            self.viewport.center.y + (Ppy / near) * (self.viewport.height / 2)
        )
        f = near/(bottom-top) * self.viewport.height
        shift = (P - self.viewport.center) / (self.viewport.size / 2.0)
        return P, f, shift
    
    def decompose_extrinsics(self)->Tuple[glm.vec3, glm.quat]:
        """ Decomposes the view matrix to retreive position, orientation and scale."""
        if self.view is None:
            raise ValueError("View matrix is None, cannot decompose extrinsics.")
        
        scale = glm.vec3()
        quat = glm.quat()  # This will be our quaternion
        translation = glm.vec3()
        skew = glm.vec3()
        perspective = glm.vec4()
        success = glm.decompose(self.view, scale, quat, translation, skew, perspective)
        if not success:
            raise ValueError("Failed to decompose view matrix.")
        return translation, quat

    # serialization
    def as_dict(self)->dict:
        position = self.get_position()
        quaternion = self.get_quaternion()
        projection = self.get_projection()
        return {
            "transform": np.array(self.transform).reshape(4,4).tolist(),
            "fovy": self.fovy,
            "position": tuple(position) if position else None,
            "quaternion": tuple(quaternion) if quaternion else None,
            "euler_order": EulerOrder.ZXY.name,
            "euler": tuple(self.get_euler(order=EulerOrder.ZXY)),
            "projection": np.array(projection).reshape(4,4).tolist() if projection is not None else None,
            "aspect": self.aspect,
            "near_plane": self.near_plane,
            "far_plane": self.far_plane,
            "shift_x": self.shift_x,
            "shift_y": self.shift_y
        }

    def as_blender_script(self, camera_name: str="VLCamera")-> str:
        """Generate a Blender Python script to recreate the camera setup."""
        from imgui_bundle import hello_imgui
        from pathlib import Path

        blender_template_path = hello_imgui.asset_file_full_path("blender_camera_factory_template.py")
        try:
            script = Path(blender_template_path).read_text()
        except Exception as e:
            warnings.warn(f"Failed to read Blender template: {e}")
            return "# Failed to read Blender template."

        fovx = 2.0 * math.degrees(math.atan(math.tan(math.radians(self.fovy) * 0.5) * self.aspect))
        script = script.replace("<CAMERA_FOV>", str(math.radians(max(fovx, self.fovy))))
        transform_list = [[v for v in row] for row in glm.transpose(self.transform)]
        script = script.replace("<CAMERA_TRANSFORM>", str(transform_list))
        script = script.replace("<CAMERA_NAME>", f"'{camera_name}'")
        return script

    def __str__(self)->str:
        from textwrap import dedent
        def pretty_matrix(value:np.array, separator:str='\t') -> str:
            """format a matrix nicely for printing"""
            text = np.array2string(
                value,
                precision=3,
                suppress_small=True,
                separator=separator,  # Use double space as separator
                prefix='',
                suffix='',
                formatter={'float_kind': lambda x: f"{'+' if np.sign(x)>=0 else '-'}{abs(x):.3f}"}  # Right-aligned with 8 characters width
            )
            
            text = text.replace('[', ' ').replace(']', '')
            text = dedent(text).strip()
            text = text.replace('+', ' ')
            return text
        
        transform_text = pretty_matrix(np.array(self.transform).reshape(4,4), separator=" ") if self.transform is not None else "N/A"
        position_text =  pretty_matrix(np.array(self.get_position()), separator=" ")
        quat_text =      pretty_matrix(np.array(self.get_quaternion()), separator=" ")
        euler_text =     pretty_matrix(np.array([math.degrees(radians) for radians in self.get_euler()]), separator=" ")

        projection_text = pretty_matrix(np.array(self.get_projection()).reshape(4,4), separator=" ") if self.get_projection() is not None else "N/A"

        return dedent(f"""Solver Results:\n
            transform:\n{transform_text}\n
            position:\n{position_text}\n
            quaternion:\n{quat_text}\n
            euler (degrees):\n{euler_text}\n
            projection:\n{projection_text}\n
            fovy: {math.degrees(self.fovy)}\n
            fovx: {math.degrees(self.get_fovx())}\n
            shift_x: {self.shift_x}\n
            shift_y: {self.shift_y}\n
        """)

#########################
# MAIN SOLVER FUNCTIONS #
#########################

def solve(*args, **kwargs)->SolverResults:
    return _solve_functional_impl(*args, **kwargs)

def _solve_imperative_impl(
        mode:SolverMode, 
        viewport: Rect,
        first_vanishing_lines: List[Tuple[glm.vec2, glm.vec2]],
        second_vanishing_lines: List[Tuple[glm.vec2, glm.vec2]],
        third_vanishing_lines: List[Tuple[glm.vec2, glm.vec2]],

        f:float, # focal length (in height units)
        P:glm.vec2,
        O:glm.vec2,

        reference_axis:ReferenceAxis,
        reference_distance_segment:Tuple[float, float], # 2D distance from origin to camera
        reference_world_size:float,

        first_axis:Axis,
        second_axis:Axis
    )->SolverResults:

    results:Final[SolverResults] = SolverResults(viewport)

    # 1. compute vanishing points
    vp1 = least_squares_intersection_of_lines(first_vanishing_lines)
    if mode in (SolverMode.TwoVP, SolverMode.ThreeVP):
        vp2 = least_squares_intersection_of_lines(second_vanishing_lines)
    else:
        vp2 = None
    if mode == SolverMode.ThreeVP:
        vp3 = least_squares_intersection_of_lines(third_vanishing_lines)
    else:
        vp3 = None

    # 2. compute intrinsics
    if mode == SolverMode.ThreeVP:
        P = triangle_orthocenter(vp1,vp2,vp3)

    if mode in (SolverMode.TwoVP, SolverMode.ThreeVP):
        f = compute_focal_length_from_vanishing_points(Fu=vp1,Fv=vp2,P=P)
        
    shift = (P - viewport.center) / (viewport.size / 2.0)
    projection = perspective_tiltshift(
        fov_from_focal_length(f, viewport.height), 
        viewport.width/viewport.height, 
        DEFAULT_NEAR_PLANE,
        DEFAULT_FAR_PLANE, 
        shift.x, 
        -shift.y # TODO: note the negation here to match unProject convention TODO: double check why? see roll matrix later.
    )

    # 3. compute orientation
    match mode:
        case SolverMode.OneVP:
            view_matrix:glm.mat4x4 = glm.mat4(compute_orientation_from_single_vanishing_point(
                Fu=vp1,
                P=P,
                f=f,
                horizon_direction=glm.vec2(1,0)
            ))
            # Adjust Camera Roll to match second vanishing line
            view_matrix:glm.mat4 = view_matrix * compute_roll_matrix(
                second_vanishing_lines[0], # Roll the camera based on the horizon line projected to 3D
                view_matrix,
                projection,
                viewport
            )

        case SolverMode.TwoVP:
            view_matrix:glm.mat4 = glm.mat4(compute_orientation_from_two_vanishing_points(
                Fu=vp1,
                Fv=vp2,
                P=P,
                f=f
            ))

        case SolverMode.ThreeVP:
            view_matrix:glm.mat4 = glm.mat4(compute_orientation_from_two_vanishing_points(
                Fu=vp1,
                Fv=vp2,
                P=P,
                f=f
            ))

    # 4. Adjust position
    ray = cast_ray(O, view_matrix, projection, tuple(viewport))
    camera_position = glm.normalize(ray[1] - glm.vec3(0,0,0))
    view_matrix = glm.translate(view_matrix, camera_position)


    # 5. Adjust axis assignment
    view_matrix = view_matrix * glm.mat4(create_axis_assignment_matrix(first_axis, second_axis))

    # 6. Adjust scale scene
    view_matrix = apply_reference_world_distance(
        reference_axis, 
        reference_distance_segment, 
        reference_world_size,
        view_matrix, 
        projection, 
        viewport
    )

    return SolverResults(
        # initial parameters
        viewport=viewport,

        # vanishing points
        first_vanishing_point=vp1,
        second_vanishing_point=vp2,
        third_vanishing_point=vp3,
        principal_point=P,

        # projection
        projection=projection,
        focal_length=f,
        shift_x=shift.x,
        shift_y=shift.y,
        near_plane=DEFAULT_NEAR_PLANE,
        far_plane=DEFAULT_FAR_PLANE,

        # position
        view = view_matrix
    )

def _solve_functional_impl(
        mode:SolverMode, 
        viewport: Rect,
        first_vanishing_lines: List[Tuple[glm.vec2, glm.vec2]],
        second_vanishing_lines: List[Tuple[glm.vec2, glm.vec2]],
        third_vanishing_lines: List[Tuple[glm.vec2, glm.vec2]],

        f:float, # focal length (in height units)
        P:glm.vec2,
        O:glm.vec2,

        reference_axis:ReferenceAxis,
        reference_distance_segment:Tuple[float, float], # 2D distance from origin to camera
        reference_world_size:float,

        first_axis:Axis,
        second_axis:Axis
    ):
    
    match mode:
        case SolverMode.OneVP:
            vp1 = least_squares_intersection_of_lines(first_vanishing_lines)
            vp2 = None
            vp3 = None
            projection, view = orientation_from_one_vanishing_point(
                viewport,
                vp1=vp1,
                second_line=second_vanishing_lines[0],
                f=f,
                P=P
            )

        case SolverMode.TwoVP:
            vp1 = least_squares_intersection_of_lines(first_vanishing_lines)
            vp2 = least_squares_intersection_of_lines(second_vanishing_lines)
            vp3 = None
            projection, view = orientation_from_two_vanishing_points(
                viewport,
                vp1=vp1,
                vp2=vp2,
                P=P
            )

        case SolverMode.ThreeVP:
            vp1 = least_squares_intersection_of_lines(first_vanishing_lines)
            vp2 = least_squares_intersection_of_lines(second_vanishing_lines)
            vp3 = least_squares_intersection_of_lines(third_vanishing_lines)

            projection, view = orientation_from_three_vanishing_points(
                viewport,
                vp1=vp1,
                vp2=vp2,
                vp3=vp3
            )

    view = adjust_position_to_origin(
        viewport, 
        projection, 
        O, 
        view
    )

    view = adjust_scale_to_reference_distance(
        viewport, 
        projection, 
        reference_world_size, 
        reference_axis, 
        reference_distance_segment, 
        view
    )

    view = adjust_axis_assignment(
        first_axis,
        second_axis,
        view
    )

    # retrive principal point from projection matrix
    # - TODO: refactor making, and decomposing projection matrices
    # - TODO: create a utility functions, to retreive xcamera instrinsic parameters from projection matrix, note, that currently, height and fovy are used to compute focal length
    left, right, top, bottom, near, far = decompose_frustum(projection)
    Ppx = ((right + left) / (top - bottom)) * near
    Ppy = ((top + bottom) / (top - bottom)) * near
    P = glm.vec2(
        viewport.center.x - (Ppx / near) * (viewport.height / 2),
        viewport.center.y + (Ppy / near) * (viewport.height / 2)
    )

    f = near/(bottom-top) * viewport.height
    shift = (P - viewport.center) / (viewport.size / 2.0)

    return SolverResults(
        # initial parameters
        viewport=viewport,

        # vanishing points
        first_vanishing_point =  vp1,
        second_vanishing_point = vp2,
        third_vanishing_point =  vp3,
        
        # projection
        projection =   projection,
        principal_point = P,
        focal_length = f,
        shift_x =      shift.x,
        shift_y =      shift.y,

        # position
        view = view
    )



def orientation_from_one_vanishing_point(viewport, vp1, second_line, f, P)->Tuple[glm.mat4, glm.mat3]:
    # compute projection
    shift = (P - viewport.center) / (viewport.size / 2.0)
    projection = perspective_tiltshift(
        fov_from_focal_length(f, viewport.height), 
        viewport.width/viewport.height, 
        DEFAULT_NEAR_PLANE,
        DEFAULT_FAR_PLANE, 
        shift.x, 
        -shift.y # TODO: note the negation here to match unProject convention TODO: double check why? see roll matrix later.
    )

    # compute orientation
    view_matrix:glm.mat4x4 = glm.mat4(compute_orientation_from_single_vanishing_point(
        Fu=vp1,
        P=P,
        f=f,
        horizon_direction=glm.vec2(1,0)
    ))

    # Adjust Camera Roll to match second vanishing line
    view_matrix:glm.mat4 = view_matrix * compute_roll_matrix(
        second_line, # Roll the camera based on the horizon line projected to 3D
        view_matrix,
        projection,
        viewport
    )

    return projection, view_matrix

def orientation_from_two_vanishing_points(viewport, vp1, vp2, P)->Tuple[glm.mat4, glm.mat3]:
    f = compute_focal_length_from_vanishing_points(Fu=vp1,Fv=vp2,P=P)

    # compute projection
    shift = (P - viewport.center) / (viewport.size / 2.0)
    projection = perspective_tiltshift(
        fov_from_focal_length(f, viewport.height), 
        viewport.width/viewport.height, 
        DEFAULT_NEAR_PLANE,
        DEFAULT_FAR_PLANE, 
        shift.x, 
        -shift.y # TODO: note the negation here to match unProject convention TODO: double check why? see roll matrix later.
    )

    # compute orientation
    view_matrix:glm.mat4 = glm.mat4(compute_orientation_from_two_vanishing_points(
        Fu=vp1,
        Fv=vp2,
        P=P,
        f=f
    ))

    return projection, view_matrix

def orientation_from_three_vanishing_points(viewport, vp1, vp2, vp3)->Tuple[glm.mat4, glm.mat3]:
    P = triangle_orthocenter(vp1,vp2,vp3)
    f = compute_focal_length_from_vanishing_points(Fu=vp1,Fv=vp2,P=P)

    # compute projection
    shift = (P - viewport.center) / (viewport.size / 2.0)
    projection = perspective_tiltshift(
        fov_from_focal_length(f, viewport.height), 
        viewport.width/viewport.height, 
        DEFAULT_NEAR_PLANE,
        DEFAULT_FAR_PLANE, 
        shift.x, 
        -shift.y # TODO: note the negation here to match unProject convention TODO: double check why? see roll matrix later.
    )

    # compute orientation
    view_matrix:glm.mat4 = glm.mat4(compute_orientation_from_two_vanishing_points(
        Fu=vp1,
        Fv=vp2,
        P=P,
        f=f
    ))

    return projection, view_matrix

def adjust_position_to_origin(
        viewport, 
        projection:glm.mat4, 
        O:glm.vec2, 
        view:glm.mat4
    )->glm.mat4:
    ray = cast_ray(O, view, projection, tuple(viewport))
    camera_position = glm.normalize(ray[1] - glm.vec3(0,0,0))
    view = glm.translate(view, camera_position)

    return view

def adjust_scale_to_reference_distance(
        viewport, 
        projection:glm.mat4,
        reference_world_size:float, 
        reference_axis:ReferenceAxis,
        reference_distance_segment:Tuple[float, float],
        view:glm.mat4, 
    )->glm.mat4:

    return apply_reference_world_distance(
        reference_axis, 
        reference_distance_segment, 
        reference_world_size,
        view, 
        projection, 
        viewport
    )

def adjust_axis_assignment(
        first_axis, 
        second_axis, 
        view_matrix:glm.mat4
    )->glm.mat4:
    return view_matrix * glm.mat4(create_axis_assignment_matrix(first_axis, second_axis))

def solve1vp(
        viewport: Rect,
        Fu: glm.vec2,
        second_vanishing_line: Tuple[glm.vec2, glm.vec2],

        f:float, # focal length (in width and height units)
        P:glm.vec2,
        O:glm.vec2,

        first_axis,
        second_axis,

        reference_axis:ReferenceAxis,
        reference_distance_segment:Tuple[float, float], # 2D distance from origin to camera
        reference_world_size:float
    )->SolverResults:
        """
        Solve camera orientation from a single vanishing point and focal length,
        and computes the camera position from the scene origin 'O'.
        
        params:
            width: image width in pixels
            height: image height in pixels
            Fu: first vanishing point in pixel coordinates
            second_vanishing_line: used to compute camera roll
            f: focal length in pixels
            P: principal point in pixel coordinates
            O: the scene origin in pixel coordinates
            first_axis: the world axis that the first vanishing point represents
            second_axis: the world axis that the second vanishing point represents
            scale: scene scale factor

        returns:
            the camera transformation matrix.
        """

        ##############################
        # COMPUTE Camera Orientation #
        ##############################
        view_matrix = glm.mat4(compute_orientation_from_single_vanishing_point(
            Fu,
            P,
            f
        ))

        ######################
        # COMPUTE Projection #
        ######################
        # compute lens shift from principal point
        shift = (viewport.center - P) / (viewport.size / 2)

        # construct projection matrix with lens shift
        projection_matrix = perspective_tiltshift(
            fov_from_focal_length(f, viewport.height), 
            viewport.width/viewport.height, 
            DEFAULT_NEAR_PLANE,
            DEFAULT_FAR_PLANE, 
            shift.x, 
            -shift.y # TODO: note the negation here to match unProject convention TODO: double check why? see roll matrix later.
        )

        ############################
        # 4. Apply Camera Position #
        ############################
        ray = cast_ray(O, view_matrix, projection_matrix, tuple(viewport))
        camera_position = glm.normalize(ray[1] - glm.vec3(0,0,0))
        view_matrix = glm.translate(view_matrix, camera_position)


        #####################
        # Apply Camera Roll #
        #####################
        view_matrix = compute_roll_matrix(
            second_vanishing_line, # Roll the camera based on the horizon line projected to 3D
            view_matrix,
            projection_matrix,
            viewport
        )

        ############################
        # Apply reference distance #
        ############################
        view_matrix = apply_reference_world_distance(
            reference_axis, 
            reference_distance_segment, 
            reference_world_size,
            view_matrix, 
            projection_matrix, 
            viewport
        )

        #########################
        # Apply axis assignment #
        #########################
        axis_assignment_matrix:glm.mat3 = create_axis_assignment_matrix(first_axis, second_axis)   
        view_matrix = view_matrix * glm.mat4(axis_assignment_matrix)

        return SolverResults(
            viewport=viewport,
            transform=glm.inverse(view_matrix) ,
            fovy=fov_from_focal_length(f, viewport.height),
            aspect=viewport.width/viewport.height,
            near_plane=DEFAULT_NEAR_PLANE,
            far_plane=DEFAULT_FAR_PLANE,
            shift_x=shift.x,
            shift_y=shift.y,
            principal_point=P
        )

def solve2vp(
        viewport: Rect,
        Fu: glm.vec2,
        Fv: glm.vec2,
        P: glm.vec2,
        O: glm.vec2,
        first_axis,
        second_axis,
        reference_distance_mode:ReferenceAxis,
        reference_distance_segment_screen:Tuple[float, float], # 2D distance from origin to camera
        reference_world_size:float, # referenmce worlds space size
    )->SolverResults:
    """ Solve camera intrinsics and orientation from 3 orthogonal vanishing points.
    returns (fovy in radians, camera_orientation_matrix, camera_position)
    """

    ########################
    # COMPUTE Focal Length #
    ########################
    f = compute_focal_length_from_vanishing_points(Fu=Fu,Fv=Fv,P=P)
    fovy = fov_from_focal_length(f, viewport.height)

    ##############################
    # COMPUTE Camera Orientation #
    ##############################
    view_matrix = glm.mat4(compute_orientation_from_two_vanishing_points(
        Fu=Fu,
        Fv=Fv,
        P=P,
        f=f
    ))

    #########################
    # 4. COMPUTE Projection #
    #########################
    # compute lens shift from principal point
    center_x = viewport.x + viewport.width / 2
    center_y = viewport.y + viewport.height / 2
    shift_x = -(P.x - center_x) / (viewport.width / 2)
    shift_y = (P.y - center_y) / (viewport.height / 2)

    # construct projection matrix with lens shift
    projection_matrix = perspective_tiltshift(
        fov_from_focal_length(f, viewport.height), 
        viewport.width/viewport.height, 
        DEFAULT_NEAR_PLANE,
        DEFAULT_FAR_PLANE, 
        shift_x, 
        -shift_y # TODO: note the negation here to match unProject convention TODO: double check why? see roll matrix later.
    )

    #########################
    # Apply Camera Position #
    #########################
    ray = cast_ray(O, view_matrix, projection_matrix, tuple(viewport))
    camera_position = glm.normalize(ray[1] - glm.vec3(0,0,0))
    view_matrix = glm.translate(view_matrix, camera_position)
    
    
    ############################
    # Apply reference distance #
    ############################
    view_matrix = apply_reference_world_distance(
        reference_distance_mode, 
        reference_distance_segment_screen, 
        reference_world_size,
        view_matrix, 
        projection_matrix, 
        viewport
    ) 

    #########################
    # Apply axis assignment #
    #########################
    axis_assignment_matrix:glm.mat3 = create_axis_assignment_matrix(first_axis, second_axis)   
    view_matrix = view_matrix * glm.mat4(axis_assignment_matrix)

    return SolverResults(
        viewport=viewport,
        transform=glm.inverse(view_matrix),
        fovy=fovy,
        aspect=viewport.width/viewport.height,
        near_plane=DEFAULT_NEAR_PLANE,
        far_plane=DEFAULT_FAR_PLANE,
        shift_x=shift_x,
        shift_y=shift_y,
        principal_point=P
    )

###########
# HELPERS #
###########
def second_vanishing_point_from_focal_length(
        Fu: glm.vec2, 
        f: float, 
        P: glm.vec2, 
        horizonDir: glm.vec2
    )->glm.vec2:
    """
    Computes the coordinates of the second vanishing point
    based on the first, a focal length, the center of projection and
    the desired horizon tilt angle. The equations here are derived from
    section 3.2 "Determining the focal length from a single image".

    @param Fu the first vanishing point in _image plane_ coordinates.
    @param f the relative focal length
    @param P the center of projection in _normalized image_ coordinates
    @param horizonDir The desired horizon direction
    """
    
    # find the second vanishing point
    # // TODO_ take principal point into account here
    if glm.distance(Fu, P) < EPSILON:
        raise ValueError("First vanishing point coincides with principal point, cannot compute second vanishing point.")

    Fu_P = Fu - P

    k = -(glm.dot(Fu_P, Fu_P) + f * f) / glm.dot(Fu_P, horizonDir)
    Fv = Fu_P + k * horizonDir + P

    return Fv

def compute_focal_length_from_vanishing_points(
        Fu: glm.vec2, # first vanishing point
        Fv: glm.vec2, # second vanishing point
        P: glm.vec2   # principal point
    )-> float:
    """
    Computes the focal length from two orthogonal vanishing points using the cross-ratio formula.
    Enhanced with numerical stability improvements for distant vanishing points.
    """
    # Check for degenerate cases
    Fu_Fv_distance = glm.distance(Fu, Fv)
    if Fu_Fv_distance < EPSILON:
        raise ValueError(f"Vanishing points are too close together: distance = {Fu_Fv_distance:.2e}")
    
    # Detect if vanishing points are very far away and need special handling
    max_reasonable_distance = MAX_VANISHING_POINT_DISTANCE # Configurable threshold
    Fu_distance = glm.distance(Fu, P)
    Fv_distance = glm.distance(Fv, P)
    
    # For very distant VPs, clamp them to reasonable bounds to prevent numerical issues
    if Fu_distance > max_reasonable_distance or Fv_distance > max_reasonable_distance:
        warnings.warn(f"Warning: Very distant vanishing points detected (Fu: {Fu_distance:.1f}, Fv: {Fv_distance:.1f})")
        
        # Clamp to reasonable distance while preserving direction
        if Fu_distance > max_reasonable_distance:
            direction = glm.normalize(Fu - P)
            Fu = P + direction * max_reasonable_distance
            
        if Fv_distance > max_reasonable_distance:
            direction = glm.normalize(Fv - P)
            Fv = P + direction * max_reasonable_distance

        warnings.warn(f"  Clamped vanishing points to Fu: {Fu}, Fv: {Fv}")
    
    # Use the standard cross-ratio formula with improved numerical precision
    horizon_vector = Fu - Fv
    horizon_direction = glm.normalize(horizon_vector)
    
    principal_to_fv = P - Fv
    projection_length = glm.dot(horizon_direction, principal_to_fv)
    projection_point = Fv + projection_length * horizon_direction
    
    # Use double precision for critical calculations
    distance_fv_to_proj = float(glm.distance(Fv, projection_point))
    distance_fu_to_proj = float(glm.distance(Fu, projection_point))
    distance_p_to_proj =  float(glm.distance(P, projection_point))
    
    focal_length_squared = distance_fv_to_proj * distance_fu_to_proj - distance_p_to_proj * distance_p_to_proj
    
    if focal_length_squared <= 0:
        vanishing_point_distance = glm.distance(Fu, Fv)
        angle_deg = math.degrees(math.acos(glm.clamp(
            glm.dot(glm.normalize(Fu - P), glm.normalize(Fv - P)), -1.0, 1.0
        )))
        
        raise ValueError(
            f"Invalid vanishing point configuration: cannot compute focal length.\n"
            f"  f² = {focal_length_squared:.6f} (must be > 0)\n"
            f"  Vanishing point separation: {vanishing_point_distance:.2f} pixels\n"
            f"  Angle between VP directions: {angle_deg:.1f}° (should be close to 90°)\n"
            f"  Distance Fu->projection: {distance_fu_to_proj:.2f}\n"
            f"  Distance Fv->projection: {distance_fv_to_proj:.2f}\n"
            f"  Distance P->projection: {distance_p_to_proj:.2f}\n"
            f"  Possible causes: VPs too close to principal point, VPs not orthogonal, or VPs collinear with principal point"
        )
    
    focal_length = math.sqrt(focal_length_squared)
    return focal_length

@warnings.deprecated("Use compute_focal_length_from_vanishing_points instead")
def _compute_focal_length_from_vanishing_points_simple(
        Fu: glm.vec2, # first vanishing point
        Fv: glm.vec2, # second vanishing point
        P: glm.vec2   # principal point
    )-> float:
    """
    Computes the focal length from two orthogonal vanishing points using the cross-ratio formula.
    
    The formula is derived from the constraint that orthogonal directions in 3D space
    project to vanishing points that satisfy: f² = |Fv_Puv| * |Fu_Puv| - |P_Puv|²
    where Puv is the orthogonal projection of P onto the line FuFv.
    
    Args:
        Fu: First vanishing point in pixel coordinates
        Fv: Second vanishing point in pixel coordinates  
        P: Principal point in pixel coordinates
        
    Returns:
        Focal length in pixels
        
    Raises:
        ValueError: If vanishing points are too close, collinear with principal point,
                   or configuration is otherwise invalid
    """
    # Check for degenerate cases
    Fu_Fv_distance = glm.distance(Fu, Fv)
    if Fu_Fv_distance < EPSILON:
        raise ValueError(f"Vanishing points are too close together: distance = {Fu_Fv_distance:.2e}")
    
    # Compute Puv: orthogonal projection of principal point P onto line segment Fu-Fv
    horizon_vector = Fu - Fv
    horizon_direction = glm.normalize(horizon_vector)
    
    # Vector from Fv to principal point
    principal_to_fv = P - Fv
    
    # Project onto horizon line
    projection_length = glm.dot(horizon_direction, principal_to_fv)
    projection_point = Fv + projection_length * horizon_direction
    
    # Compute distances for focal length formula
    # f² = |Fv_Puv| * |Fu_Puv| - |P_Puv|²
    distance_fv_to_proj = glm.distance(Fv, projection_point)
    distance_fu_to_proj = glm.distance(Fu, projection_point)
    distance_p_to_proj = glm.distance(P, projection_point)
    
    # Apply focal length formula
    focal_length_squared = distance_fv_to_proj * distance_fu_to_proj - distance_p_to_proj * distance_p_to_proj
    
    # Validate result
    if focal_length_squared <= 0:
        # Provide detailed diagnostic information
        vanishing_point_distance = glm.distance(Fu, Fv)
        angle_deg = math.degrees(math.acos(glm.clamp(
            glm.dot(glm.normalize(Fu - P), glm.normalize(Fv - P)), -1.0, 1.0
        )))
        
        raise ValueError(
            f"Invalid vanishing point configuration: cannot compute focal length.\n"
            f"  f² = {focal_length_squared:.6f} (must be > 0)\n"
            f"  Vanishing point separation: {vanishing_point_distance:.2f} pixels\n"
            f"  Angle between VP directions: {angle_deg:.1f}° (should be close to 90°)\n"
            f"  Distance Fu->projection: {distance_fu_to_proj:.2f}\n"
            f"  Distance Fv->projection: {distance_fv_to_proj:.2f}\n"
            f"  Distance P->projection: {distance_p_to_proj:.2f}\n"
            f"  Possible causes: VPs too close to principal point, VPs not orthogonal, or VPs collinear with principal point"
        )
    
    return math.sqrt(focal_length_squared)

#########################
# ORIENTATION FUNCTIONS #
#########################

def compute_orientation_from_single_vanishing_point(
        Fu:glm.vec2,
        P:glm.vec2,
        f:float,
        horizon_direction:glm.vec2
    ):
    """
    Computes the camera orientation matrix from a single vanishing point.
    """

    # Direction from principal point to vanishing point
    forward = glm.normalize( glm.vec3(Fu-P, -f))
    up =      glm.normalize( glm.cross(glm.vec3(horizon_direction, 0), forward))
    right =   glm.normalize( glm.cross(up, forward))

    #
    view_orientation_matrix = glm.mat3(forward, right, up)

    # validate if matrix is a purely rotational matrix
    determinant = glm.determinant(view_orientation_matrix)
    if math.fabs(determinant - 1) > EPSILON:
        view_orientation_matrix = apply_gram_schmidt_orthogonalization(view_orientation_matrix)
        warnings.warn(f'Warning: Invalid vanishing point configuration. Rotation determinant {determinant}\n'+"View orientation matrix was not orthogonal, applied Gram-Schmidt orthogonalization")
    
    return view_orientation_matrix

def compute_orientation_from_two_vanishing_points(
        Fu:glm.vec2, # first vanishing point
        Fv:glm.vec2, # second vanishing point
        P:glm.vec2,
        f:float
    )->glm.mat3:

    forward = glm.normalize(glm.vec3(Fu-P, -f))
    right =   glm.normalize(glm.vec3(Fv-P, -f))
    up =      glm.cross(forward, right)

    view_orientation_matrix = glm.mat3(forward, right, up)

    # validate if matrix is a purely rotational matrix
    determinant = glm.determinant(view_orientation_matrix)
    if math.fabs(determinant - 1) > EPSILON:
        view_orientation_matrix = apply_gram_schmidt_orthogonalization(view_orientation_matrix)
        warnings.warn(f'Warning: Invalid vanishing point configuration. Rotation determinant {determinant}\n'+"View orientation matrix was not orthogonal, applied Gram-Schmidt orthogonalization")

    return view_orientation_matrix

###########################
# ADJUST CAMERA FUNCTIONS #
###########################

def compute_roll_matrix(
        second_vanishing_line:Tuple[glm.vec2, glm.vec2],
        view_matrix:glm.mat4,
        projection_matrix:glm.mat4,
        viewport: Rect,
        first_axis:Axis=Axis.PositiveX, # TODO: are these needed?
        second_axis:Axis=Axis.PositiveY
)->glm.mat4:
    """
    Apply a roll correction matrix to the viewmatrix
    to align the horizon based on the second vanishing lines.
    """

    # Project the second vanishing line the forward plane in 3D world space
    A, B = second_vanishing_line

    # Unproject pixel coordinates to world space rays 
    A_ray = cast_ray(A, view_matrix, projection_matrix, tuple(viewport))
    B_ray = cast_ray(B, view_matrix, projection_matrix, tuple(viewport))

    # define the plane coordinate system (the plane facing against the camera screen, orineted by the first axis)
    view_origin = glm.vec3(view_matrix[3])
    forward = glm.normalize(glm.vec3(view_matrix[0][2], view_matrix[1][2], view_matrix[2][2]))

    plane_origin = view_origin + forward*0.01# glm.vec3(0, 0, 0) TODO: the computation is dependent on the plane position. Consider removeing this dependency from the algorithm.
    plane_normal = _axis_positive_vector(first_axis)
    plane_y_axis = glm.cross(plane_normal, _third_axis_vector(first_axis, second_axis)) # along the line
    plane_x_axis = glm.cross(plane_normal, plane_y_axis)  # perpendicular in the plane

    # Intersect rays with facing plane
    A_on_plane = intersect_ray_with_plane(A_ray, plane_origin, plane_normal)
    B_on_plane = intersect_ray_with_plane(B_ray, plane_origin, plane_normal)

    v = B_on_plane - A_on_plane # vector along the line on the plane
    v_proj = v - glm.dot(v, plane_normal) * plane_normal # project vector onto plane

    # --- Compute 360° angle using atan2 ---
    x_on_plane = glm.dot(v_proj, plane_y_axis)
    y_on_plane = glm.dot(v_proj, plane_x_axis)
    angle = angle = math.atan(y_on_plane / x_on_plane)
    
    roll_axis = plane_normal # plane normal
    roll_matrix = glm.rotate(glm.mat4(1.0), angle, roll_axis)
    return roll_matrix

def apply_reference_world_distance(
        reference_axis:ReferenceAxis, 
        reference_screen_length_segment:Tuple[float, float], # 2D distance on the specidied reference axis. Optionally use a tuple for a segment (start, end)
        reference_world_size:float,
        view_matrix, 
        projection_matrix, 
        viewport
    ):

    """ Calculate the world distance from origin based on the reference distance mode and value."""
    match reference_axis:
        case ReferenceAxis.X_Axis:
            reference_axis = glm.vec3(1, 0, 0)
        case ReferenceAxis.Y_Axis:
            reference_axis = glm.vec3(0, 1, 0)
        case ReferenceAxis.Z_Axis:
            reference_axis = glm.vec3(0, 0, 1)
        case ReferenceAxis.Screen | _:
            # use camera right vector as reference axis
            right = glm.mat3(glm.inverse(view_matrix))[0]   # right vector is +X in view space
            reference_axis = right

    O_screen = glm.project(
        glm.vec3(0, 0, 0), 
        view_matrix, 
        projection_matrix, 
        tuple(viewport)).xy
    
    V_screen = glm.project(reference_axis, view_matrix, projection_matrix, tuple(viewport)).xy
    dir_screen = glm.normalize(glm.vec2(V_screen.x - O_screen.x, V_screen.y - O_screen.y))

    reference_offset, reference_length = reference_screen_length_segment
    reference_line: Line3 = (glm.vec3(0,0,0), reference_axis)

    reference_start_point_screen = O_screen + dir_screen * reference_offset
    reference_start_ray = cast_ray(reference_start_point_screen, view_matrix, projection_matrix, tuple(viewport))
    reference_start_point_world = closest_point_between_lines(
        reference_line, 
        reference_start_ray
    )

    reference_end_point_screen = O_screen + dir_screen * (reference_offset + reference_length)
    reference_end_ray = cast_ray(reference_end_point_screen, view_matrix, projection_matrix, tuple(viewport))

    reference_end_point_world = closest_point_between_lines(
        reference_line, 
        reference_end_ray
    )

    reference_world_length = glm.distance(reference_start_point_world, reference_end_point_world)

    # apply to view matrix
    view_matrix = glm.mat4(view_matrix) # make a copy
    view_position = glm.vec3(view_matrix[3])
    view_matrix[3] = glm.vec4(view_position/reference_world_length*reference_world_size, 1.0)
    return view_matrix

def create_axis_assignment_matrix(first_axis: Axis, second_axis: Axis) -> glm.mat3:
    """
    Creates an axis assignment matrix that maps vanishing point directions to user-specified world axes.
    
    Args:
        firstVanishingPointAxis: The world axis that the first vanishing point should represent
        secondVanishingPointAxis: The world axis that the second vanishing point should represent
    
    Returns:
        A 3x3 rotation matrix that transforms from vanishing point space to world space
    
    Raises:
        Exception: If the axis assignment creates an invalid (non-orthogonal) matrix

    Note:
        Identity if:
        - if First vanishing point naturally points along the world's +X direction
        - Second vanishing point naturally points along the world's +Y direction
        - Third direction (computed via cross product) naturally points along the world's +Z direction
    """
    
    # Get the unit vectors for the specified axes
    forward = _axis_vector(first_axis)
    right = _axis_vector(second_axis)
    up = glm.cross(forward, right)
    
    # Build the matrix with each row representing the target world axis
    axis_assignment_matrix = glm.mat3( # TODO: this is the inverse of the mat3_from_directions
        forward.x,
        forward.y,
        forward.z,
        right.x,
        right.y,
        right.z,
        up.x,
        up.y,
        up.z
    )
    
    # Validate that we have a proper orthogonal matrix
    assert math.fabs(1 - glm.determinant(axis_assignment_matrix)) < EPSILON, "Invalid axis assignment: axes must be orthogonal"
    return axis_assignment_matrix

def flip_coordinate_handness(mat: glm.mat4) -> glm.mat4:
    """swap left-right handed coordinate system"""
    flipZ = glm.scale(glm.vec3(1.0, 1.0, -1.0))
    return flipZ * mat # todo: check order


#####################
# UTILITY FUNCTIONS #
#####################
def _axis_vector(axis: Axis)->glm.vec3:
    match axis:
      case Axis.NegativeX:
        return glm.vec3(-1, 0, 0)
      case Axis.PositiveX:
        return glm.vec3(1, 0, 0)
      case Axis.NegativeY:
        return glm.vec3(0, -1, 0)
      case Axis.PositiveY:
        return glm.vec3(0, 1, 0)
      case Axis.NegativeZ:
        return glm.vec3(0, 0, -1)
      case Axis.PositiveZ:
        return glm.vec3(0, 0, 1)

def _axis_positive_vector(axis)->glm.vec3:
    match axis:
        case Axis.PositiveX | Axis.NegativeX:
            return glm.vec3(1, 0, 0)
        case Axis.PositiveY | Axis.NegativeY:
            return glm.vec3(0, -1, 0)
        case Axis.PositiveZ | Axis.NegativeZ:
            return glm.vec3(0, 0, 1)
        
def _third_axis_vector(axis1:Axis, axis2:Axis)->glm.vec3:
    vec1 = _axis_vector(axis1)
    vec2 = _axis_vector(axis2)
    return glm.normalize(glm.cross(vec1, vec2))

def _vectorAxis(vector: glm.vec3)->Axis:
    if vector.x == 0 and vector.y == 0:
      return Axis.PositiveZ if vector.z > 0 else Axis.NegativeZ
    elif vector.x == 0 and vector.z == 0:
      return Axis.PositiveY if vector.y > 0 else Axis.NegativeY
    elif vector.y == 0 and vector.z == 0:
      return Axis.PositiveX if vector.x > 0 else Axis.NegativeX
    
    raise ValueError('Invalid axis vector')

def adjust_vanishing_lines(
        old_vp:glm.vec2, 
        new_vp:glm.vec2, 
        vanishing_lines:List[Tuple[glm.vec2, glm.vec2]]
    ) -> List[Tuple[glm.vec2, glm.vec2]]:
    # When vanishing point moves, adjust only the closest endpoint of each vanishing line
    new_vanishing_lines = vanishing_lines.copy()
    for i, (P, Q) in enumerate(vanishing_lines):
        # Find which endpoint is closer to the old vanishing point
        dist_P = glm.length(P - old_vp)
        dist_Q = glm.length(Q - old_vp)
        
        # Choose the closer endpoint and the fixed endpoint
        if dist_P < dist_Q:
            moving_point, fixed_point = P, Q
        else:
            moving_point, fixed_point = Q, P
        
        # Calculate relative position and apply to new vanishing point
        line_to_old_vp = old_vp - fixed_point
        line_to_moving = moving_point - fixed_point
        
        if glm.length(line_to_old_vp) > EPSILON:
            ratio = glm.length(line_to_moving) / glm.length(line_to_old_vp)
            new_line_to_vp = new_vp - fixed_point
            new_moving_point = fixed_point + glm.normalize(new_line_to_vp) * glm.length(new_line_to_vp) * ratio
            
            # Update the correct endpoint
            if dist_P < dist_Q:
                new_vanishing_lines[i] = (new_moving_point, Q)
            else:
                new_vanishing_lines[i] = (P, new_moving_point)
    return new_vanishing_lines

def adjust_vanishing_lines_by_rotation(
        old_vp: glm.vec2, 
        new_vp: glm.vec2, 
        vanishing_lines: List[Tuple[glm.vec2, glm.vec2]],
        principal_point: glm.vec2
    ) -> List[Tuple[glm.vec2, glm.vec2]]:
    """
    Adjust vanishing lines by rotating them around the principal point so they point to the new vanishing point.
    """
    
    # Apply the same rotation to all line endpoints
    new_vanishing_lines = []
    for P, Q in vanishing_lines:
        # Calculate the global rotation from old VP to new VP (relative to principal point)
        old_dir = glm.normalize(old_vp - P)
        new_dir = glm.normalize(new_vp - P)
        
        # Calculate rotation angle
        dot_product = glm.dot(old_dir, new_dir)
        dot_product = max(-1.0, min(1.0, dot_product))  # Clamp to avoid numerical errors
        rotation_angle = math.acos(dot_product)
        
        # Determine rotation direction using cross product (in 2D, this gives the z-component)
        cross_z = old_dir.x * new_dir.y - old_dir.y * new_dir.x
        if cross_z < 0:
            rotation_angle = -rotation_angle
        new_P = rotate_point_around_center(P, principal_point, rotation_angle)
        new_Q = rotate_point_around_center(Q, principal_point, rotation_angle)
        new_vanishing_lines.append((new_P, new_Q))
    
    return new_vanishing_lines

def calc_vanishing_points_from_camera(
        view_matrix: glm.mat3, 
        projection_matrix: glm.mat4, 
        viewport: Rect
    ) -> Tuple[glm.vec2, glm.vec2, glm.vec2]:
    """
    Calculate the projected vanishing points from the camera matrices.
    """
    
    # Project vanishing Points
    MAX_FLOAT32 = (2 - 2**-23) * 2**127
    VPX = glm.project(glm.vec3(MAX_FLOAT32,0,0), view_matrix, projection_matrix, viewport)
    VPY = glm.project(glm.vec3(0,MAX_FLOAT32,0), view_matrix, projection_matrix, viewport)
    VPZ = glm.project(glm.vec3(0,0,MAX_FLOAT32), view_matrix, projection_matrix, viewport)

    return glm.vec2(VPX), glm.vec2( VPY), glm.vec2(VPZ)


