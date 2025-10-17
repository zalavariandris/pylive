
from pylive.glrenderer.gllayers import TriangleLayer, GridLayer, AxesLayer, TrimeshLayer
from pylive.glrenderer.windows.mgl_render_window import MGLCameraWindow
import trimesh
import moderngl


class RenderLayersExampleWindow(MGLCameraWindow):
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
        
        self.ctx.disable(moderngl.DEPTH_TEST) #TODO: cosider moving this into the layers
        self.axes.render(self.camera.viewMatrix(), self.camera.projectionMatrix())
        self.ctx.enable(moderngl.DEPTH_TEST)

if __name__ == "__main__":
    # Run the window
    RenderLayersExampleWindow.run()