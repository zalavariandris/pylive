from venv import logger
from imgui_bundle import imgui, immapp
from matplotlib import use
from networkx import draw
from core import LineSegment, Point2D
from pylive.render_engine.render_layers import GridLayer, RenderLayer
from gizmos import drag_points
import math
import numpy as np
import moderngl
import OpenGL.GL as gl
import glm
## 3D Scene Setup (Simple software renderer)

## ModernGL 3D Scene Implementation

from pylive.render_engine.camera import Camera
from contextlib import contextmanager


# Global 3D scene instances
import glm 

from calibrate_camera import (
    compute_vanishing_point, 
    estimate_focal_length, 
    compute_camera_orientation
)


def touch_pad(label:str, size:imgui.ImVec2=imgui.ImVec2(200,200))->imgui.ImVec2:
    imgui.button(label, size)
    if imgui.is_item_active():
        delta = imgui.get_mouse_drag_delta()
        imgui.reset_mouse_drag_delta()

        return delta
    else:
        return imgui.ImVec2(0,0)

## state
from pathlib import Path
from dataclasses import dataclass, field
from typing import Tuple, List, Optional
import pickle

Point2D = Tuple[float, float]

@dataclass
class LineSegment:
    start: Point2D
    end: Point2D

    def __iter__(self):
        return iter((self.start, self.end))

from gizmos import window_to_screen, drag_point

from typing import NewType, Callable, Dict
Radians = NewType("Radians", float)
Degrees = NewType("Degrees", float)

## gui loop
# COLOR CONSTANTS
BLUE = imgui.color_convert_float4_to_u32((0,0,1, 1.0))
BLUE_DIMMED = imgui.color_convert_float4_to_u32((0,0,1, 0.2))
GREEN = imgui.color_convert_float4_to_u32((0,1,0, 1.0))
GREEN_DIMMED = imgui.color_convert_float4_to_u32((0,1,0, 0.2))
WHITE = imgui.color_convert_float4_to_u32((1,1,1, 1.0))
WHITE_DIMMED = imgui.color_convert_float4_to_u32((1,1,1, 0.2))

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


## GUI helpers
from gizmos import drag_lines, drag_horizon
from utils.geo import closest_point_on_line_segment

# ModernGL context and framebuffer
scene_renderer = SceneLayer()
ctx: moderngl.Context|None = None
fbo: moderngl.Framebuffer|None = None

# Parameters
horizon = 300.0
vanishing_lines = [
    [
        [imgui.ImVec2(620, 840), imgui.ImVec2(262, 611)],
        [imgui.ImVec2(766, 670), imgui.ImVec2(420, 570)]
    ],[
        [imgui.ImVec2(100, 400), imgui.ImVec2(300, 300)],
        [imgui.ImVec2(200, 500), imgui.ImVec2(400, 350)]
    ],[
        [imgui.ImVec2(145, 480), imgui.ImVec2(330, 330)],
        [imgui.ImVec2(650, 460), imgui.ImVec2(508, 343)]
    ]
]

use_vanishing_lines = [False, False, True]
axis_names = ('X', 'Y', 'Z')
screen_origin = imgui.ImVec2(400, 400)
fov:Degrees = 60.0
distance = 5.0

from camera_estimator import CameraEstimator, CameraEstimate

# Add this after the global variables
camera_estimator = CameraEstimator()



