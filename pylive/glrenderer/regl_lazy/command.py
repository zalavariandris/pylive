from typing import Dict
import moderngl
import numpy as np
from typing import Any, Tuple, List
import textwrap
from .resources import Framebuffer

type AttributeType = Tuple[moderngl.Buffer, str, str]

class Command:
    def __init__(self, 
            vert:str, 
            frag:str, 
            uniforms:Dict[str, Any], 
            attributes:Dict[str, np.ndarray|list], 
            count:int,
            framebuffer:Framebuffer=None
        ):
        super().__init__()
        self.vert = textwrap.dedent(vert)
        self.frag = textwrap.dedent(frag)
        self.uniforms = uniforms
        self.attributes = attributes
        self.count = count
        self.framebuffer = framebuffer

        # GL OBJECTS
        self._handle: Tuple[moderngl.Program, List[AttributeType], moderngl.VertexArray] = None
    
    def allocate(self):
        ctx = moderngl.get_context()
        assert ctx is not None, "Moderngl context is not initialized."

        program = ctx.program(self.vert, self.frag)

        attributes: List[AttributeType] = []
        for name, data in self.attributes.items():
            buffer = ctx.buffer(data.tobytes())
            type_string = f"{data.shape[1]}{data.dtype.char}"
            attr_buffer = (buffer, type_string, name)
            attributes.append(attr_buffer)

        vao = ctx.vertex_array(
            program,
            attributes,
            mode=moderngl.TRIANGLES
        )

        return (program, attributes, vao)

    def __call__(self, *, uniforms:Dict[str, Any]=None, attributes:Dict[str, np.ndarray|list]=None, count:int=None):
        # merge call-time parameters
        uniforms = uniforms or {}
        uniforms = {**self.uniforms, **uniforms} # merge initial uniforms with call-time uniforms
        if attributes is not None:
            raise NotImplementedError("Updating attributes at call time is not implemented yet.")
        
        attributes = attributes or {}
        attributes = {**self.attributes, **attributes} # merge initial attributes with call-time attributes
        count = count or self.count

        # lazy setup
        if self._handle is None:
            self._handle = self.allocate()
        prog, attrs, vao = self._handle

        # validate input parameters
        self._validate_uniforms()
        self._validate_attributes()

        # set uniforms
        for key, value in uniforms.items():
            prog[key].write(value)

        ctx = moderngl.get_context()

        if self.framebuffer:
            fbo = self.framebuffer.get()
            fbo.use()
        else:
            ctx.screen.use()
        vao.render()
        if self.framebuffer:
            ctx.screen.use()
        
    def __del__(self):
        if self._handle:
            program, attributes, vao = self._handle
            program.release()
            vao.release()

            for buffer, type_string, name in attributes:
                buffer.release()


    def _validate_uniforms(self):
        for uniform in self.uniforms.values():
            ... #TODO: Validate uniform values. allow tuples, numpy arrays and glm values.

    def _validate_attributes(self):
        if not all(isinstance(buffer, np.ndarray) or isinstance(buffer, list) for buffer in self.attributes.values()):
            raise ValueError(f"All buffer must be np.ndarray or a List, got:{self.attributes.values()}")

        if not all(len(buffer.shape) == 2 for buffer in self.attributes.values()):
            # see  opengl docs: https://registry.khronos.org/OpenGL-Refpages/gl4/html/glVertexAttribPointer.xhtml
            # size must be aither 1,2,3 or 4
            raise ValueError(f"The buffers must be 2 dimensional.") #TODO: accep 1 or a flat array for 1 dimensional data.

        if not all(buffer.shape[1] in {1,2,3,4} for buffer in self.attributes.values()):
            # see  opengl docs: https://registry.khronos.org/OpenGL-Refpages/gl4/html/glVertexAttribPointer.xhtml
            # size must be aither 1,2,3 or 4
            raise ValueError(f"The number of components per generic vertex attribute. Must be 1, 2, 3, or 4.")

        supported_datatypes = {'f','u'}
        for buffer in self.attributes.values():
            if buffer.dtype.char not in supported_datatypes:
                raise ValueError(f"Datatype '{buffer.dtype}' is not supported.")

