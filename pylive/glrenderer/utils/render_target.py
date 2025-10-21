import moderngl

class RenderTarget:
    def __init__(self, width:int, height:int, **kwargs):
        self._width = width
        self._height = height

        self.fbo:moderngl.Framebuffer|None = None
        self.color_texture:moderngl.Texture|None = None
        self.depth_buffer:moderngl.Renderbuffer|None = None

        self._previous_fbo:moderngl.Framebuffer|None = None

        self._initialized = False

    def clear(self, r:float, g:float, b:float, a:float):
        if self.fbo is None:
            raise Exception("RenderTarget not setup. Call setup(ctx) before using.")
        self.fbo.clear(r, g, b, a)

    @property
    def initialized(self) -> bool:
        return self._initialized

    def setup(self):
        ctx = moderngl.get_context()
        if ctx is None:
            raise Exception("No current ModernGL context. Cannot setup SceneLayer.")
        
        # Create color texture
        self.color_texture = ctx.texture((self._width, self._height), 4, dtype='f1')
        self.color_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

        # Create depth renderbuffer
        self.depth_buffer = ctx.depth_renderbuffer((self._width, self._height))

        # Create framebuffer
        self.fbo = ctx.framebuffer(
            color_attachments=[self.color_texture],
            depth_attachment=self.depth_buffer
        )

        self._initialized = True

    def texture_id(self) -> int:
        if self.color_texture is None:
            raise Exception("RenderTarget not setup. Call setup(ctx) before using.")
        return self.color_texture.glo

    def resize(self, width:int, height:int):
        if width == self._width and height == self._height:
            return
        self._width = width
        self._height = height
        self.destroy()
        self.setup()

    def __enter__(self):
        # Get current context
        ctx = moderngl.get_context()
        if ctx is None:
            raise Exception("No current ModernGL context. Cannot setup SceneLayer.")
        
        # Save previous framebuffer
        if self._previous_fbo is not None:
            raise Exception("RenderTarget already in use.")
        self._previous_fbo = ctx.fbo

        # Bind our framebuffer
        if self.fbo is None:
            raise Exception("RenderTarget not setup. Call setup(ctx) before using.")
        self.fbo.use()
    
    def __exit__(self, exc_type, exc_value, traceback):
        assert self._previous_fbo, "RenderTarget was not properly entered."
        # Restore previous framebuffer
        self._previous_fbo.use()
        self._previous_fbo = None

    def destroy(self):
        if self.fbo:
            self.fbo.release()
            self.fbo = None
        if self.color_texture:
            self.color_texture.release()
            self.color_texture = None
        if self.depth_buffer:
            self.depth_buffer.release()
            self.depth_buffer = None
        self._initialized = False

    def __del__(self):
        self.destroy()