import logging
import time
from typing import *
import math
import numpy as np
import glm # or import pyrr !!!! TODO: checkout pyrr
import trimesh
import moderngl
from textwrap import dedent
from pylive.render_engine.camera import Camera

logger = logging.getLogger(__name__)


from abc import ABC, abstractmethod
class RenderLayer(ABC):
    """ Abstract base class for render layers. 
    RenderLayers are the basic building blocks of the rendering engine.
    Each layer encapsulates its own shaders, buffers, and rendering logic.
    """
    
    FLAT_VERTEX_SHADER = dedent('''
        #version 330 core
        // input attributes
        layout(location = 0) in vec3 position;
                             
        // uniform variables
        uniform mat4 view;
        uniform mat4 projection;

        // main function
        void main() {
            gl_Position = projection * view * vec4(position, 1.0);
        }
    ''')

    FLAT_FRAGMENT_SHADER = dedent('''
        #version 330 core
        // output attributes
        layout (location = 0) out vec4 out_color;
                               
        // uniform variables
        uniform vec4 color;
                               
        // main function
        void main() {
            out_color = color;
        }
    ''')

    @abstractmethod
    def setup(self, ctx:moderngl.Context):
        ...

    @abstractmethod
    def render(self):
        ...

    @abstractmethod
    def destroy(self):
        ...


class TriangleLayer(RenderLayer):
    """ A simple render layer that draws a triangle.
    """

    def __init__(self, camera:Camera|None=None) -> None:
        super().__init__()
        self.camera = camera or Camera()
        self.program = None

    @override
    def setup(self, ctx:moderngl.Context):
        logger.info(f"Setting up {self.__class__.__name__}...")
        start_time = time.time()
        
        logger.info(f"{self.__class__.__name__}: Compiling shaders...")
        shader_start = time.time()
        self.program = ctx.program(
            vertex_shader=self.FLAT_VERTEX_SHADER,
            fragment_shader=self.FLAT_FRAGMENT_SHADER
        )
        shader_time = time.time() - shader_start
        logger.info(f"{self.__class__.__name__}: Shader compilation took {shader_time:.3f}s")

        # triangle
        vertices = np.array([
             0.0, 0.0,  0.4,   # Vertex 1
            -0.4, 0.0, -0.3,   # Vertex 2
             0.4, 0.0, -0.3    # Vertex 3
        ], dtype=np.float32)

        self.vbo = ctx.buffer(vertices.tobytes())

        self.vao = ctx.vertex_array(
            self.program,
            [
                (self.vbo, '3f', 'position'),
            ],
            mode=moderngl.TRIANGLES
        )
        
        setup_time = time.time() - start_time
        logger.info(f"{self.__class__.__name__} setup completed in {setup_time:.3f}s")

    @override
    def destroy(self):
        if self.program:
            self.program.release()
            self.program = None
        if self.vbo:
            self.vbo.release()
            self.vbo = None
        if self.vao:
            self.vao.release()
            self.vao = None

    @override
    def render(self, **kwargs):
        self.program['view'].write(self.camera.viewMatrix())
        self.program['projection'].write(self.camera.projectionMatrix())
        self.program['color'].write(glm.vec4(1.0, 1.0, 0.3, 1.0))
        self.vao.render()


