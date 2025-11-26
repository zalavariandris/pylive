from imgui_bundle import imgui, immapp
import watchfiles
import threading
import ast

def hello_world2():
    imgui.text("Hello, hello!")

def update():
    imgui.text("This is the update Function!")
    hello_world2()

# ----------------------------------
# MAIN PROGRAM
# ----------------------------------
if __name__ == "__main__":
    filename = __file__
    rendered_code_text = ""
    last_symbols = set()  # for deletion detection

    # -------------------------------
    # Utility: load file, strip __main__
    # -------------------------------
    def load_script_without_main(filename: str) -> str:
        with open(filename, "r") as f:
            source = f.read()

        tree = ast.parse(source)

        new_body = []
        for node in tree.body:
            # remove: if __name__ == "__main__": ...
            if isinstance(node, ast.If):
                try:
                    if isinstance(node.test, ast.Compare):
                        left = node.test.left
                        ops = node.test.ops
                        comparators = node.test.comparators
                        if (
                            isinstance(left, ast.Name) and
                            left.id == "__name__" and
                            isinstance(ops[0], ast.Eq) and
                            isinstance(comparators[0], ast.Constant) and
                            comparators[0].value == "__main__"
                        ):
                            continue  # skip main block
                except:
                    pass

            new_body.append(node)

        tree.body = new_body
        return ast.unparse(tree)

    def reload_script():
        global rendered_code_text, last_symbols

        try:
            # Load code and remove main-block
            rendered_code_text = load_script_without_main(filename)

            # Compile for better error messages + speed
            try:
                code_obj = compile(rendered_code_text, filename, "exec")
            except SyntaxError as e:
                print("SYNTAX ERROR:", e)
                return
            except Exception as e:
                print("COMPILATION ERROR:", e)
                return

            # Execute into a fresh namespace
            temp = {}
            try:
                exec(code_obj, temp, temp)
            except Exception as e:
                print("EXECUTION ERROR:", e)
                return

            # Remove deleted names
            current_symbols = set(temp.keys())
            to_delete = last_symbols - current_symbols
            for key in to_delete:
                if key in globals():
                    del globals()[key]

            # Update or add new items
            for key, value in temp.items():
                if not key.startswith("__"):
                    globals()[key] = value

            last_symbols = current_symbols

            print("Hot-reloaded OK")

        except Exception as e:
            print("RELOAD ERROR:", e)


    # Initial load
    reload_script()

    # Watch thread
    def watcher():
        for _ in watchfiles.watch(filename, debounce=1600):
            reload_script()

    threading.Thread(target=watcher, daemon=True).start()


    # ---------------------------
    # GUI LOOP
    # ---------------------------
    def gui():
        imgui.begin("Live Script")
        imgui.text_wrapped(rendered_code_text)
        imgui.end()

        imgui.begin("Output")
        # <--- this will always call the latest version!
        if "update" in globals():
            try:
                update()
            except Exception as e:
                imgui.text(f"UPDATE ERROR: {e}")
        imgui.end()

    immapp.run(gui)
