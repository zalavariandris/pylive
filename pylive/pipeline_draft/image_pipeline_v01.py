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


class Input:
    def __init__(self, name:str):
        self._name = name

    @property
    def name(self)->str:
        return self._name


def execute(pipeline:Iterable[OperatorType], *opargs, **op_kwargs)->Any: #TODO: support  arguments to the first operator:
    pipeline_iterator = iter(pipeline)
    # initial operator
    
    func, op_args, op_kwargs = next(pipeline_iterator)
    current_value = func(*op_args, **op_kwargs)

    # subsequent operators
    for func, opargs, op_kwargs in pipeline_iterator:
        opargs = (current_value, ) + opargs
        args_evaluated = []
        for arg in opargs:
            if isinstance(arg, Pipeline):
                arg = execute(arg)
            args_evaluated.append(arg)
        
        kwargs_evaluated = {}
        for key, value in op_kwargs.items():
            if isinstance(value, Pipeline):
                value = execute(value)
            kwargs_evaluated[key] = value
            
        current_value = func(*args_evaluated, **kwargs_evaluated)
    return current_value
    
if __name__ == "__main__":
    import rich
    from pathlib import Path
    rich.print("[bold green]Pipeline v0.1[/bold green]")
    rich.print(f"  - {Path.cwd()}")

    # model
    image_pipeline = Pipeline(
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
    result = execute(image_pipeline)

    # view
    import cv2
    cv2.imshow("Result", result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
