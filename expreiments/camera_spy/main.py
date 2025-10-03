from imgui_bundle import imgui, immapp
from core import LineSegment, Point2D
from widgets import drag_points
import math
import numpy as np
import moderngl
import struct
import OpenGL.GL as gl

## 3D Scene Setup (Simple software renderer)

## ModernGL 3D Scene Implementation

from pylive.render_engine.camera import Camera
from contextlib import contextmanager

class ModernGLScene:
    def __init__(self):
        self.ctx = None
        self.program = None
        self.vao = None
        self.vbo = None
        self.ibo = None
        self.texture = None
        self.fbo = None
        self.color_attachment = None
        self.depth_attachment = None
        self.initialized = False

        # Camera
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.zoom = 3.0
        self.auto_rotate = False
        
    def initialize_gl(self, width, height):
        if self.initialized:
            return
            
        try:
            # Use the existing OpenGL context instead of creating a standalone one
            self.ctx = moderngl.create_context()
            
            # Vertex shader
            vertex_shader = '''
            #version 330 core
            
            in vec3 position;
            in vec3 color;
            
            uniform mat4 mvp;
            
            out vec3 v_color;
            
            void main() {
                gl_Position = mvp * vec4(position, 1.0);
                v_color = color;
            }
            '''
            
            # Fragment shader
            fragment_shader = '''
            #version 330 core
            
            in vec3 v_color;
            out vec4 fragColor;
            
            void main() {
                fragColor = vec4(v_color, 1.0);
            }
            '''
            
            # Create shader program
            self.program = self.ctx.program(
                vertex_shader=vertex_shader,
                fragment_shader=fragment_shader
            )
            
            # Create a cube with colored vertices
            vertices = np.array([
                # Position (x,y,z) + Color (r,g,b)
                # Front face
                [-1, -1,  1,  1.0, 0.0, 0.0],  # red
                [ 1, -1,  1,  0.0, 1.0, 0.0],  # green
                [ 1,  1,  1,  0.0, 0.0, 1.0],  # blue
                [-1,  1,  1,  1.0, 1.0, 0.0],  # yellow
                
                # Back face
                [-1, -1, -1,  1.0, 0.0, 1.0],  # magenta
                [ 1, -1, -1,  0.0, 1.0, 1.0],  # cyan
                [ 1,  1, -1,  1.0, 1.0, 1.0],  # white
                [-1,  1, -1,  0.5, 0.5, 0.5],  # gray
            ], dtype=np.float32)
            
            # Indices for cube edges (wireframe)
            indices = np.array([
                # Front face edges
                0, 1,  1, 2,  2, 3,  3, 0,
                # Back face edges  
                4, 5,  5, 6,  6, 7,  7, 4,
                # Connecting edges
                0, 4,  1, 5,  2, 6,  3, 7
            ], dtype=np.uint32)
            
            # Create buffers
            self.vbo = self.ctx.buffer(vertices.tobytes())
            self.ibo = self.ctx.buffer(indices.tobytes())
            
            # Create vertex array object
            self.vao = self.ctx.vertex_array(
                self.program,
                [(self.vbo, '3f 3f', 'position', 'color')],
                self.ibo
            )
            
            # Create framebuffer for offscreen rendering
            self.create_framebuffer(width, height)
            
            self.initialized = True
            
        except Exception as e:
            print(f"ModernGL initialization error: {e}")
            self.initialized = False
    
    def create_framebuffer(self, width, height):
        if width <= 0 or height <= 0:
            return
            
        # Clean up old framebuffer
        if self.fbo:
            self.fbo.release()
        if self.color_attachment:
            self.color_attachment.release()
        if self.depth_attachment:
            self.depth_attachment.release()
            
        # Create color texture
        self.color_attachment = self.ctx.texture((width, height), 4)
        self.color_attachment.filter = (moderngl.LINEAR, moderngl.LINEAR)
        
        # Create depth texture
        self.depth_attachment = self.ctx.depth_texture((width, height))
        
        # Create framebuffer
        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.color_attachment],
            depth_attachment=self.depth_attachment
        )
        
    def render_to_texture(self, width, height, camera:Camera):
        if not self.initialized:
            self.initialize_gl(width, height)
            
        if not self.initialized or width <= 0 or height <= 0:
            return None
            
        # Resize framebuffer if needed
        if (self.fbo.width != width or self.fbo.height != height):
            self.create_framebuffer(width, height)
            
        # Save current OpenGL state
        prev_viewport = gl.glGetIntegerv(gl.GL_VIEWPORT)
        prev_fbo = gl.glGetIntegerv(gl.GL_FRAMEBUFFER_BINDING)
        
        try:
            # Bind our framebuffer
            self.fbo.use()
            
            # Set viewport
            self.ctx.viewport = (0, 0, width, height)
            
            # Enable depth testing
            self.ctx.enable(moderngl.DEPTH_TEST)
            self.ctx.enable(moderngl.BLEND)
            
            # Clear
            self.ctx.clear(0.1, 0.1, 0.1, 0.0)
            
            # Update MVP matrix using camera
            camera.setAspectRatio(width / height if height > 0 else 1.0)
            proj = camera.projectionMatrix()
            view = camera.viewMatrix()
            mvp = proj * view  # glm supports * for matrix multiplication

            # set program uniforms
            self.program['mvp'].write(mvp)
            
            # Render wireframe
            self.vao.render(moderngl.LINES)
            
            # Return the OpenGL texture ID for direct display in ImGui
            texture_id = self.color_attachment.glo
            
            return texture_id
            
        finally:
            # Restore previous OpenGL state
            gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, prev_fbo)
            gl.glViewport(prev_viewport[0], prev_viewport[1], prev_viewport[2], prev_viewport[3])


