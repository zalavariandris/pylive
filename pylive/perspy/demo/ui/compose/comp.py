from typing import Callable, Tuple, Any, List

def comp(widget):
    def mapper(label, values, **options):
        any_changed = False
        results = []
        for i, value in enumerate(values):
            changed, result = widget(f"{label}{i}", value, **options)
            if changed:
                any_changed = True
            results.append(result)
        return any_changed, results
    return mapper