class TrimeshLayer(RenderLayer):
    """ A render layer that draws any trimesh.Trimesh mesh.
    """
    def __init__(self, mesh:trimesh.Trimesh|None=None) -> None:
        super().__init__()
        self.program = None
        self.mesh = mesh

    @override
    def setup(self, ctx:moderngl.Context):
        logger.info(f"Setting up {self.__class__.__name__}...")
        start_time = time.time()
        
        # Setup shaders
        logger.info(f"{self.__class__.__name__}: Compiling shaders...")
        shader_start = time.time()
        self.program = ctx.program(
            vertex_shader=self.FLAT_VERTEX_SHADER,
            fragment_shader=self.FLAT_FRAGMENT_SHADER
        )
        shader_time = time.time() - shader_start
        logger.info(f"{self.__class__.__name__}: Shader compilation took {shader_time:.3f}s")

        # to VAO
        vertices = self.mesh.vertices.flatten().astype(np.float32)
        indices = self.mesh.faces.flatten().astype(np.uint32)
        self.vbo = ctx.buffer(vertices)
        self.ibo = ctx.buffer(indices)

        self.vao = ctx.vertex_array(
            self.program,
            [
                (self.vbo, '3f', 'position'),
            ],
            mode=moderngl.TRIANGLES,
            index_buffer=self.ibo
        )
        
        setup_time = time.time() - start_time
        logger.info(f"{self.__class__.__name__} setup completed in {setup_time:.3f}s")

    @override
    def render(self, *, view:glm.mat4=None, projection:glm.mat4=None, color:glm.vec4=None):
        assert self.program is not None
        if view is None:
            view = glm.mat4(1.0)
        if projection is None:
            projection = glm.mat4(1.0)
        if color is None:
            color = glm.vec4(0.5, 0.5, 0.5, 1.0)

        self.program['view'].write(view)
        self.program['projection'].write(projection)
        self.program['color'].write(color)
        
        self.vao.render()

    def destroy(self):
        if self.program:
            self.program.release()
            self.program = None
        if self.vao:
            self.vao.release()
            self.vao = None
        if self.vbo:
            self.vbo.release()
            self.vbo = None
        if self.ibo:
            self.ibo.release()
            self.ibo = None


class GridLayer(RenderLayer):
    """ A render layer that draws a grid on the XZ plane."""
    def __init__(self, XY=False, XZ=True, YZ=False, color=glm.vec4(0.5, 0.5, 0.5, 1.0)):
        super().__init__()
        self.program = None
        self.vao = None
        self.color = color

        self.XY = XY
        self.XZ = XZ
        self.YZ = YZ

        self._initialized = False
        
    def setup(self, ctx):
        logger.info(f"Setting up {self.__class__.__name__}...")
        start_time = time.time()
        
        logger.info(f"{self.__class__.__name__}: Compiling shaders...")
        shader_start = time.time()
        self.program = ctx.program(
            vertex_shader=self.FLAT_VERTEX_SHADER,
            fragment_shader=self.FLAT_FRAGMENT_SHADER
        )
        shader_time = time.time() - shader_start
        logger.info(f"{self.__class__.__name__}: Shader compilation took {shader_time:.3f}s")
        
        all_vertices = []
        
        # XZ grid (horizontal plane, Y=0)
        if self.XZ:
            for x in range(0, 11, 1):
                all_vertices.extend([(x-5, 0, -5), (x-5, 0, +5)])
            for z in range(0, 11, 1):
                all_vertices.extend([(-5, 0, z-5), (+5, 0, z-5)])
        
        # XY grid (vertical plane, Z=0)
        if self.XY:
            for x in range(0, 11, 1):
                all_vertices.extend([(x-5, -5, 0), (x-5, +5, 0)])
            for y in range(0, 11, 1):
                all_vertices.extend([(-5, y-5, 0), (+5, y-5, 0)])
        
        # YZ grid (vertical plane, X=0)
        if self.YZ:
            for y in range(0, 11, 1):
                all_vertices.extend([(0, y-5, -5), (0, y-5, +5)])
            for z in range(0, 11, 1):
                all_vertices.extend([(0, -5, z-5), (0, +5, z-5)])

        # Convert to numpy array and create buffer
        vertices = np.array(all_vertices, dtype=np.float32).flatten()
        self.vbo = ctx.buffer(vertices)

        self.vao = ctx.vertex_array(
            self.program,
            [
                (self.vbo, '3f', 'position'),
            ],
            mode=moderngl.LINES
        )
        self._initialized = True
        
        setup_time = time.time() - start_time
        logger.info(f"{self.__class__.__name__} setup completed in {setup_time:.3f}s")
        
    def render(self, view:glm.mat4, projection:glm.mat4):
        if not self._initialized:
            logging.warning("GridLayer not initialized. Call setup(ctx) before render().")
            return
        self.program['view'].write(view)
        self.program['projection'].write(projection)
        self.program['color'].write(self.color)
        self.vao.render()

    def destroy(self):
        if self.program:
            self.program.release()
        if self.vao:
            self.vao.release()
        if self.vbo:
            self.vbo.release()


