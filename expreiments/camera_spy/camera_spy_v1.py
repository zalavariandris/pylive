import logging
logger = logging.getLogger(__name__)

import math
import numpy as np
from pylive.render_engine.camera import Camera


# ############## #
# Graphics Layer #
# ############## #
import moderngl
from pylive.render_engine.render_layers import GridLayer, RenderLayer
import OpenGL.GL as gl
import glm


class SceneLayer(RenderLayer):
    def __init__(self):
        self.initialized = False
        self.grid = GridLayer()

    def setup(self, ctx:moderngl.Context):
        self.grid.setup(ctx)
        super().setup(ctx)

    def destroy(self):
        if self.grid:
            self.grid.destroy()
            self.grid = None
        return super().destroy()
    
    def render(self, camera:Camera):
        self.grid.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        super().render()


# ########### #
# GUI helpers #
# ########### #
from imgui_bundle import imgui, immapp
from gizmos import drag_axes, drag_horizon
from utils.geo import closest_point_line_segment
from gizmos import window_to_screen, drag_point

# COLOR CONSTANTS
BLUE = imgui.color_convert_float4_to_u32((0,0,1, 1.0))
BLUE_DIMMED = imgui.color_convert_float4_to_u32((0,0,1, 0.2))
GREEN = imgui.color_convert_float4_to_u32((0,1,0, 1.0))
GREEN_DIMMED = imgui.color_convert_float4_to_u32((0,1,0, 0.2))
WHITE = imgui.color_convert_float4_to_u32((1,1,1, 1.0))
WHITE_DIMMED = imgui.color_convert_float4_to_u32((1,1,1, 0.2))

# ##### #
# TYPES #
# ##### #
from core import LineSegment, Point2D
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
from typing import NewType, Callable, Dict
from typing import NewType
Point2D = NewType("Point2D", Tuple[float, float])
LineSegment = NewType("LineSegment", Tuple[Point2D, Point2D])
Radians = NewType("Radians", float)
Degrees = NewType("Degrees", float)

from typing import NamedTuple
class CameraEstimate(NamedTuple):
    position: Tuple[float, float, float]  # (x, y, z)
    pitch: float  # radians
    yaw: float    # radians
    roll: float   # radians
    fov: Optional[float] = None  # degrees, None if not estimable


Width = NewType("Width", int)
Height = NewType("Height", int)
Size = NewType("Size", Tuple[Width, Height])

class Rect(NamedTuple):
    x: int
    y: int
    width: Width
    height: Height


# ########################## #
# Camera Estimator Functions #
# ########################## #

from calibrate_camera import compute_vanishing_point, estimate_focal_length, compute_camera_orientation

def compute_camera_position(*,viewport_size:imgui.ImVec2, screen_origin:imgui.ImVec2, principal_point:imgui.ImVec2, camera_pitch:float, distance:float):
    ## 2. Compute camera POSITION from origin marker
    # Origin marker tells us where the world origin (0,0,0) appears on screen
    # We need to position the camera so that (0,0,0) projects to the origin marker
    
    # Convert origin to NDC space
    origin_ndc_x = (screen_origin.x - principal_point.x) / (viewport_size.x / 2.0)
    origin_ndc_y = (principal_point.y - screen_origin.y) / (viewport_size.y / 2.0)  # Flip Y
    
    # Calculate the ray direction from camera through the origin point in screen space
    # In camera space (before rotation):
    # - Camera looks down -Z axis
    # - X is right, Y is up
    aspect = viewport_size.x / viewport_size.y
    tan_half_fov = math.tan(math.radians(fov) / 2.0)
    
    # Ray direction in camera space (normalized device coordinates)
    ray_x = origin_ndc_x * tan_half_fov * aspect
    ray_y = origin_ndc_y * tan_half_fov
    ray_z = -1.0  # Looking down -Z
    
    # Normalize the ray
    ray_length = math.sqrt(ray_x**2 + ray_y**2 + ray_z**2)
    ray_x /= ray_length
    ray_y /= ray_length
    ray_z /= ray_length
    
    # Apply camera pitch rotation to ray (rotate around X axis)
    # After rotation, the ray is in world space
    cos_pitch = math.cos(camera_pitch)
    sin_pitch = math.sin(camera_pitch)
    
    ray_world_x = ray_x
    ray_world_y = ray_y * cos_pitch - ray_z * sin_pitch
    ray_world_z = ray_y * sin_pitch + ray_z * cos_pitch
    
    # Now solve: camera_pos + t * ray_world = (0, 0, 0)
    # We want the ray to hit the world origin at the given distance
    # Assuming world origin is on the ground plane (y=0):
    # camera_y + t * ray_world_y = 0
    # t = -camera_y / ray_world_y
    
    # But we also want: distance = ||camera_pos||
    # So we need to solve for camera position where:
    # 1. Ray passes through world origin (0,0,0)
    # 2. Camera is at distance 'distance' from world origin
    
    # Simplification: camera_pos = -t * ray_world, and ||camera_pos|| = distance
    # Therefore: t = distance
    
    camera_pos_x = -distance * ray_world_x
    camera_pos_y = -distance * ray_world_y
    camera_pos_z = -distance * ray_world_z

    return camera_pos_x, camera_pos_y, camera_pos_z

