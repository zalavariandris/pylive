from imgui_bundle import imgui, immapp
import watchfiles
import threading

# Initial functions
def hello_world2():
    imgui.text("Hello, a!")

def update():
    imgui.text("This Is the Update Function!")
    hello_world2()


if __name__ == "__hot_main__":
    print("Running in hot-reload mode.")


if __name__ == "__main__":
    filename = __file__
    code_text = ""  # For displaying in GUI
    import ast
    # Watcher thread: replaces functions in globals() automatically
    def watching():
        global code_text
        for changes in watchfiles.watch(filename):
            try:
                with open(filename, "r") as f:
                    code_text = f.read()

                # Parse the file into an AST
                tree = ast.parse(code_text, filename)

                # Compile and execute the filtered AST
                code = compile(tree, filename, "exec")
                globals()['__name__'] = '__hot_main__'
                exec(code, globals())

            except Exception as e:
                print(f"Error reloading file: {e}")

    threading.Thread(target=watching, daemon=True).start()

    def gui():
        imgui.begin("Live Code Reloading Example")
        imgui.text_wrapped(code_text)
        imgui.end()

        imgui.begin("Hello, ImGui!")
        update()  # always calls latest version automatically
        imgui.end()

    print("Starting live code reloading example...")
    immapp.run(gui)
