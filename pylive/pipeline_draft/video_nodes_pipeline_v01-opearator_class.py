import time
from typing import Generic, TypeVar, Tuple, List
import numpy as np
import image_utils
import imageio


RequestType = TypeVar('RequestType')
OutputType = TypeVar('OutputType')

class Node():
    ...





import copy

#TODO: consider dataclass here
class _VideoFrameRequest:
    def __init__(self, frame, roi, _cache=None):
        self._frame = frame
        self._roi = roi
        # If no cache provided, create one. If provided (via replace), share it.
        self._cache = _cache if _cache is not None else {}
        self._frozen = True

    def __hash__(self):
        return hash((self._frame, self._roi))

    def __setattr__(self, key, value):
        if not getattr(self, '_frozen', False):
            return super().__setattr__(key, value)
        raise AttributeError(f"{self.__class__.__name__} is frozen")

    @property
    def frame(self):
        return self._frame

    @property
    def roi(self):
        return self._roi
    
    @property
    def cache(self):
        return self._cache
    
    # def __replace__(self, **changes):

    
    def replace(self, **changes):
        # Crucial: Always pass the existing self._cache to the new instance
        new_params = {
            "frame": self._frame,
            "roi": self._roi,
            "_cache": self._cache, # This ensures the diamond cache persists
        }
        new_params.update(changes)
        return type(self)(**new_params)
    

class Node(Generic[RequestType, OutputType]):
    def __init__(self):
        ...

    def process(self, request:RequestType)->OutputType:
        key = (self, request)
        if key not in request._cache:
            request._cache[key] = self._execute(request)
        return request._cache[key]

    def _execute(self, request:RequestType)->OutputType:
        ...

    def pipe(self, node_class: type, **kwargs):
        """
        Instantiates node_class, passing 'self' as the source 
        along with any other parameters.
        """
        if not issubclass(node_class, Node):
            raise TypeError(f"{node_class.__name__} must be a subclass of Node")
        
        # This assumes your nodes follow the convention of 
        # accepting 'source' as the first argument or keyword.
        return node_class(source=self, **kwargs)
    
    def tee(self, *node_classes: type, **kwargs) -> List['Node']:
        raise NotImplementedError("Tee method is not implemented yet.")
        ...


ImageRGBA = np.ndarray

class Read(Node[_VideoFrameRequest, ImageRGBA]):
    def __init__(self, path:str):
        super().__init__()
        self.path = path

    def __hash__(self):
        return hash(self.path)

    def _execute(self, request:_VideoFrameRequest)->ImageRGBA:
        print("Reading frame from disc", request.frame, "from", self.path % request.frame)
        first_frame, last_frame = image_utils.get_sequence_frame_range(self.path)  # Preload frame range info

        # hold first/last frame if out of bounds
        if request.frame < first_frame:
            frame = first_frame
        elif request.frame > last_frame:
            frame = last_frame
        else:
            frame = request.frame

        # Read image at frame
        img = imageio.imread(self.path % frame) # Todo: handle missing frames, and when the sequence does not exist at all

        # Convert to float32 in [0, 1]
        if np.issubdtype(img.dtype, np.integer):
            img = img.astype(np.float32) / np.iinfo(img.dtype).max
        else:
            img = img.astype(np.float32)

        # ---- Channel handling ----
        if img.ndim == 2:
            # H x W  → grayscale
            img = img[:, :, None]

        height, width, channels = img.shape

        match channels:
            case 1:
                # Grayscale → RGBA
                rgb = np.repeat(img, 3, axis=-1)
                alpha = np.ones((*img.shape[:2], 1), dtype=np.float32)
                img = np.concatenate([rgb, alpha], axis=-1)
                return img

            case 2:
                # Grayscale + Alpha → RGBA
                rgb = np.repeat(img[:, :, :1], 3, axis=-1)
                alpha = img[:, :, 1:2]
                img = np.concatenate([rgb, alpha], axis=-1)
                return img

            case 3:
                # RGB → RGBA
                alpha = np.ones((*img.shape[:2], 1), dtype=np.float32)
                img = np.concatenate([img, alpha], axis=-1)
                return img

            case 4:
                # Already RGBA
                return img

            case _:
                raise ValueError(f"Unsupported number of channels: {img.shape[-1]}")


