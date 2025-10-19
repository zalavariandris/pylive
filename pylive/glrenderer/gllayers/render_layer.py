from abc import ABC, abstractmethod
from textwrap import dedent
import moderngl


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
    def setup(self):
        ...

    @abstractmethod
    def render(self):
        ...

    @abstractmethod
    def release(self):
        ...
