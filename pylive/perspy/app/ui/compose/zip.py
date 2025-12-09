from typing import Tuple, List, Any

def zip(*widgets: Tuple[bool, Any]) -> Tuple[bool, List[Any]]:
    """Combine multiple widgets results into one.

    params:
        widgets: A list of tuples (changed: bool, value: Any) from multiple imgui widget.

    returns a tuple:
        - True if any of the widgets changed.
        - values is a list of the values from each widget.

    example:

    """
    any_changed = False
    values = []
    for changed, value in widgets:
        if changed:
            any_changed = True
        values.append(value)
    return any_changed, values

