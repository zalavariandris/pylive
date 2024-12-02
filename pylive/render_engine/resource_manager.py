from typing import *
import weakref
import moderngl

### GL RESOURCE OBJECTS ###

type ShaderSource = str

class Framebuffer:
    def __init__(self, resource_manager: 'ResourceManager', 
		color_attachments: List[moderngl.Texture|moderngl.Renderbuffer] = (), 
		depth_attachment: Optional[moderngl.Texture|moderngl.Renderbuffer] = None
    ):
        self.resource_manager = weakref.ref(resource_manager)
        self._handle = resource_manager.mgl.framebuffer(
        	color_attachments, 
        	depth_attachment)

    def release(self):
        self._handle.release()

    def handle(self):
        return self._handle

class Buffer:
    def __init__(self, resource_manager: 'ResourceManager', 
    	data: Optional[Any] = None, *, 
		reserve: int = 0, 
		dynamic: bool = False
	):
        self.resource_manager = weakref.ref(resource_manager)
        self._handle = resource_manager.mgl.buffer(data,
			reserve,
			dynamic)

    def release(self):
        self._handle.release()

    def handle(self):
        return self._handle

class Program:
    def __init__(self, resource_manager: 'ResourceManager',
		vertex_shader: ShaderSource, 
		fragment_shader: Optional[ShaderSource] = None, 
		geometry_shader: Optional[ShaderSource] = None, 
		tess_control_shader: Optional[ShaderSource] = None, 
		tess_evaluation_shader: Optional[ShaderSource] = None, 
		varyings: Tuple[str, ...] = (), 
		fragment_outputs: Optional[Dict[str, int]] = None, 
		varyings_capture_mode: str = 'interleaved'
    	):
        self.resource_manager = weakref.ref(resource_manager)
        self._handle = resource_manager.mgl().program(
			vertex_shader,
			fragment_shader,
			geometry_shader,
			tess_control_shader,
			tess_evaluation_shader,
			varyings,
			fragment_outputs,
			varyings_capture_mode)

    def release(self):
        self._handle.release()

    def handle(self):
        return self._handle

class VertexArray:
    def __init__(self, resource_manager: 'ResourceManager', 
    	program: moderngl.Program, 
		buffer: moderngl.Buffer, 
		*attributes: Union[List[str], Tuple[str, ...]], 
		index_buffer: Optional[moderngl.Buffer] = None, 
		index_element_size: int = 4, 
		mode: Optional[int] = None
    ):
        self.resource_manager = weakref.ref(resource_manager)
        self._handle = resource_manager.mgl().vertex_array(
        	program,
			buffer,
			*attributes,
			index_buffer=index_buffer,
			index_element_size=index_element_size,
			mode=mode)

    def release(self):
        self._handle.release()

    def handle(self):
        return self._handle

class Texture:
    def __init__(self, resource_manager: 'ResourceManager',
    	size: Tuple[int, int],
		components: int,
		data: Optional[Any] = None, 
		*,
		samples: int = 0,
		alignment: int = 1,
		dtype: str = 'f1',
		internal_format: Optional[int] = None
	):
        self.resource_manager = weakref.ref(resource_manager)
        self._handle = resource_manager.texture(size,
			components,
			data,
			samples=samples,
			alignment=alignment,
			dtype=dtype,
			internal_format=internal_format)

    def release(self):
        self._handle.release()

    def handle(self):
        return self._handle

class TextureArray:
    def __init__(self, resource_manager: 'ResourceManager', 
		size: Tuple[int, int, int],
		components: int,
		data: Optional[Any] = None,
		*,
		alignment: int = 1,
		dtype: str = 'f1'
    	):
        self.resource_manager = weakref.ref(resource_manager)
        self._handle = resource_manager.mgl().texture_array(size,
			components,
			data,
			alignment,
			dtype)

    def release(self):
        self._handle.release()

    def handle(self):
        return self._handle

class Texture3D:
    def __init__(self, resource_manager: 'ResourceManager',
			size: Tuple[int, int, int], 
			components: int, 
			data: Optional[Any] = None, 
			*,
			alignment: int = 1,
			dtype: str = 'f1'
    	):
        self.resource_manager = weakref.ref(resource_manager)
        self._handle = resource_manager.mgl().texture3d(
        	size,
        	components,
        	data,
        	alignment=alignment, 
        	dtype=dtype)

    def release(self):
        self._handle.release()

    def handle(self):
        return self._handle

class TextureCube:
    def __init__(self, resource_manager: 'ResourceManager', 
		size: Tuple[int, int], 
		components: int, 
		data: Optional[Any] = None,
		*,
		alignment: int = 1,
		dtype: str = 'f1',
		internal_format: Optional[int] = None
    ):
        self.resource_manager = weakref.ref(resource_manager)
        self._handle = resource_manager.mgl().texture_cube(
        	size,
			components,
			data,
			alignment=alignment,
			dtype=dtype,
			internal_format=internal_format)

    def release(self):
        self._handle.release()

    def handle(self):
        return self._handle

