from . solver import *
from abc import ABC, abstractmethod
from typing import Tuple, Self, List
from . solver import *


class Solver(ABC):
    viewport: Rect
    first_vanishing_lines: List[Tuple[glm.vec2, glm.vec2]]

    first_axis: Axis
    second_axis: Axis

    O: glm.vec2

    reference_axis: ReferenceAxis
    reference_distance_segment: Tuple[float, float]  # 2D distance from origin to camera
    reference_world_size: float

    # results
    vanishing_points: List[glm.vec2]
    view: glm.mat4
    projection: glm.mat4
    shift_x: float
    shift_y: float

    def set_viewport(self, viewport:Rect)->Self:
        self.viewport = viewport
        return self
    
    def set_axes(self, first_axis:Axis, second_axis:Axis)->Self:
        self.first_axis = first_axis
        self.second_axis = second_axis
        return self
    
    def set_origin(self, O:glm.vec2)->Self:
        self.O = O
        return self

    @abstractmethod
    def solve(self) -> Dict:
        pass


class OneVPSolver(Solver):
    f: float  # focal length (in height units)
    roll_line: Tuple[glm.vec2, glm.vec2]
    principal: glm.vec2|None

    def set_focal_length(self, f:float)->Self:
        self.f = f
        return self

    def set_roll_line(self, roll_line:Tuple[glm.vec2, glm.vec2])->Self:
        self.roll_line = roll_line
        return self
    
    def set_principal(self, principal:glm.vec2)->Self:
        self.principal = principal
        return self

    def solve(self):
        vp1 = least_squares_intersection_of_lines(self.first_vanishing_lines)


class TwoVPSolver(Solver):
    second_vanishing_lines: List[Tuple[glm.vec2, glm.vec2]]
    principal: glm.vec2|None

    def set_principal(self, principal:glm.vec2)->Self:
        self.principal = principal
        return self
    
    def solve(self):
        return super().solve()


class ThreeVPSolver(Solver):
    third_vanishing_lines: List[Tuple[glm.vec2, glm.vec2]]

    def solve(self):
        return super().solve()
    

