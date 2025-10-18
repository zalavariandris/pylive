from __future__ import annotations
from typing import *
import weakref
import moderngl
import numpy as np
### GL RESOURCE OBJECTS ###

type ShaderSource = str

from abc import ABC, abstractmethod

from typing import TypeVar
Handle = TypeVar("Handle")


from .resources import (
    Texture, 
    TextureArray, 
    Texture3D, 
    TextureCube, 
    Framebuffer, 
    Renderbuffer, 
    Buffer
)

### GL RESOURCE MANAGER ###
class ResourceManager:
    def __init__(self):
        self.buffers:        list[Buffer] =       []
        # self.programs:       list[Program] =      []
        # self.vertex_arrays:  list[VertexArray] =  []
        self.textures:       list[Texture] =      []
        self.texture_arrays: list[TextureArray] = []
        self.texture3ds:     list[Texture3D] =    []
        self.texture_cubes:  list[TextureCube] =  []
        self.framebuffers:   list[Framebuffer] =  []
        self.renderbuffers:  list[Renderbuffer] = []
        
        # weakref caches (for reuse)
        self._buffer_cache = {}
        # self._program_cache = {}

    def buffer(self, 
        data: Optional[Any] = None, *, 
        reserve: int = 0, 
        dynamic: bool = False
    )->Buffer:
        # create cache key
        cache_key = id(data) if isinstance(data, np.ndarray) else None
        if cache_key and cache_key in self._buffer_cache:
            ref = self._buffer_cache[cache_key]
            buf = ref()
            if buf:
                return buf
            
        # create new buffer
        buffer = Buffer(self, data, reserve=reserve, dynamic=dynamic)
        self.buffers.append(buffer)

        # cache buffer
        self._buffer_cache[cache_key] = weakref.ref(buffer)
        return buffer

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
        texture_array = TextureArray(self, 
            size, 
            components, 
            data, 
            alignment=alignment, 
            dtype=dtype)
        self.texture_arrays.append(texture_array)
        return texture_array

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
        texture_cube = TextureCube(self, size,
            components,
            data,
            alignment=alignment,	
            dtype=dtype,
            internal_format=internal_format)
        self.texture_cubes.append(texture_cube)
        return texture_cube

    def framebuffer(self,
        color_attachments: List[moderngl.Texture|moderngl.Renderbuffer] = None, 
        depth_attachment: Optional[moderngl.Texture|moderngl.Renderbuffer] = None
    )->Framebuffer:
        framebuffer = Framebuffer(self, 
            color_attachments, 
            depth_attachment)
        
        self.framebuffers.append(framebuffer)
        return framebuffer

    def renderbuffer(self,
        size: Tuple[int, int],
        components: int = 4,
        *,
        samples: int = 0,
        dtype: str = 'f1'
    )->Renderbuffer:
        renderbuffer = Renderbuffer(self,
            size,
            components,
            samples=samples,
            dtype=dtype)
        self.renderbuffers.append(renderbuffer)
        return renderbuffer

    def destroy(self):
        # release all resources
        for buffer in self.buffers:
            buffer.release()
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

        # clear caches
        self._buffer_cache.clear()
        # self._program_cache.clear()

    def __del__(self):
        self.destroy()