class Renderbuffer:
    def __init__(self, resource_manager: 'ResourceManager',
    	size: Tuple[int, int],
    	components: int = 4,
    	*,
    	samples: int = 0,
    	dtype: str = 'f1'
    ):
        self.resource_manager = weakref.ref(resource_manager)
        self._handle = resource_manager.mgl().renderbuffer(size,
			components,
			samples=samples,
			dtype=dtype)

    def release(self):
        self._handle.release()

    def handle(self):
        return self._handle


### GL RESOURCE MANAGER ###

class ResourceManager:
	def __init__(self):
		self.buffers = []
		self.programs = []
		self.vertex_arrays = []
		self.textures = []
		self.texture_arrays = []
		self.texture3ds = []
		self.texture_cubes = []
		self.framebuffers = []
		self.renderbuffers = []

		self._mgl = None

	def mgl(self)->moderngl.Context:
		if not self._mgl:
			self._mgl = moderngl.get_context()
		return self._mgl

	def buffer(self, 
		data: Optional[Any] = None, *, 
		reserve: int = 0, 
		dynamic: bool = False
	)->moderngl.Buffer:
		return self.mgl().buffer(data, reserve, dynamic)

	def program(self, *, 
		vertex_shader: ShaderSource, 
		fragment_shader: Optional[ShaderSource] = None, 
		geometry_shader: Optional[ShaderSource] = None, 
		tess_control_shader: Optional[ShaderSource] = None, 
		tess_evaluation_shader: Optional[ShaderSource] = None, 
		varyings: Tuple[str, ...] = (), 
		fragment_outputs: Optional[Dict[str, int]] = None, 
		varyings_capture_mode: str = 'interleaved'
	)->Program:
		program = Program(self,
			vertex_shader,
			fragment_shader,
			geometry_shader,
			tess_control_shader,
			tess_evaluation_shader,
			varyings,
			fragment_outputs,
			varyings_capture_mode)
		self.programs.append(program)
		return program

	def vertex_array(self,
		program: moderngl.Program, 
		buffer: moderngl.Buffer, 
		*attributes: Union[List[str], Tuple[str, ...]], 
		index_buffer: Optional[moderngl.Buffer] = None, 
		index_element_size: int = 4, 
		mode: Optional[int] = None
	) -> VertexArray:
		vao = VertexArray(self, 
			program,
			buffer,
			*attributes,
			index_buffer=index_buffer,
			index_element_size=index_element_size,
			mode=mode)
		self.vertex_arrays.append(vao)
		return vao

	def texture(self,
		size: Tuple[int, int],
		components: int,
		data: Optional[Any] = None, *,
		samples: int = 0,
		alignment: int = 1,
		dtype: str = 'f1',
		internal_format: Optional[int] = None
	)->Texture:
		texture = Texture(self,
			size,
			components,
			data,
			samples=samples,
			alignment=alignment,
			dtype=dtype,
			internal_format=internal_format)
		self.textures.append(texture)
		return texture

	def texture_array(self,
		size: Tuple[int, int, int],
		components: int,
		data: Optional[Any] = None,
		*,
		alignment: int = 1,
		dtype: str = 'f1'
	)->TextureArray:
		return TextureArray(self, 
			size, 
			components, 
			data, 
			alignment=alignment, 
			dtype=dtype)

	def texture3d(self,
		size: Tuple[int, int, int], 
		components: int, 
		data: Optional[Any] = None, 
		*,
		alignment: int = 1,
		dtype: str = 'f1'
	)->Texture3D:
		texture3d = Texture3D(self,
			size,
			components,
			data,
			alignment=alignment,
			dtype=dtype)
		self.texture3ds.append(texture3d)
		return texture3d

	def texture_cube(self, 
		size: Tuple[int, int], 
		components: int, 
		data: Optional[Any] = None,
		*,
		alignment: int = 1,
		dtype: str = 'f1',
		internal_format: Optional[int] = None
	)->TextureCube:
		return TextureCube(self, size,
			components,
			data,
			alignment=alignment,	
			dtype=dtype,
			internal_format=internal_format)

	def framebuffer(self,
		color_attachments: List[moderngl.Texture|moderngl.Renderbuffer] = [], 
		depth_attachment: Optional[moderngl.Texture|moderngl.Renderbuffer] = None
	)->Framebuffer:
		framebuffer = Framebuffer(self, 
			color_attachments, 
			depth_attachment)
		self.framebuffers.append(framebuffer)
		return framebuffer

	def destroy(self):
		for buffer in self.buffers:
			buffer.release()
		for program in self.programs:
			program.release()
		for vertex_array in self.vertex_arrays:
			vertex_array.release()
		for texture in self.textures:
			texture.release()
		for texture_array in self.texture_arrays:
			texture_array.release()
		for texture3d in self.texture3ds:
			texture3d.release()
		for texture_cube in self.texture_cubes:
			texture_cube.release()
		for framebuffer in self.framebuffers:
			framebuffer.release()
		for renderbuffer in self.renderbuffers:
			renderbuffer.release()

	def __del__(self):
		self.destroy()
