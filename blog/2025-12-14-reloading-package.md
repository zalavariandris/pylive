https://github.com/julvo/reloading

# Reloading Python Packages for Faster Development
In Python development, it's common to make changes to your code and want to see those changes reflected
immediately without restarting your application. The `reloading` is simple and pretty useful.

you can simply decorate a function with `@reloading`, and on file change, the next time the function is called,
it will use the new code.

example:

```python
from reloading import reloading

@reloading
def my_gui():
    imgui.text("This is my n.")

if __name__ == "__main__":
    from imgui_bundle import immapp
    immapp.run(my_gui)
```

since immapp is calling `my_gui` all the time, it will reflect the changes.
