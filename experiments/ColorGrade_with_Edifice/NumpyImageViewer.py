from pylive.qt_components.pan_and_zoom_graphicsview_not_optimized import PanAndZoomGraphicsView
class NumpyImageViewer(CustomWidget[PanAndZoomGraphicsView]):
    def __init__(self, src:MyNumpyArray, **kwargs):
        super().__init__(**kwargs)
        self._register_props(
            {
                "src": src,
            }
        )

    def create_widget(self):
        view = PanAndZoomGraphicsView()
        view.setViewport(QOpenGLWidget() )
        scene = QGraphicsScene()
        pixmap_item = QGraphicsPixmapItem()
        scene.addItem(pixmap_item)
        view.setScene(scene)
        self.pixmap_item = pixmap_item
        pixmap = QPixmap.fromImage(qimage2ndarray.array2qimage(self.props["src"].np_array))
        self.pixmap_item.setPixmap(pixmap)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)

        # scene.addPixmap()
        view.setScene(scene)

        return view

    def update(self, widget: PanAndZoomGraphicsView, diff_props: PropsDiff):
        match diff_props.get("src"):
            case _, new_image:
                img = new_image.np_array
                qimg = numpy_to_qimage(img)
                pixmap = QPixmap.fromImage(qimg)
                if not pixmap.isNull():
                    self.pixmap_item.setPixmap(pixmap)
                else:
                    print("TODO: Failed to convert numpy array to QImage") #TODO: Handle this case properly
                    print(f"Shape: {img.shape}, Dtype: {img.dtype}")
                