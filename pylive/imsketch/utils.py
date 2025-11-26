import ast
def remove_main_guiard_content(tree):
    # Filter out __main__ blocks
    new_body = []
    for node in tree.body:
        # Keep everything except `if __name__ == "__main__":`
        if not (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and isinstance(node.test.left, ast.Name)
            and node.test.left.id == "__name__"
            and isinstance(node.test.ops[0], ast.Eq)
            and isinstance(node.test.comparators[0], ast.Constant)
            and node.test.comparators[0].value == "__main__"
        ):
            new_body.append(node)

    tree.body = new_body