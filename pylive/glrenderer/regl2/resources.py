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
from .resource_manager import ResourceManager


class GLResource(ABC):
    """Base class for all OpenGL resources managed by ResourceManager."""
    def __init__(self, resource_manager: 'ResourceManager'):
        self.resource_manager = weakref.ref(resource_manager)
        self._handle = None

    def handle(self)->Handle:
        if not self._handle:
            self._handle = self.allocate()
        return self._handle

    @abstractmethod
    def allocate(self)->Handle:
        pass

    @abstractmethod
    def release(self, handle: Handle=None):
        ...


class Texture(GLResource):
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
        self._size = size
        self._components = components
        self._data = data
        self._samples = samples
        self._alignment = alignment
        self._dtype = dtype
        self._internal_format = internal_format
        super().__init__(resource_manager)

    def allocate(self)->moderngl.Texture:
        ctx = self._resource_manager.mgl()
        assert ctx is not None, "Moderngl context is not initialized."
        handle = ctx.texture(size,
            components,
            data,
            samples=samples,
            alignment=alignment,
            dtype=dtype,
            internal_format=internal_format)



class Framebuffer(GLResource):
    def __init__(self, resource_manager: 'ResourceManager', 
        color_attachments: List[moderngl.Texture|moderngl.Renderbuffer] = None, 
        depth_attachment: Optional[moderngl.Texture|moderngl.Renderbuffer] = None
    ):
        if color_attachments is None:
            color_attachments = []

        handle = resource_manager.mgl().framebuffer(
            color_attachments, 
            depth_attachment)
    
        super().__init__(resource_manager, handle)

class Buffer(GLResource):
    def __init__(self, resource_manager: 'ResourceManager', 
        data: Optional[Any] = None, *, 
        reserve: int = 0, 
        dynamic: bool = False
    ):
        handle = resource_manager.mgl().buffer(data, reserve, dynamic)
        super().__init__(resource_manager, handle)



class TextureArray(GLResource):
    def __init__(self, resource_manager: 'ResourceManager', 
        size: Tuple[int, int, int],
        components: int,
        data: Optional[Any] = None,
        *,
        alignment: int = 1,
        dtype: str = 'f1'
    ):
        handle = resource_manager.mgl().texture_array(size,
            components,
            data,
            alignment,
            dtype)
        super().__init__(resource_manager, handle)


class Texture3D(GLResource):
    def __init__(self, resource_manager: 'ResourceManager',
            size: Tuple[int, int, int], 
            components: int, 
            data: Optional[Any] = None, 
            *,
            alignment: int = 1,
            dtype: str = 'f1'
    ):
        handle = resource_manager.mgl().texture3d(
            size,
            components,
            data,
            alignment=alignment, 
            dtype=dtype)
        super().__init__(resource_manager, handle)


class TextureCube(GLResource):
    def __init__(self, resource_manager: 'ResourceManager', 
        size: Tuple[int, int], 
        components: int, 
        data: Optional[Any] = None,
        *,
        alignment: int = 1,
        dtype: str = 'f1',
        internal_format: Optional[int] = None
    ):
        handle = resource_manager.mgl().texture_cube(
            size,
            components,
            data,
            alignment=alignment,
            dtype=dtype,
            internal_format=internal_format)
        super().__init__(resource_manager, handle)


class Renderbuffer(GLResource):
    def __init__(self, resource_manager: 'ResourceManager',
        size: Tuple[int, int],
        components: int = 4,
        *,
        samples: int = 0,
        dtype: str = 'f1'
    ):
        handle = resource_manager.mgl().renderbuffer(size,
            components,
            samples=samples,
            dtype=dtype)
        super().__init__(resource_manager, handle)
