class Operation:
    def __init__(self, op, path):
        self.op = op
        self.path = path

class ReplaceNode(Operation):
    def __init__(self, path, new_node):
        super().__init__("replace", path)
        self.new_node = new_node

class UpdateProp(Operation):
    def __init__(self, path, key, value):
        super().__init__("update_prop", path)
        self.key = key
        self.value = value

class AddChild(Operation):
    def __init__(self, path, index, node):
        super().__init__("add_child", path)
        self.index = index
        self.node = node

class RemoveChild(Operation):
    def __init__(self, path, index):
        super().__init__("remove_child", path)
        self.index = index
