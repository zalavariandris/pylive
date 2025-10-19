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


class GLResource(ABC, Generic[Handle]):
    """Base class for all OpenGL resources managed by ResourceManager."""
    def __init__(self):
        self._handle = None

    def handle(self)->Handle:
        """Get the underlying OpenGL resource handle, or None if not allocated."""
        return self._handle

    def get(self)->Handle:
        """Get the underlying OpenGL resource handle, allocating it if necessary."""
        if not self._handle:
            self._handle = self.allocate()
        return self._handle

    @abstractmethod
    def allocate(self)->Handle:
        """subclasses should implement this method, and create the actual opengl resource.
        this will be automatically called when necessary."""
        pass

    @abstractmethod
    def release(self, handle: Handle=None):
        pass

    def __del__(self):
        self.release()


class Texture(GLResource[moderngl.Texture]):
    def __init__(self,
        size: Tuple[int, int],
        components: int,
        data: Optional[Any] = None, 
        *,
        samples: int = 0,
        alignment: int = 1,
        dtype: str = 'f1',
        internal_format: Optional[int] = None
    ):
        super().__init__()
        self._size = size
        self._components = components
        self._data = data
        self._samples = samples
        self._alignment = alignment
        self._dtype = dtype
        self._internal_format = internal_format   

    @override
    def allocate(self)->moderngl.Texture:
        ctx = moderngl.get_context()
        assert ctx is not None, "Moderngl context is not initialized."
        return ctx.texture(self._size,
            self._components,
            self._data,
            samples=self._samples,
            alignment=self._alignment,
            dtype=self._dtype,
            internal_format=self._internal_format
        )
    
    @override
    def release(self, handle:Handle):
        handle.release()
 

class Framebuffer(GLResource[moderngl.Framebuffer]):
    def __init__(self, 
        color_attachments: List[moderngl.Texture|moderngl.Renderbuffer] = None, 
        depth_attachment: Optional[moderngl.Texture|moderngl.Renderbuffer] = None
    ):
        super().__init__()
        self._color_attachments = color_attachments
        self._depth_attachment = depth_attachment

    @override
    def allocate(self):
        ctx = moderngl.get_context()
        assert ctx is not None, "Moderngl context is not initialized."
        return ctx.framebuffer(
            self._color_attachments, 
            self._depth_attachment
        )
    
    @override
    def release(self, handle:Handle):
        handle.release()
   

class Buffer(GLResource[moderngl.Buffer]):
    def __init__(self, 
        data: Optional[Any] = None, *, 
        reserve: int = 0, 
        dynamic: bool = False
    ):
        self._data = data
        self._reserve = reserve
        self._dynamic = dynamic
        super().__init__()

    @override
    def allocate(self)->moderngl.Buffer:
        ctx = moderngl.get_context()
        assert ctx is not None, "Moderngl context is not initialized."
        return ctx.buffer(self._data, self._reserve, self._dynamic)
    

class TextureArray(GLResource[moderngl.TextureArray]):
    def __init__(self, 
        size: Tuple[int, int, int],
        components: int,
        data: Optional[Any] = None,
        *,
        alignment: int = 1,
        dtype: str = 'f1'
    ):
        self._size = size
        self._components = components
        self._data = data
        self._alignment = alignment
        self._dtype = dtype
        super().__init__()

    @override
    def allocate(self)->moderngl.TextureArray:
        ctx = moderngl.get_context()
        assert ctx is not None, "Moderngl context is not initialized."
        return ctx.texture_array(
            self._size,
            self._components,
            self._data,
            alignment=self._alignment,
            dtype=self._dtype
        )
    
    @override
    def release(self, handle:Handle):
        handle.release()


class Texture3D(GLResource[moderngl.Texture3D]):
    def __init__(self, 
            size: Tuple[int, int, int], 
            components: int, 
            data: Optional[Any] = None, 
            *,
            alignment: int = 1,
            dtype: str = 'f1'
    ):
        super().__init__()
        self._size = size
        self._components = components
        self._data = data
        self._alignment = alignment
        self._dtype = dtype

    @override
    def allocate(self)->moderngl.Texture3D:
        ctx = moderngl.get_context()
        assert ctx is not None, "Moderngl context is not initialized."
        return ctx.texture3d(
            self._size,
            self._components,
            self._data,
            alignment=self._alignment,
            dtype=self._dtype
        )
    
    @override
    def release(self, handle:Handle):
        handle.release()


class TextureCube(GLResource[moderngl.TextureCube]):
    def __init__(self, 
        size: Tuple[int, int], 
        components: int, 
        data: Optional[Any] = None,
        *,
        alignment: int = 1,
        dtype: str = 'f1',
        internal_format: Optional[int] = None
    ):
        super().__init__()
        self._size = size
        self._components = components
        self._data = data
        self._alignment = alignment
        self._dtype = dtype
        self._internal_format = internal_format

    @override
    def allocate(self)->moderngl.TextureCube:
        ctx = moderngl.get_context()
        assert ctx is not None, "Moderngl context is not initialized."
        return ctx.texture_cube(
            self._size,
            self._components,
            self._data,
            alignment=self._alignment,
            dtype=self._dtype,
            internal_format=self._internal_format
        )
    
    @override
    def release(self, handle:Handle):
        handle.release()


class Renderbuffer(GLResource[moderngl.Renderbuffer]):
    def __init__(self,
        size: Tuple[int, int],
        components: int = 4,
        *,
        samples: int = 0,
        dtype: str = 'f1'
    ):
        super().__init__()
        self._size = size
        self._components = components
        self._samples = samples
        self._dtype = dtype

    @override
    def allocate(self)->moderngl.Renderbuffer:
        ctx = moderngl.get_context()
        assert ctx is not None, "Moderngl context is not initialized."
        return ctx.renderbuffer(
            self._size,
            self._components,
            samples=self._samples,
            dtype=self._dtype
        )
    
    @override
    def release(self, handle:Handle):
        handle.release()