class ArrowLayer(RenderLayer):
    """ A render layer that draws an arrow with a flat head, useful for visualizing axes.

    NOTE: BILLBOARD constant and helper functions (decompose, lookAt) are reserved 
    for future billboard/sprite implementation.
    """
    BILLBOARD = dedent('''\
        // Decompose the view matrix to remove its rotational part
        mat4 billboard(mat4 view, vec4 position){
            // Extract translation and scale (ignore rotation) from the view matrix
            mat4 billboardMatrix = mat4(1.0); // Identity matrix for billboard effect
            billboardMatrix[3] = view[3];     // Keep camera's translation
            
            // Compute final position in world space
            return billboardMatrix * vec4(position, 1.0);
        }
    ''')
    FLAT_VERTEX_SHADER = dedent('''\
        #version 330 core

        uniform mat4 view;         // View matrix
        uniform mat4 projection;   // Projection matrix
        uniform mat4 model;        // Model matrix

        layout(location = 0) in vec3 position; // Local vertex position (e.g., quad corners)

        // Function to decompose a matrix into position, rotation, and scale
        void decompose(mat4 M, out vec3 position, out mat3 rotation, out vec3 scale) {
            // Extract translation
            position = vec3(M[3][0], M[3][1], M[3][2]);

            // Extract the upper-left 3x3 matrix for rotation and scale
            mat3 upper3x3 = mat3(M);

            // Extract scale
            scale.x = length(upper3x3[0]); // Length of the X-axis
            scale.y = length(upper3x3[1]); // Length of the Y-axis
            scale.z = length(upper3x3[2]); // Length of the Z-axis

            // Normalize the columns of the 3x3 matrix to remove scaling, leaving only rotation
            rotation = mat3(
                upper3x3[0] / scale.x,
                upper3x3[1] / scale.y,
                upper3x3[2] / scale.z
            );
        }

        // Function to create a lookAt matrix
        mat4 lookAt(vec3 eye, vec3 center, vec3 up) {
            vec3 forward = normalize(center - eye);
            vec3 right = normalize(cross(forward, up));
            vec3 cameraUp = cross(right, forward);

            // Create a rotation matrix
            mat4 rotation = mat4(
                vec4(right, 0.0),
                vec4(cameraUp, 0.0),
                vec4(-forward, 0.0),
                vec4(0.0, 0.0, 0.0, 1.0)
            );

            // Create a translation matrix
            mat4 translation = mat4(
                vec4(1.0, 0.0, 0.0, 0.0),
                vec4(0.0, 1.0, 0.0, 0.0),
                vec4(0.0, 0.0, 1.0, 0.0),
                vec4(-eye, 1.0)
            );

            // Combine rotation and translation
            return rotation * translation;
        }

        void main() {
            // Decompose the inverse of the view matrix to get camera properties
            vec3 eye;
            mat3 rotation;
            vec3 scale;
            decompose(inverse(view), eye, rotation, scale);

            // Create a lookAt matrix (view matrix from camera properties)
            mat4 lookAtMatrix = lookAt(vec3(0.0, 0.0, 0.0), eye, vec3(0.0, 1.0, 0.0));

            // Apply transformations: projection * view * model
            gl_Position = projection * view * model * vec4(position, 1.0);
        }
    ''')
    def __init__(self, model=glm.mat4(1.0), color=glm.vec4(1.0, 1.0, 1.0, 1.0)):
        super().__init__()
        self.program = None
        self.vao = None
        self.model = model
        self.color = color
        
    def setup(self, ctx):
        logger.info(f"Setting up {self.__class__.__name__}...")
        start_time = time.time()
        
        logger.info(f"{self.__class__.__name__}: Compiling shaders...")
        shader_start = time.time()
        self.program = ctx.program(
            vertex_shader=self.FLAT_VERTEX_SHADER,
            fragment_shader=self.FLAT_FRAGMENT_SHADER
        )
        shader_time = time.time() - shader_start
        logger.info(f"{self.__class__.__name__}: Shader compilation took {shader_time:.3f}s")
        
        vertices = np.array([
            (0.0, 0.0, 0.0),  # Bottom of the shaft
            (0.0, 1.0, 0.0),  # Top of the shaft

            (0.0, 1.0, 0.0),  # Top of the shaft
            (-0.1, 0.9, 0.0),  # Left of the arrowhead
            
            (0.0, 1.0, 0.0),  # Top of the shaft
            (0.1, 0.9, 0.0)   # Right of the arrowhead
        ], dtype=np.float32).flatten()
    

        self.vbo = ctx.buffer(vertices)

        self.vao = ctx.vertex_array(
            self.program,
            [
                (self.vbo, '3f', 'position'),
            ],
            mode=moderngl.LINES
        )
        
        setup_time = time.time() - start_time
        logger.info(f"{self.__class__.__name__} setup completed in {setup_time:.3f}s")
        
    def render(self, view:glm.mat4=None, projection:glm.mat4=None):
        self.program['view'].write(view)
        self.program['projection'].write(projection)
        self.program['model'].write(self.model)
        self.program['color'].write(self.color)
        self.vao.render()

    def destroy(self):
        if self.program:
            self.program.release()
            self.program = None
        if self.vao:
            self.vao.release()
            self.vao = None
        if self.vbo:
            self.vbo.release()
            self.vbo = None


