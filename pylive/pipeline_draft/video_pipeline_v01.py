from typing import Any, Callable, Iterator, Iterable, Tuple, List, Union, overload
import image_utils as utils

OperatorType = Tuple[Callable, tuple, dict]

class Pipeline:
    def __init__(self, operator:Callable|None=None, *args, **kwargs):
        self._operators:List[OperatorType] = []
        if operator is not None:
            self.append(operator, *args, **kwargs)

    def append(self, operator:Callable, *args, **kwargs):
        self._operators.append( (operator, args, kwargs) )
        return self
    
    def __iter__(self)->Iterator[Tuple[Callable, tuple, dict]]:
        return iter(self._operators)
    
    @overload
    def __getitem__(self, index: int) -> OperatorType: ...
    
    @overload
    def __getitem__(self, index: slice) -> List[OperatorType]: ...
    
    def __getitem__(self, index: slice|int)->OperatorType|List[OperatorType]:
        return self._operators[index]

    def __call__(self, operator:Callable, *args, **kwds):
        return self.append(operator, *args, **kwds)
    
def execute(pipeline:Iterable[OperatorType], *args, **kwargs)->Any: #TODO: support  arguments to the first operator:
    pipeline_iterator = iter(pipeline)
    # initial operator
    
    func, op_args, op_kwargs = next(pipeline_iterator)
    # print(f"Executing: {func.__name__} with args={op_args} kwargs={op_kwargs}")
    current_value = func(*op_args, **op_kwargs)

    # subsequent operators
    for func, args, kwargs in pipeline_iterator:
        args = (current_value, ) + args
        args_evaluated = []
        for arg in args:
            if isinstance(arg, Pipeline):
                arg = execute(arg)
            args_evaluated.append(arg)
        
        kwargs_evaluated = {}
        for key, value in kwargs.items():
            if isinstance(value, Pipeline):
                value = execute(value)
            kwargs_evaluated[key] = value
            
        # print(f"Executing: {func.__name__} with args={args_evaluated} kwargs={kwargs_evaluated}")
        current_value = func(*args_evaluated, **kwargs_evaluated)
    return current_value

from dataclasses import dataclass

@dataclass
class Context:
    frame:int
    tile:Tuple[int, int, int, int]|None # x, y, w, h

from typing import Protocol
import numpy as np


from copy import copy
class Operator(Protocol):
    def pull(self, context:Context)->Tuple[Context, Any]:
        return context, None

# class OperatorImage:
#     def __init__(self, func:Callable, /, *args, **kwargs):
#         self.func = func
#         self.args = args
#         self.kwargs = kwargs

#     def pull(self, context:Context)->Tuple[np.ndarray, Context]:
#         """Pull a tile of size (w,h) at position (x,y)."""
#         raise NotImplementedError

class ReadSequenceOperator(Operator):
    def __init__(self, path:str):
        self.path = path

        # detect sequence:
        is_sequence = False
        for fmt in ["%03d", "%04d", "%05d", "%06d"]:
            if fmt in path:
                is_sequence = True
                break
        self.is_sequence = is_sequence

        if is_sequence:
            first_frame, last_frame = utils.get_sequence_frame_range(path)
            self.first_frame = first_frame
            self.last_frame = last_frame

    def pull(self, context:Context, *sources:Operator)->Any:
        path = self.path % context.frame
        # read image
        try:
            image = utils.read_image(path)
        except FileNotFoundError:
            image = np.ones((480, 640, 4), dtype=np.float32)
        if context.tile:
            x, y, w, h = context.tile
            return image[y:y+h, x:x+w]
        else:
            return image
    
class TimeOffsetOperator:
    def __init__(self, source:Operator, offset:int):
        self.source = source
        self.offset = offset

    def pull(self, context:Context)->Any:
        context = Context(frame=context.frame + self.offset, tile=context.tile)
        img = self.source.pull( context )
        return img
    
class MergeOverOperator():
    def __init__(self, source1:Operator, source2:Operator):
        self.source1 = source1
        self.source2 = source2

    def pull(self, context:Context)->Any:
        img1 = self.source1.pull( context )
        img2 = self.source2.pull( context )
        merged = utils.merge_over(img1, img2, 0.5)
        return merged
    

if __name__ == "__main__":
    import cv2
    read = ReadSequenceOperator("./assets/SMPTE_Color_Bars_animation/SMPTE_Color_Bars_animation_%05d.png")
    offset1 = TimeOffsetOperator(read, 5)
    offset2 = TimeOffsetOperator(read, 10)
    merge = MergeOverOperator(offset1, offset2)

    # Assume 100 frames for demo, adjust as needed
    NUM_FRAMES = 24
    window_name = "Result"
    current_frame = [0]  # Use list for mutability in callback

    def show_frame(frame_idx):
        ctx = Context(frame=frame_idx, tile=None)
        img = merge.pull(ctx)
        cv2.imshow(window_name, img)

    def on_mouse(event, x, y, flags, param):
        if event == cv2.EVENT_MOUSEMOVE:
            # Map x to frame number
            width = cv2.getWindowImageRect(window_name)[2]
            frame = int((x / max(1, width-1)) * (NUM_FRAMES-1))
            frame = max(0, min(NUM_FRAMES-1, frame))
            if frame != current_frame[0]:
                current_frame[0] = frame
                show_frame(frame)

    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, on_mouse)
    show_frame(0)
    while True:
        key = cv2.waitKey(20)
        if key == 27 or key == ord('q'):
            break
    cv2.destroyAllWindows()

    
