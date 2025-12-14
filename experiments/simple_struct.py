class Struct:
    # TODO: consider using types.SimpleNamespace, dataclasses, pydantic, or attrs
    """A simple struct-like class that allows attribute access to its keys."""
    def __init__(self, **kwargs):
        # normal dict storage
        self.__dict__.update(kwargs)
        # remember allowed keys
        self.__frozen_keys = set(kwargs)

    def __setattr__(self, name, value):
        # allow internal attributes
        if name.startswith("_Struct__"):
            super().__setattr__(name, value)
            return
        # disallow new attributes
        if name not in self.__frozen_keys:
            raise AttributeError(f"Cannot add new attribute: {name!r}")
        self.__dict__[name] = value

    def __delattr__(self, name):
        raise AttributeError("Cannot delete attributes")

    def to_dict(self):
        """Optional: export a regular dict"""
        return {k: getattr(self, k) for k in self.__frozen_keys}
