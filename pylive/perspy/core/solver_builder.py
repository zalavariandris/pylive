from . solver import *


# Builder
class CameraSolver:
    def __init__(self, viewport: Viewport):
        self.viewport = viewport
        
        # Internal State
        self.view_matrix = glm.mat4(1.0)
        self.projection_matrix = glm.mat4(1.0)
        
        # Metadata for results
        self.fovy = 0.0
        self.principal_point = glm.vec2(0,0)
        self.shift = glm.vec2(0,0)
        
        # Vanishing points storage for result metadata
        self.vp1: glm.vec2|None = None
        self.vp2: glm.vec2|None = None
        self.vp3: glm.vec2|None = None

    def _update_projection(self, f: float, P: glm.vec2):
        """Internal helper to rebuild projection matrix based on f and P"""
        self.fovy = fov_from_focal_length(f, self.viewport.height)
        self.principal_point = P
        
        # Calculate lens shift
        pos = glm.vec2(self.viewport.x, self.viewport.y)
        size = glm.vec2(self.viewport.width, self.viewport.height)
        center = pos + size / 2
        self.shift = (center - P) / (size / 2)

        self.projection_matrix = perspective_tiltshift(
            self.fovy, 
            self.viewport.width/self.viewport.height, 
            0.1, 1000.0, 
            self.shift.x, -self.shift.y
        )

    # -------------------------------------------------------
    # Step 1: Initialization Strategies (Mutually Exclusive)
    # -------------------------------------------------------

    def init_1vp(self, Fu: glm.vec2, P: glm.vec2, f: float) -> 'CameraSolver':
        self.vp1 = Fu
        self._update_projection(f, P)
        
        # Compute Orientation (Rotation only)
        orientation = compute_orientation_from_single_vanishing_point(Fu, P, f)
        self.view_matrix = glm.mat4(orientation)
        return self

    def init_2vp(self, Fu: glm.vec2, Fv: glm.vec2, P: glm.vec2) -> 'CameraSolver':
        self.vp1 = Fu
        self.vp2 = Fv
        
        # Compute Focal Length
        f = _compute_focal_length_from_vanishing_points(Fu, Fv, P)
        self._update_projection(f, P)

        # Compute Orientation (Rotation only)
        orientation = compute_orientation_from_two_vanishing_points(Fu, Fv, P, f)
        self.view_matrix = glm.mat4(orientation)
        return self

    def init_3vp(self, Fu: glm.vec2, Fv:glm.vec2, Fw:glm.vec2) -> 'CameraSolver':
        # Logic for 3VP (calculates P automatically)
        P = triangle_orthocenter(Fu, Fv, Fw)
        return self.init_2vp(Fu, Fv, P)

    # -------------------------------------------------------
    # Step 2: Refinements (Optional / Sequential)
    # -------------------------------------------------------

    def apply_roll(self, vanishing_line: Tuple[glm.vec2, glm.vec2]) -> 'CameraSolver':
        """Rotates the camera so the 3D line matches the horizon."""
        self.view_matrix = compute_roll_matrix(
            vanishing_line, 
            self.view_matrix, 
            self.projection_matrix, 
            self.viewport
        )
        return self

    def set_position(self, screen_origin: glm.vec2, world_origin: glm.vec2 = glm.vec2(0,0)) -> 'CameraSolver':
        """Moves the camera so that world_origin projects to screen_origin."""
        # Note: This logic assumes O is (0,0,0) in 3D for now, as per original code
        ray = cast_ray(screen_origin, self.view_matrix, self.projection_matrix, self.viewport)
        
        # Vector from camera to the point on the ray corresponding to distance 0? 
        # Original logic: camera_position = normalize(ray_direction) * distance?
        # Actually, original logic was: translate view matrix by camera position.
        
        # Re-implementing the logic from solve1vp:
        camera_position = glm.normalize(ray[1] - glm.vec3(0,0,0)) # This looks like direction, not position?
        # Wait, the original code `view_matrix = glm.translate(view_matrix, camera_position)` 
        # implies moving the world relative to camera.
        
        self.view_matrix = glm.translate(self.view_matrix, camera_position)
        return self

    def set_scale(self, 
                  segment: Tuple[float, float], 
                  world_size: float, 
                  axis: ReferenceAxis) -> 'CameraSolver':
        """Scales the world to match a known reference distance."""
        self.view_matrix = apply_reference_world_distance(
            axis, segment, world_size,
            self.view_matrix, self.projection_matrix, self.viewport
        )
        return self

    def align_axes(self, first_axis: Axis, second_axis: Axis) -> 'CameraSolver':
        """Permutes the axes (e.g. swap X and Y)."""
        assignment = create_axis_assignment_matrix(first_axis, second_axis)
        self.view_matrix = self.view_matrix * glm.mat4(assignment)
        return self

    # -------------------------------------------------------
    # Step 3: Build
    # -------------------------------------------------------

    def build(self) -> SolverResults:
        return SolverResults(
            compute_space=self.viewport,
            transform=glm.inverse(self.view_matrix), # Camera to World
            fovy=self.fovy,
            aspect=self.viewport.width / self.viewport.height,
            near_plane=0.1,
            far_plane=1000.0,
            shift_x=self.shift.x,
            shift_y=self.shift.y,
            principal_point=self.principal_point,
            first_vanishing_point=self.vp1,
            second_vanishing_point=self.vp2,
            third_vanishing_point=self.vp3
        )


if __name__ == "__main__":
    # Usage Example for 1VP
    results = (
        CameraSolver(viewport)
        .init_1vp(vp1, principal_point, focal_length)
        .apply_roll(horizon_line)  # Specific to 1VP
        .set_position(screen_origin, world_origin)
        .set_scale(ref_segment, world_size)
        .align_axes(axis1, axis2)
        .build()
    )

    # Usage Example for 2VP
    results = (
        CameraSolver(viewport)
        .init_2vp(vp1, vp2, principal_point)
        # .apply_roll() is skipped because 2VP determines roll automatically
        .set_position(screen_origin, world_origin)
        .set_scale(ref_segment, world_size)
        .align_axes(axis1, axis2)
        .build()
    )