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


if __name__ == "__main__":
    import rich
    from pathlib import Path
    rich.print("[bold green]Pipeline v0.1[/bold green]")
    rich.print(f"  - {Path.cwd()}")

    # model
    pipeline = Pipeline(
        utils.read_image,
        path="./assets/IMG_0885.JPG")\
    .append(
        utils.reformat,
        size=(512, 512))\
    .append(
        utils.merge_over,
        B=Pipeline(
            utils.checkerboard, size=(512,512), square_size=8
        ))\
    .append(
        utils.add_grain, 
        variance=0.1)
    
    # update
    result = execute(pipeline)

    # view
    import cv2
    cv2.imshow("Result", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
