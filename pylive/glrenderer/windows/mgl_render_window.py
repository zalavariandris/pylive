import moderngl_window as mglw
from typing import List, Tuple, override
from pylive.glrenderer.utils.camera import Camera
import glm

class MGLRenderWindow(mglw.WindowConfig):
    gl_version = (4, 1)  # macOS compatible
    title = "ModernGL Window"
    window_size = (800, 600)
    aspect_ratio = None
    resizable = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @override
    def on_render(self, time, frame_time):
        return super().on_render(time, frame_time)
    
    @override
    def on_resize(self, width: int, height: int):
        return super().on_resize(width, height)
    

class MGLCameraWindow(MGLRenderWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Setup camera
        self.camera = Camera()
        self.camera.setPosition(glm.vec3(1.5, 2.5, 4.5))
        self.camera.lookAt(glm.vec3(0, 0, 0), glm.vec3(0, 1, 0))

    @override
    def on_mouse_drag_event(self, x, y, dx, dy):
        self.camera.orbit(-dx, -dy, target=(0,0,0))
        return super().on_mouse_drag_event(x, y, dx, dy)

    @override
    def on_mouse_scroll_event(self, x_offset: float, y_offset: float):
        self.camera.dolly(y_offset * 0.1)
        return super().on_mouse_scroll_event(x_offset, y_offset)

    def on_resize(self, width: int, height: int):
        self.camera.setAspectRatio(width / height)