def _estimate_pitch_from_horizon(horizon:float, principal_point:imgui.ImVec2, size:imgui.ImVec2, fov:float)->float:
    # Convert horizon to NDC space
    horizon_ndc_y = (principal_point.y - horizon) / (size.y / 2.0)  # Flip Y
    
    # Calculate pitch angle from horizon NDC position
    pitch = math.atan2(-horizon_ndc_y * math.tan(math.radians(fov) / 2), 1.0)
    return pitch

def estimate_no_axis(*, 
        viewport_size:imgui.ImVec2, 
        screen_origin:imgui.ImVec2, 
        principal_point:imgui.ImVec2, 
        fov:Degrees, 
        distance:float, 
        horizon:float
    ) -> Tuple[float, float, float, float]:
    """Estimate camera pitch and position given no axis lines, just horizon and origin.
    
    return (camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z)
    """
    ## 1. Compute camera PITCH from horizon line (camera orientation)
    # Horizon tells us where the camera is looking vertically

    # horizon_ndc_dy = (principal_point.y - horizon) / (size.y / 2.0)
    # camera_pitch = math.atan2(-horizon_ndc_dy * math.tan(math.radians(fov) / 2), 1.0)

    camera_pitch = _estimate_pitch_from_horizon(
        horizon, 
        principal_point, 
        viewport_size, 
        fov
    )

    camera_pos_x, camera_pos_y, camera_pos_z = compute_camera_position(
        viewport_size=viewport_size,
        screen_origin=screen_origin,
        principal_point=principal_point,
        camera_pitch=camera_pitch,
        distance=distance
    )

    return camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z

def build_camera_transform(camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z):
    ## Build camera transform
    # The camera should be oriented based on pitch (from horizon) and positioned
    # so that the world origin (0,0,0) appears at the origin marker's screen position
    
    # Build the camera's local coordinate system
    # Start with camera looking down -Z with up being +Y
    camera_forward = glm.vec3(0, 0, -1)
    camera_up = glm.vec3(0, 1, 0)
    camera_right = glm.vec3(1, 0, 0)
    
    # Apply pitch rotation to the camera axes
    cos_pitch = math.cos(camera_pitch)
    sin_pitch = math.sin(camera_pitch)
    
    # Rotate forward and up vectors around X-axis (right vector stays the same)
    camera_forward = glm.vec3(0, sin_pitch, -cos_pitch)
    camera_up = glm.vec3(0, cos_pitch, sin_pitch)
    
    # Build rotation matrix from camera axes
    # OpenGL camera: right = +X, up = +Y, forward = -Z (view direction)
    rotation_matrix = glm.mat4(
        glm.vec4(camera_right, 0),
        glm.vec4(camera_up, 0),
        glm.vec4(-camera_forward, 0),  # Negative because camera looks down -Z
        glm.vec4(0, 0, 0, 1)
    )
    
    # Create translation matrix
    translation = glm.translate(glm.mat4(1.0), glm.vec3(camera_pos_x, camera_pos_y, camera_pos_z))
    
    # Combine: first rotate, then translate
    return translation * rotation_matrix


# ########## #
# INITIALIZE #
# ########## #

# ModernGL context and framebuffer
scene_renderer = SceneLayer()
ctx: moderngl.Context|None = None
fbo: moderngl.Framebuffer|None = None

# Parameters
horizon = 300.0
vanishing_lines = [
        [

    ],[

    ],[
        [imgui.ImVec2(145, 480), imgui.ImVec2(330, 330)],
        [imgui.ImVec2(650, 460), imgui.ImVec2(508, 343)]
    ]
]

use_vanishing_lines = [False, False, False]
axis_names = ('X', 'Y', 'Z')
screen_origin = imgui.ImVec2(400, 400)
fov:Degrees = 60.0
distance = 5.0