class Cache(Node[_VideoFrameRequest, ImageRGBA]):
    def __init__(self, source:Node[_VideoFrameRequest, ImageRGBA]):
        super().__init__()
        self.source = source
        self.cache = {}

    def __hash__(self):
        return hash(self.source)
    
    def _execute(self, request:_VideoFrameRequest)->ImageRGBA:
        key = (self.source, request.frame, request.roi)
        if key not in self.cache:
            print(f"Caching frame {request.frame}")
            self.cache[key] = self.source.process(request)
        return self.cache[key]


class TimeOffset(Node[_VideoFrameRequest, ImageRGBA]):
    def __init__(self, source:Node[_VideoFrameRequest, ImageRGBA], offset:int):
        super().__init__()
        self.source = source
        self.offset = offset

    def __hash__(self):
        return hash((self.source, self.offset))

    def _execute(self, request:_VideoFrameRequest)->ImageRGBA:
        return self.source.process(request.replace(frame=request.frame + self.offset))


class Transform(Node[_VideoFrameRequest, ImageRGBA]):
    def __init__(self, source:Node[_VideoFrameRequest, ImageRGBA], translate:Tuple[float, float], scale:Tuple[float, float]=(1.0,1.0), pivot:Tuple[float, float]=(0.5,0.5)):
        self.source = source
        self.translate = translate
        self.scale = scale
        self.pivot = pivot

    def __hash__(self):
        return hash((self.source, self.translate, self.scale, self.pivot))

    def _execute(self, request:_VideoFrameRequest)->ImageRGBA:
        img = self.source.process(request)
        transformed = image_utils.transform(img, self.translate, self.scale, self.pivot)
        return transformed

class MergeOverOperator(Node[_VideoFrameRequest, ImageRGBA]):
    def __init__(self, A:Node[_VideoFrameRequest, ImageRGBA], B:Node[_VideoFrameRequest, ImageRGBA], mix:float):
        self.A = A
        self.B = B
        self.mix = mix

    def __hash__(self):
        return hash((self.A, self.B, self.mix))

    def _execute(self, request:_VideoFrameRequest)->ImageRGBA:
        A = self.A.process(request)
        B = self.B.process(request)
        merged = image_utils.merge_over(A, B, self.mix)
        return merged



def execute(node:Node[_VideoFrameRequest, ImageRGBA], frame:int, roi:Tuple[float, float, float, float])->ImageRGBA:
    request = _VideoFrameRequest(frame=frame, roi=roi)
    return node.process(request)

if __name__ == "__main__":
    import cv2
    read_node = (
        Read(r"assets\SMPTE_Color_Bars_animation\SMPTE_Color_Bars_animation_%05d.png")
        .pipe(Cache)
    )

    merge_moved_node = MergeOverOperator(
        MergeOverOperator(
            read_node, 
            read_node.pipe(TimeOffset, offset=10),
        0.5), 
        Transform(read_node, translate=(100, 30)), 
    0.5)


    OUTPUT_NODE = Cache(merge_moved_node)
    # result_cache_node = Cache(merge_over_node)

    # Assume 100 frames for demo, adjust as needed
    NUM_FRAMES = 24
    window_name = "Result"
    current_frame = [0]  # Use list for mutability in callback

    def show_frame(frame_idx):
        # frame_request = _VideoFrameRequest(frame=frame_idx, roi=None)
        # img = OUTPUT_NODE.process(frame_request)
        img = execute(OUTPUT_NODE, frame_idx, roi=None)
        cv2.imshow(window_name, img)
        print(f"Showing frame: {frame_idx}")

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            # Map x to frame number
            width = cv2.getWindowImageRect(window_name)[2]
            frame = int((x / max(1, width-1)) * (NUM_FRAMES-1))
            frame = max(0, min(NUM_FRAMES-1, frame))
            if frame != current_frame[0]:
                current_frame[0] = frame
                begin_time = time.time()
                show_frame(frame)
                end_time = time.time()
                elapsed_ms = (end_time - begin_time) * 1000
                fps = 1000 / elapsed_ms if elapsed_ms > 0 else float('inf')
                print(f"Frame {frame} rendered in {elapsed_ms:.1f} ms ({fps:.1f} fps)")

    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, on_mouse)
    show_frame(0)
    while True:
        key = cv2.waitKey(20)
        if key == 27 or key == ord('q'):
            break
    cv2.destroyAllWindows()