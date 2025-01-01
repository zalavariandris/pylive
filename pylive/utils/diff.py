from typing import *
from dataclasses import dataclass
from itertools import zip_longest
_SENTINEL_ = object()

@dataclass
class Change:
    added: dict
    removed: dict
    changed: dict
    unchanged: dict

def diff_dict(dict1:dict, dict2:dict)->Change:
    """
    Compute the difference between two dictionaries.

    Args:
        dict1 (dict): The first dictionary (original).
        dict2 (dict): The second dictionary (updated).

    Returns:
        dict: A dictionary containing added, removed, changed, and unchanged keys.
    """
    added =     {k: dict2[k] for k in dict2 if k not in dict1}
    removed =   {k: dict1[k] for k in dict1 if k not in dict2}
    changed =   {k: (dict1[k], dict2[k]) for k in dict1 if k in dict2 and dict1[k] != dict2[k]}
    unchanged = {k: dict1[k] for k in dict1 if k in dict2 and dict1[k] == dict2[k]}

    return Change(
        added=added,
        removed=removed,
        changed=changed,
        unchanged=unchanged,
    )


def diff_list(list1:list, list2:list)->Change:
    added = dict()
    removed = dict()
    unchanged = dict()
    for i, (item1, item2) in enumerate(zip_longest(list1, list2, fillvalue=_SENTINEL_)):
        if item1 is item2:
            # Items are unchanged
            unchanged[i]=item1
        elif item1 is _SENTINEL_:
            # Item added in list2
            added[i]=item2
        elif item2 is _SENTINEL_:
            # Item removed from list1
            removed[i]=item1
        else:
            # Item replaced (treated as a remove and add)
            removed[i]=item1
            added[i]=item2

    return Change(added, removed, dict(), unchanged)


# New patch_dict
def patch_dict(original: dict, change: Change) -> dict:
    """
    Apply a dictionary patch to transform the original dictionary.

    Args:
        original (dict): The original dictionary.
        change (Change): The changes to apply.

    Returns:
        dict: The updated dictionary.
    """
    updated = original.copy()
    # Remove keys
    for key in change.removed:
        updated.pop(key, None)
    # Add or update keys
    for key, value in change.added.items():
        updated[key] = value
    # Apply changed values
    for key, (_, new_value) in change.changed.items():
        updated[key] = new_value
    return updated

# New patch_list
def patch_list(original: List, change: Change) -> List:
    """
    Apply a list patch to transform the original list.

    Args:
        original (List): The original list.
        change (Change): The changes to apply.

    Returns:
        List: The updated list.
    """
    updated = original[:]
    # Remove items in reverse order to preserve indices
    for index in sorted(change.removed.keys(), reverse=True):
        if index < len(updated):
            updated.pop(index)
    # Add items at the specified indices
    for index, value in change.added.items():
        updated.insert(index, value)
    return updated