# ######### #
# MAIN LOOP #
# ######### #
def gui():
    global ctx, fbo
    # Camera Calibration parameters
    global distance
    global screen_origin
    global horizon
    global fov
    global vanishing_lines, use_vanishing_lines

    imgui.text("Camera Spy")
    if imgui.begin_child("3d_viewport", imgui.ImVec2(0, 0)):
        # Get ImGui child window dimensions and position
        size = imgui.get_content_region_avail()
        pos = imgui.get_cursor_screen_pos()

        if ctx is None:
            logger.info("Initializing ModernGL context...")
            ctx = moderngl.create_context()
            
            scene_renderer.setup(ctx)
        
        ## Create or resize framebuffer if needed
        dpi = imgui.get_io().display_framebuffer_scale
        fb_width = int(size.x * dpi.x)
        fb_height = int(size.y * dpi.y)
        
        
        if fbo is None or fbo.width != fb_width or fbo.height != fb_height:
            if fbo is not None:
                fbo.release()
            
            # Create color texture
            color_texture = ctx.texture((fb_width, fb_height), 4, dtype='f1')
            color_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            
            # Create depth renderbuffer
            depth_buffer = ctx.depth_renderbuffer((fb_width, fb_height))
            
            # Create framebuffer
            fbo = ctx.framebuffer(
                color_attachments=[color_texture],
                depth_attachment=depth_buffer
            )
            
            logger.info(f"Created framebuffer: {fb_width}x{fb_height}")
        
        
        # parameters
        camera = Camera()
        camera.setAspectRatio(size.x / size.y)
        camera.setFOV(fov)

        # Compute Camera from parameters
        for i, in_use in enumerate(use_vanishing_lines):
            _, use_vanishing_lines[i] = imgui.checkbox(f"use {axis_names[i]} axes", in_use)

        match use_vanishing_lines:
            case (False, False, False):
                # parameters
                _, horizon = drag_horizon(horizon, WHITE_DIMMED)
                _, fov = imgui.slider_float("fov", fov, 20.0, 120.0, "%.2f")
                _, distance = imgui.drag_float("distance", distance, 0.1, 0.1, 20.0, "%.2f")
                _, screen_origin = drag_point("origin###origin", screen_origin)
                principal_point = imgui.ImVec2(size.x / 2, size.y / 2)

                # compute
                camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z = estimate_no_axis(
                    horizon=horizon,
                    viewport_size=size,
                    screen_origin=screen_origin,
                    fov=fov,
                    principal_point=principal_point,
                    distance=distance,
                )

                camera.transform = build_camera_transform(camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z)

            case (False, False, True):
                # parameters
                principal_point = imgui.ImVec2(size.x / 2, size.y / 2)
                _, vanishing_lines[2] = drag_axes("Z", vanishing_lines[2], BLUE)

                # calculate vanishing point
                vp_z = imgui.ImVec2(compute_vanishing_point([axis for axis in vanishing_lines[2]]))
                
                # draw vanishing point
                draw_list = imgui.get_window_draw_list()
                draw_list.add_circle_filled(window_to_screen(vp_z), 5, BLUE)
                draw_list.add_text(window_to_screen(vp_z) + imgui.ImVec2(5, -5),  BLUE, f"VP{2} ({vp_z.x:.0f},{vp_z.y:.0f})")

                # draw lines to vanishing point
                for axis in vanishing_lines[2]:
                    closest_point = closest_point_line_segment(vp_z, axis)
                    imgui.get_window_draw_list().add_line(window_to_screen(closest_point), window_to_screen(vp_z), BLUE_DIMMED, 1)

                # calc yaw from y axes.
                horizon = vp_z.y

                camera_pitch = _estimate_pitch_from_horizon(horizon, principal_point=principal_point, size=size, fov=fov)
                
                # compute yaw from vanishing point?
                vp_z_ndc_x = (vp_z.x - principal_point.x) / (size.x / 2.0)
                aspect = size.x / size.y
                tan_half_fov = math.tan(math.radians(fov) / 2.0)
                tan_half_fov_x = tan_half_fov * aspect
                camera_yaw = math.atan(vp_z_ndc_x * tan_half_fov_x)
                imgui.text(f"Camera yaw: {math.degrees(camera_yaw):.2f}° (from Z VP)")

                # compute camera position
                camera_pos_x, camera_pos_y, camera_pos_z = compute_camera_position(
                    viewport_size=size,
                    screen_origin=screen_origin,
                    principal_point=principal_point,
                    camera_pitch=camera_pitch,
                    distance=distance
                )

                # build transform
                camera.transform = build_camera_transform(camera_pitch, camera_pos_x, camera_pos_y, camera_pos_z)
                

            case _:
                imgui.text("Only Z axis supported for now")
                return
            

        # Update GL viewport
        display_size = imgui.get_io().display_size
        dpi = imgui.get_io().display_framebuffer_scale
        gl_size = display_size * dpi
        ctx.viewport = (0, 0, gl_size.x, gl_size.y)

        # Render to framebuffer
        fbo.use()
        fbo.clear(0.1, 0.1, 0.1, 0.0)  # Clear with dark gray background
        ctx.enable(moderngl.DEPTH_TEST)
        scene_renderer.render(camera)
        ctx.screen.use() # Restore default framebuffer
        
        # Display the framebuffer texture in ImGui
        texture = fbo.color_attachments[0] # Get texture from framebuffer
        texture_ref = imgui.ImTextureRef(texture.glo)
        
        imgui.set_cursor_pos(imgui.ImVec2(0,0))
        imgui.image(
            texture_ref,  # OpenGL texture ID
            imgui.ImVec2(size.x, size.y),
            uv0=imgui.ImVec2(0, 1),  # Flip vertically (OpenGL texture is bottom-up)
            uv1=imgui.ImVec2(1, 0)
        )

    imgui.end_child()

    
    # camera.setPosition(glm.vec3(5, 5, 5))
    # camera.lookAt(glm.vec3(0,0,0))
    # scene_renderer.render(camera)


if __name__ == "__main__":
    immapp.run(gui, window_title="ImGui Bundle - 2D Points & 3D Scene", window_size=(800, 800))