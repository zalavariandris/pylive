from node import Node
from changes import UpdateProp, AddChild, RemoveChild, ReplaceNode


class TextNode(Node):
    def __init__(self, text, key=None):
        super().__init__("Text", props={"value": text}, children=[], key=key)

    def _diff_self(self, other, path):
        ops = []
        if self.props["value"] != other.props["value"]:
            ops.append(UpdateProp(path, "value", other.props["value"]))
        return ops

    def _apply_op(self, op):
        if isinstance(op, UpdateProp):
            if op.key == "value":
                self.props["value"] = op.value
        elif isinstance(op, ReplaceNode):
            self.type = op.new_node.type
            self.props = op.new_node.props


class ContainerNode(Node):
    def __init__(self, children=None, key=None):
        super().__init__("Container", props={}, children=children or [], key=key)

    def _diff_self(self, other, path):
        ops = []
        # Diff children by position (simple version)
        min_len = min(len(self.children), len(other.children))
        for i in range(min_len):
            ops += self.children[i].diff(other.children[i], path + [i])
        if len(self.children) < len(other.children):
            for i in range(len(self.children), len(other.children)):
                ops.append(AddChild(path, i, other.children[i]))
        elif len(self.children) > len(other.children):
            for i in range(len(other.children), len(self.children)):
                ops.append(RemoveChild(path, i))
        return ops

    def _apply_op(self, op):
        if isinstance(op, AddChild):
            self.children.insert(op.index, op.node)
        elif isinstance(op, RemoveChild):
            self.children.pop(op.index)
        elif isinstance(op, ReplaceNode):
            self.type = op.new_node.type
            self.props = op.new_node.props
            self.children = op.new_node.children


a = ContainerNode(children=[
    TextNode("Hello"),
    TextNode("World")
])

b = ContainerNode(children=[
    TextNode("Hello there"),
    TextNode("World!"),
    TextNode("New line")
])


def render(node, indent=0):
    print("  " * indent + repr(node))
    for child in node.children:
        render(child, indent + 1)

render(a)

print("\nDiff operations:")
ops = a.diff(b)
for op in ops:
    print("- ", op.op, op.path, getattr(op, "value", getattr(op, "node", None)))

print("\nPatching a to become b...")
a.patch(ops)
render(a)