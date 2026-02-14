from typing import TypeVar, Generic, Callable

T = TypeVar("T")

class Registry(Generic[T]):
    _instances: dict[type, "Registry"] = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    def __init__(self, factory: Callable[[str | int], T]):
        # prevent re-init for singleton
        if getattr(self, "_initialized", False):
            return

        self._factory = factory
        self._objects: dict[int | str, T] = {}
        self._current_name: int | str | None = None
        self._initialized = True

    def current(self) -> T | None:
        if self._current_name is None:
            return None
        return self._objects.get(self._current_name)

    def begin(self, name: int | str) -> T:
        if name not in self._objects:
            self._objects[name] = self._factory(name)  # automatic creation
        self._current_name = name
        return self._objects[name]

    def end(self):
        self._current_name = None
