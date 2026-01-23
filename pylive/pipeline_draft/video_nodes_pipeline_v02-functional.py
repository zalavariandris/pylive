from typing import Callable, Tuple
import numpy as np
import imageio
import time
import image_utils



type Time = int
VideoNodeType = Callable[[Time], image_utils.ImageRGBA]


def read(path:str)->VideoNodeType:
    def func(frame:Time)->np.ndarray:
        print("reading frame from disc:", frame)
        try:
            img = image_utils.read_image(path%frame)
            assert img.shape[2]==4, f"Input image must be RGBA, got shape: {img.shape}"
            return img
        except FileNotFoundError:
            return image_utils.constant(size=(720,512), color=(0,1,1,1))
    return func

def transform(video:VideoNodeType, translate:Tuple[int, int])->VideoNodeType:
    def func(frame:Time)->np.ndarray:
        source = video(frame)
        assert source.shape[2]==4, f"Input image must be RGBA, got shape: {source.shape}"
        result = image_utils.transform(source, translate)
        return result
    return func

def time_offset(A:VideoNodeType, offset:Time)->VideoNodeType:
    def func(frame:Time)->np.ndarray:
        return A(frame+offset)

    return func

def cache(video:VideoNodeType)->VideoNodeType:
    _cache = dict()
    def func(frame:Time)->np.ndarray:
        if frame not in _cache:
            _cache[frame] = video(frame)
        return _cache[frame]
    return func

def merge(fg:VideoNodeType, bg:VideoNodeType, mix:float)->VideoNodeType:
    def func(frame:Time)->np.ndarray:
        # return fg(frame) * (1 - mix) + bg(frame) * mix
        fg_img = fg(frame)
        assert fg_img.shape[2]==4, f"Input image must be RGBA, got shape: {fg_img.shape}"
        bg_img = bg(frame)
        assert bg_img.shape[2]==4, f"Input image must be RGBA, got shape: {bg_img.shape}"
        A, a = np.split(fg_img, [3], axis=-1)
        B, b = np.split(bg_img, [3], axis=-1)
        rgb_result = A*mix + B * (1 - a*mix)
        result_rgba = np.concatenate([rgb_result, a], axis=-1)
        assert result_rgba.shape[2]==4, f"Input image must be RGBA, got shape: {result_rgba.shape}"
        return result_rgba
    return func

def constant(color:Tuple[float, float, float, float])->VideoNodeType:
    def func(frame:Time)->np.ndarray:
        result = image_utils.constant(size=(720,512), color=color)
        assert result.shape[2]==4, f"Input image must be RGBA, got shape: {result.shape}"
        return result
    return func

class VideoOperator:       
    def __init__(self, *args, **kwargs):
        ...

    def __call__(self, frame:Time)->np.ndarray:
        ...

class VideoGraph(VideoOperator):
    def __init__(self):
        # self._nodes = []
        self._output_node: VideoNodeType|None = None
        self._cache = dict()

    def node(self, factory, *factory_args, **factory_kwargs)->VideoNodeType:
        # 1. Configuration Phase (happens once at graph build)
        node = factory(*factory_args, **factory_kwargs)

        # 2. Execution Phase (happens many times during __call__)
        def cached_node(*request_args, **request_kwargs)->np.ndarray:
            # We assume request_args are simple types (int, float, str) TODO: valiadate this. make a hashable key
            key = (node, request_args, tuple(sorted(request_kwargs.items())))
            if key not in self._cache:
                self._cache[key] = node(*request_args, **request_kwargs)
            return self._cache[key]
        
        # return
        return cached_node
    
    def output(self, node:VideoNodeType):
        self._output_node = node

    def __call__(self, frame:Time)->np.ndarray:
        print("Graph executing frame:", frame)
        if self._output_node is None:
            raise ValueError("Output node is not set.")
        self._cache.clear()
        return self._output_node(frame)
    


if __name__ == "__main__":
    import cv2
    import cv2

    graph = VideoGraph()
    read_node =            graph.node(read, r"assets\SMPTE_Color_Bars_animation\SMPTE_Color_Bars_animation_%05d.png")
    transform_node =       graph.node(transform, read_node, translate=(50,50))
    merge_over_transform = graph.node(merge, transform_node, read_node, mix=0.5)
    offset_node =          graph.node(time_offset, read_node, 5)
    merge_over_node =      graph.node(merge, merge_over_transform, offset_node, mix=0.5)
    cache_node =           graph.node(cache, merge_over_node)
    graph.output(cache_node)


    # Assume 100 frames for demo, adjust as needed
    NUM_FRAMES = 24
    window_name = "Result"
    current_frame = [0]  # Use list for mutability in callback

    def show_frame(frame_idx):
        # frame_request = _VideoFrameRequest(frame=frame_idx, roi=None)
        # img = OUTPUT_NODE.process(frame_request)
        img = graph(frame_idx)
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