class AxesLayer(RenderLayer):
    """ A render layer that draws 3 arrows representing the X, Y, and Z axes.
    """
    def __init__(self):
        super().__init__()

        self.xarrow = ArrowLayer( 
            model=glm.rotate(math.radians(90), glm.vec3(1,0,0)),
            color=glm.vec4(1,0,0,1)
        ) # X

        self.yarrow = ArrowLayer(
            model=glm.mat4(1),
            color=glm.vec4(0,1,0,1),
        ) # Y

        self.zarrow = ArrowLayer( 
            model=glm.rotate(math.radians(90), glm.vec3(0,0,1)),
            color=glm.vec4(0,0,1,1)
        ) # Z

    def setup(self, ctx: moderngl.Context):
        logger.info(f"Setting up {self.__class__.__name__}...")
        start_time = time.time()
        
        self.xarrow.setup(ctx)
        self.yarrow.setup(ctx)
        self.zarrow.setup(ctx)
        
        setup_time = time.time() - start_time
        logger.info(f"{self.__class__.__name__} setup completed in {setup_time:.3f}s")

    def render(self, view:glm.mat4, projection:glm.mat4):
        self.xarrow.render(view, projection)
        self.yarrow.render(view, projection)
        self.zarrow.render(view, projection)

    def destroy(self):
        self.xarrow.destroy()
        self.yarrow.destroy()
        self.zarrow.destroy()


if __name__ == "__main__":
    import moderngl_window as mglw

    class RenderWindow(mglw.WindowConfig):
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
        

    class CameraWindow(RenderWindow):
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


    class RenderLayersExampleWindow(CameraWindow):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
                        
            # Create triangle layer
            self.triangle = TriangleLayer()
            self.triangle.setup(self.ctx)
            self.grid = GridLayer()
            self.grid.setup(self.ctx)
            self.axes = AxesLayer()
            self.axes.setup(self.ctx)
            self.cube = TrimeshLayer(mesh=trimesh.creation.box(extents=(1,1,1)))
            self.cube.setup(self.ctx)
            
            # Enable depth testing
            self.ctx.enable(moderngl.DEPTH_TEST)
        
        def on_render(self, time: float, frametime: float):
            self.ctx.clear(0.1, 0.1, 0.1, 1.0)
            self.triangle.render()
            self.grid.render(self.camera.viewMatrix(), self.camera.projectionMatrix())
            
            self.cube.render(view=self.camera.viewMatrix(), projection=self.camera.projectionMatrix())
            self.ctx.disable(moderngl.DEPTH_TEST)
            self.axes.render(self.camera.viewMatrix(), self.camera.projectionMatrix())
            self.ctx.enable(moderngl.DEPTH_TEST)

    # Run the window
    RenderLayersExampleWindow.run()
