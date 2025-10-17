import math
import glm
from imgui_bundle import imgui
from typing import List, Tuple, Optional, NamedTuple
from calibrate_camera import compute_vanishing_point

class CameraEstimate(NamedTuple):
    position: glm.vec3
    pitch: float  # radians
    yaw: float    # radians
    roll: float   # radians
    fov: Optional[float] = None  # degrees, None if not estimable

class CameraEstimator:
    def __init__(self):
        self.principal_point = imgui.ImVec2(0, 0)
        self.viewport_size = imgui.ImVec2(0, 0)
        
    def set_viewport(self, size: imgui.ImVec2):
        self.viewport_size = size
        self.principal_point = imgui.ImVec2(size.x / 2, size.y / 2)
    
    def estimate_camera(
        self, 
        screen_origin: imgui.ImVec2,
        distance: float,
        vanishing_lines: List[List[List[imgui.ImVec2]]],  # [X_axis, Y_axis, Z_axis]
        use_vanishing_lines: List[bool],
        horizon: Optional[float] = None,
        provided_fov: Optional[float] = None
    ) -> CameraEstimate:
        """
        Estimate camera parameters based on available information.
        """
        num_axes = sum(use_vanishing_lines)
        
        if num_axes == 0:
            return self._estimate_no_axes(screen_origin, distance, horizon, provided_fov)
        elif num_axes == 1:
            return self._estimate_one_axis(screen_origin, distance, vanishing_lines, use_vanishing_lines, provided_fov)
        elif num_axes == 2:
            return self._estimate_two_axes(screen_origin, distance, vanishing_lines, use_vanishing_lines)
        else:  # num_axes == 3
            return self._estimate_three_axes(screen_origin, distance, vanishing_lines, use_vanishing_lines)
    
    def _estimate_no_axes(self, screen_origin: imgui.ImVec2, distance: float, horizon: float, fov: float) -> CameraEstimate:
        """
        Scenario 1: No vanishing lines, only horizon and origin.
        """
        if horizon is None:
            horizon = self.principal_point.y
            
        # Calculate pitch from horizon
        horizon_ndc_dy = (self.principal_point.y - horizon) / (self.viewport_size.y / 2.0)
        pitch = math.atan2(-horizon_ndc_dy * math.tan(math.radians(fov) / 2), 1.0)
        
        # Calculate position from origin marker
        position = self._calculate_camera_position(screen_origin, distance, pitch, 0.0, fov)
        
        return CameraEstimate(
            position=position,
            pitch=pitch,
            yaw=0.0,
            roll=0.0,
            fov=fov
        )
    
    def _estimate_one_axis(self, screen_origin: imgui.ImVec2, distance: float, vanishing_lines: List, use_vanishing_lines: List[bool], fov: float) -> CameraEstimate:
        """
        Scenario 2: One axis provided.
        Can estimate orientation based on vanishing point direction and line orientations.
        """
        # Find which axis is provided
        axis_index = use_vanishing_lines.index(True)
        lines = vanishing_lines[axis_index]
        
        if not lines:
            return self._estimate_no_axes(screen_origin, distance, None, fov)
        
        # Compute vanishing point
        vp = imgui.ImVec2(*compute_vanishing_point(lines))
        
        # Convert to NDC
        vp_ndc_x = (vp.x - self.principal_point.x) / (self.viewport_size.x / 2.0)
        vp_ndc_y = (self.principal_point.y - vp.y) / (self.viewport_size.y / 2.0)
        
        aspect = self.viewport_size.x / self.viewport_size.y
        tan_half_fov = math.tan(math.radians(fov) / 2.0)
        
        pitch = 0.0
        yaw = 0.0
        roll = 0.0
        
        if axis_index == 0:  # X axis (horizontal axis in world)
            # X-axis vanishing point tells us about camera roll and potentially yaw
            # If X-axis lines are truly horizontal in world space, VP gives us roll
            roll = math.atan2(vp_ndc_y * tan_half_fov, vp_ndc_x * aspect * tan_half_fov)
            
            # Also estimate pitch from the average direction of the lines
            avg_line_angle = self._get_average_line_angle(lines)
            # If lines are slanted, it might indicate pitch
            pitch = self._estimate_pitch_from_line_angle(avg_line_angle, axis_index)
            
        elif axis_index == 1:  # Y axis (vertical axis in world)
            # Y-axis vanishing point gives us pitch directly
            pitch = math.atan2(vp_ndc_y * tan_half_fov, 1.0)
            
            # Yaw can be estimated from the horizontal offset of the vanishing point
            yaw = math.atan(vp_ndc_x * tan_half_fov * aspect)
            
        elif axis_index == 2:  # Z axis (depth axis in world)
            # Z-axis vanishing point gives us yaw and pitch
            yaw = math.atan(vp_ndc_x * tan_half_fov * aspect)
            
            # The horizon is at the vanishing point's Y level for Z-axis
            horizon = vp.y
            horizon_ndc_dy = (self.principal_point.y - horizon) / (self.viewport_size.y / 2.0)
            pitch = math.atan2(-horizon_ndc_dy * tan_half_fov, 1.0)
            
            # Roll can be estimated from the direction of the vanishing lines
            avg_line_angle = self._get_average_line_angle(lines)
            roll = self._estimate_roll_from_z_lines(avg_line_angle, vp)
        
        position = self._calculate_camera_position(screen_origin, distance, pitch, yaw, fov)
        
        return CameraEstimate(
            position=position,
            pitch=pitch,
            yaw=yaw,
            roll=roll,
            fov=fov
        )
    
    def _get_average_line_angle(self, lines: List[List[imgui.ImVec2]]) -> float:
        """Calculate the average angle of the vanishing lines in screen space."""
        if not lines:
            return 0.0
            
        angles = []
        for line in lines:
            if len(line) >= 2:
                start, end = line[0], line[1]
                dx = end.x - start.x
                dy = end.y - start.y
                angle = math.atan2(dy, dx)
                angles.append(angle)
        
        if not angles:
            return 0.0
            
        # Average the angles (handle wraparound)
        avg_sin = sum(math.sin(a) for a in angles) / len(angles)
        avg_cos = sum(math.cos(a) for a in angles) / len(angles)
        return math.atan2(avg_sin, avg_cos)
    
    def _estimate_pitch_from_line_angle(self, line_angle: float, axis_index: int) -> float:
        """Estimate pitch from the angle of vanishing lines."""
        # For X-axis lines, if they're slanted, it might indicate camera pitch
        # This is a simplified estimation - in reality it's more complex
        if axis_index == 0:  # X-axis
            # If X lines are slanted up/down, camera might be pitched
            return line_angle * 0.1  # Scale factor to be tuned
        return 0.0
    
    def _estimate_roll_from_z_lines(self, line_angle: float, vp: imgui.ImVec2) -> float:
        """Estimate roll from Z-axis vanishing lines."""
        # Z-axis lines converging to a point - their angle relative to
        # the line from screen center to VP gives us roll information
        center_to_vp_angle = math.atan2(
            vp.y - self.principal_point.y,
            vp.x - self.principal_point.x
        )
        
        # The difference between line angle and center-to-VP angle
        # indicates roll rotation
        roll_estimate = line_angle - center_to_vp_angle
        
        # Normalize to [-pi, pi]
        while roll_estimate > math.pi:
            roll_estimate -= 2 * math.pi
        while roll_estimate < -math.pi:
            roll_estimate += 2 * math.pi
            
        return roll_estimate * 0.5  # Scale factor to be tuned
    
    def _estimate_two_axes(self, screen_origin: imgui.ImVec2, distance: float, vanishing_lines: List, use_vanishing_lines: List[bool]) -> CameraEstimate:
        """
        Scenario 3: Two axes provided.
        Can estimate: fov, full orientation, position
        """
        # Get the two provided axes
        provided_indices = [i for i, use in enumerate(use_vanishing_lines) if use]
        
        if len(provided_indices) != 2:
            raise ValueError("Expected exactly 2 axes for this scenario")
        
        # Compute vanishing points for both axes
        vp1 = imgui.ImVec2(*compute_vanishing_point(vanishing_lines[provided_indices[0]]))
        vp2 = imgui.ImVec2(*compute_vanishing_point(vanishing_lines[provided_indices[1]]))
        
        # Convert to NDC
        vp1_ndc = self._to_ndc(vp1)
        vp2_ndc = self._to_ndc(vp2)
        
        # Estimate FOV using the constraint that orthogonal axes in world space
        # should have their vanishing points satisfy certain geometric relationships
        fov = self._estimate_fov_from_two_vps(vp1_ndc, vp2_ndc, provided_indices)
        
        # Now estimate full orientation
        pitch, yaw, roll = self._estimate_orientation_from_two_vps(vp1_ndc, vp2_ndc, provided_indices, fov)
        
        position = self._calculate_camera_position(screen_origin, distance, pitch, yaw, fov)
        
        return CameraEstimate(
            position=position,
            pitch=pitch,
            yaw=yaw,
            roll=roll,
            fov=fov
        )
    
    def _estimate_three_axes(self, screen_origin: imgui.ImVec2, distance: float, vanishing_lines: List, use_vanishing_lines: List[bool]) -> CameraEstimate:
        """
        Scenario 4: All three axes provided.
        Overconstrained system for maximum accuracy.
        """
        # Compute all three vanishing points
        vps = []
        for i in range(3):
            if vanishing_lines[i]:
                vp = imgui.ImVec2(*compute_vanishing_point(vanishing_lines[i]))
                vps.append(self._to_ndc(vp))
            else:
                vps.append(None)
        
        # Use the most reliable pair for estimation
        if vps[0] and vps[2]:  # X and Z axes (most common architectural case)
            fov = self._estimate_fov_from_two_vps(vps[0], vps[2], [0, 2])
            pitch, yaw, roll = self._estimate_orientation_from_two_vps(vps[0], vps[2], [0, 2], fov)
        elif vps[1] and vps[2]:  # Y and Z axes
            fov = self._estimate_fov_from_two_vps(vps[1], vps[2], [1, 2])
            pitch, yaw, roll = self._estimate_orientation_from_two_vps(vps[1], vps[2], [1, 2], fov)
        else:  # X and Y axes
            fov = self._estimate_fov_from_two_vps(vps[0], vps[1], [0, 1])
            pitch, yaw, roll = self._estimate_orientation_from_two_vps(vps[0], vps[1], [0, 1], fov)
        
        position = self._calculate_camera_position(screen_origin, distance, pitch, yaw, fov)
        
        return CameraEstimate(
            position=position,
            pitch=pitch,
            yaw=yaw,
            roll=roll,
            fov=fov
        )
    
    def _to_ndc(self, point: imgui.ImVec2) -> Tuple[float, float]:
        """Convert screen point to normalized device coordinates"""
        ndc_x = (point.x - self.principal_point.x) / (self.viewport_size.x / 2.0)
        ndc_y = (self.principal_point.y - point.y) / (self.viewport_size.y / 2.0)
        return (ndc_x, ndc_y)
    
    def _estimate_fov_from_two_vps(self, vp1_ndc: Tuple[float, float], vp2_ndc: Tuple[float, float], axis_indices: List[int]) -> float:
        """Estimate FOV from two vanishing points of orthogonal axes."""
        # For orthogonal axes, there's a geometric constraint relating their VPs to FOV
        # This is based on the fact that orthogonal world directions should have
        # specific angular relationships in the perspective projection
        
        # Calculate the angle between the two vanishing points
        dot_product = vp1_ndc[0] * vp2_ndc[0] + vp1_ndc[1] * vp2_ndc[1]
        
        # For truly orthogonal axes viewed with perspective projection,
        # there's a relationship: cos(angle_between_VPs) = -cos²(half_fov) for some configurations
        
        # Simplified estimation based on VP separation
        aspect = self.viewport_size.x / self.viewport_size.y
        
        # Distance between VPs in NDC space
        dx = vp2_ndc[0] - vp1_ndc[0]
        dy = vp2_ndc[1] - vp1_ndc[1]
        vp_distance = math.sqrt(dx*dx + dy*dy)
        
        # Empirical relationship - to be refined
        estimated_fov = 60.0 + (vp_distance - 1.0) * 30.0
        
        # Clamp to reasonable range
        return max(20.0, min(120.0, estimated_fov))
    
    def _estimate_orientation_from_two_vps(self, vp1_ndc: Tuple[float, float], vp2_ndc: Tuple[float, float], axis_indices: List[int], fov: float) -> Tuple[float, float, float]:
        """Estimate pitch, yaw, roll from two vanishing points"""
        aspect = self.viewport_size.x / self.viewport_size.y
        tan_half_fov = math.tan(math.radians(fov) / 2.0)
        
        pitch = 0.0
        yaw = 0.0
        roll = 0.0
        
        # Extract angles based on which axes are provided
        if 0 in axis_indices:  # X axis
            vp_x = vp1_ndc if axis_indices[0] == 0 else vp2_ndc
            roll = math.atan2(vp_x[1] * tan_half_fov, vp_x[0] * aspect * tan_half_fov)
        
        if 1 in axis_indices:  # Y axis
            vp_y = vp1_ndc if axis_indices[0] == 1 else vp2_ndc
            pitch = math.atan2(vp_y[1] * tan_half_fov, 1.0)
        
        if 2 in axis_indices:  # Z axis
            vp_z = vp1_ndc if axis_indices[0] == 2 else vp2_ndc
            yaw = math.atan(vp_z[0] * tan_half_fov * aspect)
            if 1 not in axis_indices:  # If Y axis not provided, get pitch from Z axis horizon
                pitch = math.atan2(-vp_z[1] * tan_half_fov, 1.0)
        
        return (pitch, yaw, roll)
    
    def _calculate_camera_position(self, screen_origin: imgui.ImVec2, distance: float, pitch: float, yaw: float, fov: float) -> glm.vec3:
        """Calculate camera position such that world origin projects to screen_origin"""
        # Convert origin to NDC space
        origin_ndc_x = (screen_origin.x - self.principal_point.x) / (self.viewport_size.x / 2.0)
        origin_ndc_y = (self.principal_point.y - screen_origin.y) / (self.viewport_size.y / 2.0)
        
        # Calculate ray direction from camera through the origin point
        aspect = self.viewport_size.x / self.viewport_size.y
        tan_half_fov = math.tan(math.radians(fov) / 2.0)
        
        # Ray direction in camera space
        ray_x = origin_ndc_x * tan_half_fov * aspect
        ray_y = origin_ndc_y * tan_half_fov
        ray_z = -1.0
        
        # Normalize
        ray_length = math.sqrt(ray_x**2 + ray_y**2 + ray_z**2)
        ray_x /= ray_length
        ray_y /= ray_length
        ray_z /= ray_length
        
        # Apply camera rotations to ray
        cos_pitch = math.cos(pitch)
        sin_pitch = math.sin(pitch)
        cos_yaw = math.cos(yaw)
        sin_yaw = math.sin(yaw)
        
        # Rotate by pitch (around X axis), then by yaw (around Y axis)
        # First pitch
        ray_y_rotated = ray_y * cos_pitch - ray_z * sin_pitch
        ray_z_rotated = ray_y * sin_pitch + ray_z * cos_pitch
        
        # Then yaw
        ray_x_final = ray_x * cos_yaw + ray_z_rotated * sin_yaw
        ray_y_final = ray_y_rotated
        ray_z_final = -ray_x * sin_yaw + ray_z_rotated * cos_yaw
        
        # Position camera so ray hits world origin at given distance
        camera_pos_x = -distance * ray_x_final
        camera_pos_y = -distance * ray_y_final
        camera_pos_z = -distance * ray_z_final
        
        return glm.vec3(camera_pos_x, camera_pos_y, camera_pos_z)