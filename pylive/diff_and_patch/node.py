from copy import deepcopy
from abc import ABC, abstractmethod
from changes import ReplaceNode, UpdateProp, AddChild, RemoveChild


class Node(ABC):
    def __init__(self, type_name, props=None, children=None, key=None):
        self.type = type_name
        self.props = props or {}
        self.children = children or []
        self.key = key

    def __repr__(self):
        return f"<{self.__class__.__name__} type={self.type!r} key={self.key!r}>"

    # -------------------------------
    # Base diff & patch entry points
    # -------------------------------
    def diff(self, other, path=None):
        if path is None:
            path = []

        if self.type != other.type:
            # Type changed → full replace
            return [ReplaceNode(path, other)]

        # Dispatch to subclass-specific implementation
        return self._diff_self(other, path)

    def patch(self, ops):
        """Apply a list of operations to this node recursively."""
        for op in ops:
            self._apply_op_recursive(op)
        return self

    def _apply_op_recursive(self, op):
        """Recursively apply an operation based on its path."""
        if not op.path:
            self._apply_op(op)
        else:
            # Traverse to the correct child
            child_index = op.path[0]
            child = self.children[child_index]
            # Create a new op with shortened path
            new_op = deepcopy(op)
            new_op.path = op.path[1:]
            child._apply_op_recursive(new_op)

    # -------------------------------
    # Hooks for subclasses
    # -------------------------------
    @abstractmethod
    def _diff_self(self, other, path):
        """Return list of operations describing differences."""
        pass

    @abstractmethod
    def _apply_op(self, op):
        """Apply a single operation to this node."""
        pass