def gui():
    global ctx, fbo
    # Camera Calibration parameters
    global distance
    global screen_origin
    global horizon
    global fov
    global vanishing_lines, use_vanishing_lines
    global camera_estimator

    imgui.text("Camera Spy")
    if imgui.begin_child("3d_viewport", imgui.ImVec2(0, 0)):
        # Get ImGui child window dimensions and position
        size = imgui.get_content_region_avail()
        pos = imgui.get_cursor_screen_pos()
        
        # Update camera estimator viewport
        camera_estimator.set_viewport(size)

        # ...existing ModernGL setup code...
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
            
            color_texture = ctx.texture((fb_width, fb_height), 4, dtype='f1')
            color_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            depth_buffer = ctx.depth_renderbuffer((fb_width, fb_height))
            fbo = ctx.framebuffer(
                color_attachments=[color_texture],
                depth_attachment=depth_buffer
            )
            logger.info(f"Created framebuffer: {fb_width}x{fb_height}")

        # Calculate principal point at the center of the viewport
        principal_point = imgui.ImVec2(size.x / 2, size.y / 2)
        
        # UI for selecting which axes to use
        for i, in_use in enumerate(use_vanishing_lines):
            _, use_vanishing_lines[i] = imgui.checkbox(f"use {axis_names[i]} axes", in_use)

        # Draw axis lines and vanishing points for active axes
        num_active_axes = sum(use_vanishing_lines)
        colors = [GREEN, BLUE, WHITE]  # X, Y, Z colors

        for i, (in_use, color, name) in enumerate(zip(use_vanishing_lines, colors, axis_names)):
            if in_use:
                _, vanishing_lines[i] = drag_lines(name, vanishing_lines[i], color)
                
                if vanishing_lines[i]:
                    # Calculate and draw vanishing point
                    vp = imgui.ImVec2(*compute_vanishing_point(vanishing_lines[i]))
                    
                    draw_list = imgui.get_window_draw_list()
                    draw_list.add_circle_filled(window_to_screen(vp), 5, color)
                    draw_list.add_text(window_to_screen(vp) + imgui.ImVec2(5, -5), color, f"VP{axis_names[i]} ({vp.x:.0f},{vp.y:.0f})")
                    
                    # Draw lines to vanishing point
                    for axis in vanishing_lines[i]:
                        closest_point = closest_point_on_line_segment(vp, axis)
                        imgui.get_window_draw_list().add_line(window_to_screen(closest_point), window_to_screen(vp), color, 1)
                    
                    # Show line angles for single axis case
                    if num_active_axes == 1:
                        avg_angle = camera_estimator._get_average_line_angle(vanishing_lines[i])
                        imgui.text(f"Avg line angle: {math.degrees(avg_angle):.1f}°")

        # Handle horizon for no-axes case
        if num_active_axes == 0:
            _, horizon = drag_horizon(horizon, WHITE_DIMMED)

        # Draw origin
        _, screen_origin = drag_point("origin###origin", screen_origin)

        # FOV slider (only editable when FOV cannot be estimated)
        can_estimate_fov = num_active_axes >= 2
        if can_estimate_fov:
            imgui.text(f"FOV: {fov:.2f}° (estimated)")
        else:
            _, fov = imgui.slider_float("FOV", fov, 20.0, 120.0, "%.2f")
        
        _, distance = imgui.drag_float("distance", distance, 0.1, 0.1, 20.0, "%.2f")

        # Estimate camera parameters
        try:
            estimate = camera_estimator.estimate_camera(
                screen_origin=screen_origin,
                distance=distance,
                vanishing_lines=vanishing_lines,
                use_vanishing_lines=use_vanishing_lines,
                horizon=horizon if num_active_axes == 0 else None,
                provided_fov=fov if not can_estimate_fov else None
            )
            
            # Update FOV if it was estimated
            if estimate.fov is not None:
                fov = estimate.fov
            
            # Display estimated parameters
            imgui.separator()
            imgui.text("Estimated Camera Parameters:")
            imgui.text(f"Position: ({estimate.position.x:.2f}, {estimate.position.y:.2f}, {estimate.position.z:.2f})")
            imgui.text(f"Pitch: {math.degrees(estimate.pitch):.2f}°")
            imgui.text(f"Yaw: {math.degrees(estimate.yaw):.2f}°")
            imgui.text(f"Roll: {math.degrees(estimate.roll):.2f}°")
            if estimate.fov:
                imgui.text(f"FOV: {estimate.fov:.2f}°")
            
            # Set up camera for 3D rendering
            camera = Camera()
            camera.setAspectRatio(size.x / size.y)
            camera.setFoVY(fov)
            
            # Build camera transform from estimated parameters
            camera_pos = estimate.position
            
            # Create rotation matrix from pitch, yaw, roll
            rotation = (
                glm.rotate(glm.mat4(1.0), estimate.yaw, glm.vec3(0, 1, 0)) *
                glm.rotate(glm.mat4(1.0), estimate.pitch, glm.vec3(1, 0, 0)) *
                glm.rotate(glm.mat4(1.0), estimate.roll, glm.vec3(0, 0, 1))
            )
            
            translation = glm.translate(glm.mat4(1.0), camera_pos)
            camera.transform = translation * rotation
            
        except Exception as e:
            imgui.text(f"Error estimating camera: {str(e)}")
            # Fallback to your original manual calculation
            camera = Camera()
            camera.setAspectRatio(size.x / size.y)
            camera.setFoVY(fov)
            
            # Your original calculation code here...
            horizon_ndc_dy = (principal_point.y - horizon) / (size.y / 2.0)
            camera_pitch = math.atan2(-horizon_ndc_dy * math.tan(math.radians(fov) / 2), 1.0)
            
            # Original position calculation...
            origin_ndc_x = (screen_origin.x - principal_point.x) / (size.x / 2.0)
            origin_ndc_y = (principal_point.y - screen_origin.y) / (size.y / 2.0)
            
            aspect = size.x / size.y
            tan_half_fov = math.tan(math.radians(fov) / 2.0)
            
            ray_x = origin_ndc_x * tan_half_fov * aspect
            ray_y = origin_ndc_y * tan_half_fov
            ray_z = -1.0
            
            ray_length = math.sqrt(ray_x**2 + ray_y**2 + ray_z**2)
            ray_x /= ray_length
            ray_y /= ray_length
            ray_z /= ray_length
            
            cos_pitch = math.cos(camera_pitch)
            sin_pitch = math.sin(camera_pitch)
            
            ray_world_x = ray_x
            ray_world_y = ray_y * cos_pitch - ray_z * sin_pitch
            ray_world_z = ray_y * sin_pitch + ray_z * cos_pitch
            
            camera_pos_x = -distance * ray_world_x
            camera_pos_y = -distance * ray_world_y
            camera_pos_z = -distance * ray_world_z
            
            camera_forward = glm.vec3(0, math.sin(camera_pitch), -math.cos(camera_pitch))
            camera_up = glm.vec3(0, math.cos(camera_pitch), math.sin(camera_pitch))
            camera_right = glm.vec3(1, 0, 0)
            
            rotation_matrix = glm.mat4(
                glm.vec4(camera_right, 0),
                glm.vec4(camera_up, 0),
                glm.vec4(-camera_forward, 0),
                glm.vec4(0, 0, 0, 1)
            )
            
            translation = glm.translate(glm.mat4(1.0), glm.vec3(camera_pos_x, camera_pos_y, camera_pos_z))
            camera.transform = translation * rotation_matrix

        # ...existing rendering code...
        # Update GL viewport
        pos = imgui.get_item_rect_min()
        display_size = imgui.get_io().display_size
        dpi = imgui.get_io().display_framebuffer_scale
        gl_x = int(pos.x * dpi.x)
        gl_y = int((display_size.y - pos.y - size.y) * dpi.y)
        gl_width = int(display_size.x * dpi.x)
        gl_height = int(display_size.y * dpi.y)
        
        ctx.viewport = (0, 0, gl_width, gl_height)

        # Render Scene to framebuffer
        fbo.use()
        fbo.clear(0.1, 0.1, 0.1, 0.0)
        ctx.enable(moderngl.DEPTH_TEST)
        
        scene_renderer.render(camera)
        
        # Restore default framebuffer
        ctx.screen.use()
        
        # Display the framebuffer texture in ImGui
        texture = fbo.color_attachments[0]
        texture_ref = imgui.ImTextureRef(texture.glo)
        
        imgui.set_cursor_pos(imgui.ImVec2(0,0))
        imgui.image(
            texture_ref,
            imgui.ImVec2(size.x, size.y),
            uv0=imgui.ImVec2(0, 1),
            uv1=imgui.ImVec2(1, 0)
        )

    imgui.end_child()

    

if __name__ == "__main__":
    immapp.run(gui, window_title="ImGui Bundle - 2D Points & 3D Scene", window_size=(800, 800))