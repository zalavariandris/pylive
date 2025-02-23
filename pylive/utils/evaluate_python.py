from typing import *
import inspect

def store_function_args(func: Callable, **kwargs) -> dict[str, Any]:
    """
    Store function arguments in a dictionary by parameter name.
    Only accepts keyword arguments for clarity and safety.
    
    Args:
        func: The function whose arguments we want to store
        **kwargs: Keyword arguments matching the function parameters
    
    Returns:
        Dict mapping parameter names to their values
        
    Raises:
        TypeError: If required parameters are missing
    """
    sig = inspect.signature(func)

    # This will raise TypeError if required parameters are missing
    bound_args = sig.bind(**kwargs)
    bound_args.apply_defaults()
    return dict(bound_args.arguments)

def call_function_with_named_args(func: Callable, named_args: Dict[str, Any]) -> Any:
    """
    Call a function using stored arguments, respecting positional-only parameters.
    
    Args:
        func: Function to call
        stored_args: Dictionary of arguments keyed by parameter name
    """
    sig = inspect.signature(func)
    pos_args = []
    kw_args = {}
    
    for param_name, param in sig.parameters.items():
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            pos_args.append(named_args[param_name])
        else:
            if param_name in named_args:
                kw_args[param_name] = named_args[param_name]
    
    result = func(*pos_args, **kw_args)
    print("!!!!!!!!!!!!!!!!", result)
    return result


def parse_python_function(code:str)->Callable:
    """takes a python script and return the first function defined in the 
    script. raises Exceptions"""
    import inspect
    capture = {'__builtins__':__builtins__}
    try:
        exec(code, capture)
    except SyntaxError as err:
        raise err
    except Exception as err:
        raise err

    for name, attribute in capture.items():
        if callable(attribute) and not inspect.isclass(attribute):
            return attribute
    raise ValueError("no functions found in script")

