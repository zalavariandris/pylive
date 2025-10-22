class SceneLayer(RenderLayer):
    def __init__(self):
        super().__init__()
        self.show_grid_XY = True
        self.show_grid_XZ = False
        self.show_grid_YZ = False
        self.gridXY = GridLayer(XY=True)
        self.gridXZ = GridLayer(XZ=True)
        self.gridYZ = GridLayer(YZ=True)
        self.axes = AxesLayer()
        mesh = trimesh.creation.icosphere(subdivisions=2, radius=0.1)
        mesh = mesh.apply_translation([0, 0, 1])
        self.mesh = TrimeshLayer(mesh=mesh)
        self._initialized = False
        
    @property
    def initialized(self) -> bool:
        return self._initialized

    def setup(self):
        super().setup()
        self.gridXY.setup()
        self.gridXZ.setup()
        self.gridYZ.setup()
        self.axes.setup()
        self.mesh.setup()
        self._initialized = True

    def release(self):
        if self.gridXY:
            self.gridXY.release()
            self.gridXY = None
        if self.gridXZ:
            self.gridXZ.release()
            self.gridXZ = None
        if self.gridYZ:
            self.gridYZ.release()
            self.gridYZ = None
        if self.axes:
            self.axes.release()
            self.axes = None
        if self.mesh:
            self.mesh.release()
            self.mesh = None
        self._initialized = False
        return super().release()
    
    def render(self, camera:Camera):
        if self.show_grid_XY:
            self.gridXY.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        if self.show_grid_XZ:
            self.gridXZ.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        if self.show_grid_YZ:
            self.gridYZ.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        self.axes.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        self.mesh.render(view=camera.viewMatrix(), projection=camera.projectionMatrix())
        super().render()

# ModernGL context and framebuffer
scene_layer = SceneLayer()
render_target = RenderTarget(800, 800)
