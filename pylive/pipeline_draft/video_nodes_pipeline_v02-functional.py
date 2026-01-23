from typing import Callable
import numpy as np
import imageio
import time
import image_utils

VideoType = Callable[[int], np.ndarray]


def read(path:str)->VideoType:
    def func(frame:int):
        try:
            return imageio.v3.imread(path%frame)
        except FileNotFoundError:
            return image_utils.constant(size=(720,576), color=(0,1,1,1))
    return func

def transform(video:VideoType, translate)->VideoType:
    def func(frame:int):
        img = video(frame)
        return image_utils.transform(img, translate)
    return func

def time_offset(A:VideoType, offset:int)->VideoType:
    def func(frame):
        return A(frame+offset)

    return func

def merge(A:VideoType, B:VideoType, mix:float)->VideoType:
    def func(frame:int):
        return A(frame)+B(frame)
    return func

def constant(color)->VideoType:
    def func(frame:int):
        return image_utils.constant(size=(720,576), color=color)
    return func

# class Operator:       
#     def __init__(self, ...):
#         ...

#     def __call__(self, frame):
#         ...

def execute(video:VideoType, frame:int)->np.ndarray:
    return video(frame)

if __name__ == "__main__":
    import cv2
    import cv2
    read_node = read(r"assets\SMPTE_Color_Bars_animation\SMPTE_Color_Bars_animation_%05d.png")
    offset_node = time_offset(read_node, 5)
    OUTPUT_NODE = offset_node
    
    # result_cache_node = Cache(merge_over_node)

    # Assume 100 frames for demo, adjust as needed
    NUM_FRAMES = 24
    window_name = "Result"
    current_frame = [0]  # Use list for mutability in callback

    def show_frame(frame_idx):
        # frame_request = _VideoFrameRequest(frame=frame_idx, roi=None)
        # img = OUTPUT_NODE.process(frame_request)
        img = execute(OUTPUT_NODE, frame_idx)
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