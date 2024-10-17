# Working with project.tom

A minimal example project.toml

```toml
[project]
name = "Thing"
version = "1.2.3"
# ...
dependencies = [
    "SomeLibrary >= 2.2",
    "AnotherLibrary >= 4.5.6",
]
```

if you have a project.tom, edfining dependencies, you can isntall them in one go
by `pip install .`