# Global 3D scene instances
import glm
from calibrate_camera import compute_vanishing_point, estimate_focal_length, compute_camera_orientation
 


def _render_to_texture(scene:ModernGLScene, camera:Camera, width:int, height:int)->imgui.ImTextureRef:
    texture_id = scene.render_to_texture(width, height, camera)
    if texture_id is not None and texture_id > 0:
        texture_ref = imgui.ImTextureRef(texture_id)
        return texture_ref
    else:
        return None
    
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
from dataclasses import dataclass
from typing import Tuple, List
import pickle
Point2D = Tuple[float, float]

@dataclass
class LineSegment:
    start: Point2D
    end: Point2D

    def __iter__(self):
        return iter((self.start, self.end))



@dataclass
class State:
    x_lines: List[LineSegment]
    y_lines: List[LineSegment]
    z_lines: List[LineSegment]
    principal_point: Point2D = (500, 500)  # This is your principal point
    origin: Point2D = (500, 500)  # This the 3D origin point
    @classmethod
    def open(cls, filename: Path) -> "State":
        with open(filename, "rb") as f:
            return pickle.load(f)

    def write(self, filename: Path):
        with open(filename, "wb") as f:
            pickle.dump(self, f)

try:
    state = State.open("camera_lines.pkl")
except Exception as e:
    print(f"Could not open state file: {e}")
    state = State(
        x_lines=[LineSegment((100,100),(200,200)), LineSegment((100,100),(200,200))],
        y_lines=[LineSegment((300,100),(400,200)), LineSegment((350,50),(450,150))], 
        z_lines=[],
        principal_point=(500,500),
        origin=(500, 500)
    )

x = 0.5
y = 0.5
selection: List[int] = []

camera = Camera()
camera.setPosition((0,0,5))
scene = ModernGLScene()

def drag_point(label:str, point:imgui.ImVec2)->Tuple[bool, imgui.ImVec2]:
    new_point = imgui.ImVec2(point.x, point.y)
    changed = False
    store_cursor_pos = imgui.get_cursor_pos()
    imgui.set_cursor_pos(point)
    imgui.button(label)
    if imgui.is_item_active():
        delta = imgui.get_mouse_drag_delta()
        imgui.reset_mouse_drag_delta()
        new_point.x += delta.x
        new_point.y += delta.y
        changed = True

    imgui.set_cursor_pos(store_cursor_pos)
    return changed, new_point

