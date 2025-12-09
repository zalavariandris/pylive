from .widgets.radio_group import radio_group
from .widgets.touch_pad import touch_pad
from .widgets.sidebar import begin_sidebar, end_sidebar

from .compose.comp import comp
from .compose.zip import zip

from . import viewer

from typing import Generic, Tuple, List, Type, Callable
from typing import TypeVar
from enum import Enum

from imgui_bundle import imgui

T = TypeVar('T', bound=Enum)

def combo_enum(label: str, current: T, enum_type: Type[T] | None = None) -> Tuple[bool, T]:
    """
    Create a combo box for enum values.
    
    Usage:
        changed, value = combo_enum("Mode", current_mode)
    """
    if enum_type is None:
        enum_type = type(current)
    
    items = list(enum_type)
    item_names = [item.name for item in items]
    current_index = items.index(current)
    changed, index = imgui.combo(label, current_index, item_names)
    selected_item = items[index]
    return changed, selected_item

__all__ = [
    # widgets
    "radio_group",
    "touch_pad",
    "begin_sidebar",
    "end_sidebar",
    "combo_enum",

    # viewer
    "viewer",
    
    # utils
    "comp",
    "zip"
]