class MultiSolverBuilder(Solver):
    def __init__(self):
        self.viewport: Rect|None = None
        self.vanishing_lines:  List[List[Tuple[glm.vec2, glm.vec2]]] = []

        self.roll_line: Tuple[glm.vec2, glm.vec2]|None = None

        self.vanishing_points: List[glm.vec2] = []

        self.principal_point: glm.vec2|None = None # None means center of viewport

        self.focal_length: float|None = None # in viewport height units

        self.origin: glm.vec2|None = None # None means center of viewport

        self.first_axis: Axis = Axis.PositiveX
        self.second_axis: Axis = Axis.PositiveY

        self.reference_axis: ReferenceAxis|None = None # None means scale by camera distance
        self.reference_distance_segment: Tuple[float, float]|None = None
        self.reference_world_size: float|None = None

    def set_viewport(self, x, y, w, h)->Self:
        self.viewport = Rect(x,y,w,h)
        return self
    
    def use_vanishing_lines(self, 
        first:List[Tuple[glm.vec2, glm.vec2]], 
        second:List[Tuple[glm.vec2, glm.vec2]]|None=None, 
        third:List[Tuple[glm.vec2, glm.vec2]]|None=None
    ) ->Self:
        """set the vanishing lines to be used.
        at least one set of vanishing lines must be provided.
        up to three sets of vanishing lines can be provided.
        """

        self.vanishing_lines = [first]

        if second is not None:
            self.vanishing_lines.append(second)

        if third is not None:
            self.vanishing_lines.append(third)

        return self
    
    def set_roll_line(self, roll_line:Tuple[glm.vec2, glm.vec2]) ->Self:
        """Optional
        set the second vanishing line to compute camera roll when using a single vanishing point.
        """
        self.roll_line = roll_line
        return self
    
    def set_principal_point(self, x:float, y:float) ->Self:
        """set the principal point in 2D
        by default the principal point is at middle of the viewport"""
        self.principal_point = glm.vec2(x,y)
        return self
    
    def set_focal_length(self, f:float) ->Self:
        """set the focal length.
        only when a single vanishing point is used.
        this has no effect when multiple vanishing points are used.
        note that _f_ is expressed in viewport height units
        """
        self.focal_length = f
        return self
    
    def set_origin(self, x:float, y:float) ->Self:
        """set the origin point in 2D
        by default the origin is at middle of the viewport
        """
        self.origin = glm.vec2(x,y)
        return self
    
    def set_axes(self, first_axis:Axis, second_axis:Axis) ->Self:
        """Optional
        set the first two axes corresponding to the vanishing lines
        """
        self.first_axis = first_axis
        self.second_axis = second_axis
        return self
    
    def scale_by_reference(self, 
        segment:Tuple[float, float], 
        world_size:float, 
        axis:ReferenceAxis
    ) ->Self:
        """Optional
        set a reference distance segment in 2D (from origin to camera) and its corresponding world size along a given axis
        """
        self.reference_axis = axis
        self.reference_distance_segment = segment
        self.reference_world_size = world_size
        return self
    
    def scale_by_camera_distance(self, distance:float) ->Self:
        """
        Optionally set the camera distance from the origin.
        """
        self.reference_axis = None
        self.reference_world_size = distance
        return self
    
    def solve(self) -> Dict:
        self.vanishing_points = [least_squares_intersection_of_lines(lines) for lines in self.vanishing_lines]
        
        match len(self.vanishing_points):
            case 1:
                if self.focal_length is None:
                    raise ValueError("Focal length must be set when using a single vanishing point.")
                self.view = glm.mat4(compute_orientation_from_single_vanishing_point(
                    Fu=self.vanishing_points[0],
                    P=self.principal_point,
                    f=self.focal_length
                ))

            case 2:
                self.focal_length = compute_focal_length_from_vanishing_points(Fu=self.vanishing_points[0],Fv=self.vanishing_points[1],P=self.principal_point)
                self.view = glm.mat4(compute_orientation_from_two_vanishing_points(
                    Fu=self.vanishing_points[0],
                    Fv=self.vanishing_points[1],
                    P=self.principal_point,
                    f=self.focal_length
                ))

            case 3:
                self.principal = triangle_orthocenter(
                    self.vanishing_points[0], 
                    self.vanishing_points[1], 
                    self.vanishing_points[2]
                )
                self.focal_length = compute_focal_length_from_vanishing_points(
                    Fu=self.vanishing_points[0],
                    Fv=self.vanishing_points[1],
                    P=self.principal
                )
                self.view = glm.mat4(compute_orientation_from_two_vanishing_points(
                    Fu=self.vanishing_points[0],
                    Fv=self.vanishing_points[1],
                    P=self.principal,
                    f=self.focal_length
                ))
        
        # compute projection
        center_x = self.viewport.x + self.viewport.width / 2
        center_y = self.viewport.y + self.viewport.height / 2
        shift_x = -(self.principal.x - center_x) / (self.viewport.width / 2)
        shift_y = (self.principal.y - center_y) / (self.viewport.height / 2)

        self.shift_x = shift_x
        self.shift_y = shift_y

        self.projection = perspective_tiltshift(
            fov_from_focal_length(self.focal_length, self.viewport.height), 
            self.viewport.width/self.viewport.height, 
            DEFAULT_NEAR_PLANE,
            DEFAULT_FAR_PLANE, 
            shift_x, 
            -shift_y # TODO: note the negation here to match unProject convention TODO: double check why? see roll matrix later.
        )

        # Adjust camera position to look at origin O
        O = self.origin if self.origin is not None else glm.vec2(
            self.viewport.x + self.viewport.width / 2,
            self.viewport.y + self.viewport.height / 2
        )
        ray = cast_ray(O, self.view, self.projection, tuple(self.viewport))
        camera_position = glm.normalize(ray[1] - glm.vec3(0,0,0))
        self.view = glm.translate(self.view, camera_position)

        if len(self.vanishing_points) == 1 and self.roll_line is not None:
            # Adjust Camera Roll to match second vanishing line
            self.view = self.view * compute_roll_matrix(
                self.vanishing_lines[1][0], # Roll the camera based on the horizon line projected to 3D
                self.view,
                self.projection,
                tuple(self.viewport)
            )

        # Apply axis assignment
        self.view = self.view * glm.mat4(create_axis_assignment_matrix(self.first_axis, self.second_axis))

        # Apply reference scaling if provided
        if self.reference_axis is not None:
            self.view = apply_reference_world_distance(
                self.reference_axis, 
                self.reference_distance_segment, 
                self.reference_world_size,
                self.view, 
                self.projection, 
                self.viewport
            )

        return {
            'viewport': self.viewport,
            'view': self.view,
            'projection': self.projection,
            'principal_point': self.principal,
            'focal_length': self.focal_length,
            'first_vanishing_point': self.vanishing_points[0],
            'second_vanishing_point': self.vanishing_points[1] if len(self.vanishing_points) > 1 else None,
            'third_vanishing_point': self.vanishing_points[2] if len(self.vanishing_points) > 2 else None,
            'shift_x': self.shift_x,
            'shift_y': self.shift_y
        }


if __name__ == "__main__":
    results = (SolverBuilder()
        .set_viewport(0,0,1920, 1080)
        .use_vanishing_lines(...)
        .set_principal_point(960, 540)
        .set_focal_length(1.5)
        .set_origin(960, 540)
        .set_axes(Axis.PositiveX, Axis.PositiveY)
        .scale_by_camera_distance(10.0)
        .solve()
    )