## gui loop
def gui():
    global x, y, def_lines, selection, camera, scene
    
    if imgui.begin_child("3d_viewport", imgui.ImVec2(0, 0)):
        # calc size
        available_size = imgui.get_content_region_avail()
        size = imgui.ImVec2(available_size.x, available_size.y - 20)  # Leave some space for text overlay
        resolution =  int(size.x), int(size.y)

        if resolution[0] <= 0 or resolution[1] <= 0:
            imgui.text("Invalid viewport size")
            return False, camera
        
        # Calculate principal point at the center of the viewport
        principal_point = (resolution[0] / 2, resolution[1] / 2)
        

        io = imgui.get_io()
        if io.key_alt:
            # Camera Controls
            imgui.set_cursor_pos(imgui.ImVec2(0,0))
            delta = touch_pad("Touch Pad", size)
            camera.orbit(-0.3 * delta.x, -0.3 * delta.y)
        else:
            # Point Controls
            axis_changed = False
            for name,  axis_lines in zip(["x", "y", "z"], [state.x_lines, state.y_lines, state.z_lines]):
                for i, linesegment in enumerate(axis_lines):

                    start_changed, new_start_point = drag_point(f"{name}-start{i}", imgui.ImVec2(linesegment.start[0], linesegment.start[1]))
                    linesegment.start = new_start_point.x, new_start_point.y

                    end_changed, new_end_point = drag_point(f"{name}-end{i}", imgui.ImVec2(linesegment.end[0], linesegment.end[1]))
                    linesegment.end = new_end_point.x, new_end_point.y

                    if start_changed or end_changed:
                        axis_changed = True
            if axis_changed:
                state.write("camera_lines.pkl")
            
        ## draw axis lines
        draw_list = imgui.get_window_draw_list()
        for lines in state.x_lines:
            p0 = lines.start
            p1 = lines.end
            color = imgui.color_convert_float4_to_u32((1,0,0, 0.5))
            draw_list.add_line(imgui.ImVec2(*p0), imgui.ImVec2(*p1), color, 2)

        for lines in state.y_lines:
            p0 = lines.start
            p1 = lines.end
            color = imgui.color_convert_float4_to_u32((0,1,0, 0.5))
            draw_list.add_line(imgui.ImVec2(*p0), imgui.ImVec2(*p1), color, 2)

        for lines in state.z_lines:
            p0 = lines.start
            p1 = lines.end
            color = imgui.color_convert_float4_to_u32((0,0,1, 0.5))
            draw_list.add_line(imgui.ImVec2(*p0), imgui.ImVec2(*p1), color, 2)

        # compute vanishing points
        vanishing_points = {"X": None, "Y": None, "Z": None}
        for axis, lines in zip(["X", "Y", "Z"], [state.x_lines, state.y_lines, state.z_lines]):
            try:
                vp:Point2D = compute_vanishing_point(lines)
                vanishing_points[axis] = vp
            except Exception as e:
                imgui.text(f"Error computing {axis} VP: {e}")

        # draw vanishing points
        for axis, vp in vanishing_points.items():
            if vp is None:
                continue
            imgui.text(f"{axis} VP: ({int(vp[0])},{int(vp[1])})")
            color_map = {"X": (1,0,0), "Y": (0,1,0), "Z": (0,0,1)}

            color = imgui.color_convert_float4_to_u32((*color_map.get(axis,(1,1,1)), 1.0))
            draw_list.add_circle_filled(imgui.ImVec2(vp[0], vp[1]), 5, color)
            draw_list.add_text(imgui.ImVec2(vp[0]+5, vp[1]-5), color, f"{axis} VP ({int(vp[0])},{int(vp[1])})")

        for lines, vp in zip([state.x_lines, state.y_lines, state.z_lines], vanishing_points.values()):
            try:
                for line in lines:
                    p0 = line.start
                    p1 = line.end
                    color = imgui.color_convert_float4_to_u32((1,1,1, 0.2))
                    closest_point = None
                    def dist(p:Point2D, q:Point2D):
                        return math.sqrt((p[0]-q[0])**2 + (p[1]-q[1])**2)
                    closest_point = sorted([line.start, line.end], key=lambda p: dist(p, vp))[0]
                    draw_list.add_line(imgui.ImVec2(*closest_point), imgui.ImVec2(*vp), color, 1)
            except Exception as e:
                pass

        # Draw principal point at center
        draw_list.add_circle(imgui.ImVec2(principal_point[0], principal_point[1]), 8, 
                            imgui.color_convert_float4_to_u32((1, 1, 0, 1)), 2)

        # Estimate focal length from vanishing points
        from itertools import combinations
        focal_lengths = []
        try:
            for vp1, vp2 in combinations([vp for vp in vanishing_points.values() if vp is not None], 2):
                focal_length = estimate_focal_length(vp1, vp2, principal_point)
                focal_lengths.append(focal_length)

            focal_length = np.median(focal_lengths) if focal_lengths else 1000.0
        except Exception as e:
            imgui.text(f"Error estimating focal length: {e}")
            focal_length = 1000.0
        try:
            rotation_matrix = compute_camera_orientation([vp for vp in vanishing_points.values() if vp is not None], focal_length, principal_point)
        except Exception as e:
            imgui.text(f"Error computing rotation matrix: {e}")
            rotation_matrix = np.eye(3)

        imgui.text(f"Focal Length: {focal_length:.2f}")
        imgui.text(f"Principal Point: ({principal_point[0]:.2f}, {principal_point[1]:.2f})")
        imgui.text(f"Rotation Matrix:\n{rotation_matrix}")

        # Update camera intrinsics and extrinsics
        R = glm.transpose(glm.mat3(*rotation_matrix.flatten()))
        transform = glm.mat4(R)
        
        ndc_x = (state.origin[0] - principal_point[0]) / principal_point[0]
        ndc_y = -(state.origin[1] - principal_point[1]) / principal_point[1]  # Flip Y
        

        # Using the forward direction and assuming distance d from origin:
        forward = glm.vec3(R[2])  # Camera's forward direction
        right = glm.vec3(R[0])    # Camera's right direction
        up = glm.vec3(R[1])       # Camera's up direction
        
        # Calculate camera position at distance 1 from origin
        # adjusted by the NDC offset to make origin project to the desired screen point
        distance = 5.0  # Distance from origin
        
        # The offset in camera space needed to shift the projected origin
        # tan(half_fov) relates NDC to camera space at unit depth
        half_fov_y = math.atan(resolution[1] / (2.0 * focal_length))
        half_fov_x = math.atan(resolution[0] / (2.0 * focal_length))
        
        # Camera-space offset for origin to appear at ndc_x, ndc_y
        offset_right = ndc_x * distance * math.tan(half_fov_x)
        offset_up = ndc_y * distance * math.tan(half_fov_y)
        
        # Camera position: back from origin by distance, offset by screen position
        camera_position = -forward * distance + right * offset_right + up * offset_up
        
        camera.transform = transform
        camera.setPosition(camera_position)
        camera.setFOV(2 * math.degrees(half_fov_y))  # Vertical FOV
        camera.setAspectRatio(resolution[0] / resolution[1] if resolution[1] > 0 else 1.0)
        
        imgui.text(f"Camera Position: {camera.getPosition()}")
        imgui.text(f"Camera Distance: {camera.getDistance():.2f}")
        imgui.text(f"Camera Orientation:\n{camera.transform}")

        origin_changed, new_origin = drag_point("origin", imgui.ImVec2(state.origin[0], state.origin[1]))
        if origin_changed:
            state.origin = (new_origin.x, new_origin.y)
            state.write("camera_lines.pkl")
        # Display the 3D scene
        imgui.set_cursor_pos(imgui.ImVec2(0,0))
        # Render to texture and get OpenGL texture ID
        texture_ref = _render_to_texture(scene, camera, resolution[0], resolution[1])
        assert texture_ref is not None
        imgui.image(
            texture_ref,  # ImTextureRef object
            imgui.ImVec2(resolution[0], resolution[1]),  # Size
            imgui.ImVec2(0, 1),  # UV0 (top-left) - flipped vertically
            imgui.ImVec2(1, 0)   # UV1 (bottom-right) - flipped vertically
        )


    imgui.end_child()

    

if __name__ == "__main__":
    immapp.run(gui, window_title="ImGui Bundle - 2D Points & 3D Scene", window_size=(800, 700))