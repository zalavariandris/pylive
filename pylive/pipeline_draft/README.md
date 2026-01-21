## notable patterns

### the pipe metrhod
I chose thi, because simple, and easy to understand teh backed structure. Does'n feel like magic.
```python
node = (
    Read(path=r"assets\SMPTE_Color_Bars_animation\SMPTE_Color_Bars_animation_%05d.png") 
    .pipe(Cache)
    .pipe(Transform, translate=(100,30)) 
    .pipe(TimeOffset, offset=5) 
    .pipe(MergeOverOperator, mix=0.5))
```

### Pipable call factory
```python
class TimeOffset(Node):
    def __init__(self, source=None, offset=0):
        super().__init__()
        self.source = source
        self.offset = offset

    def __call__(self, source):
        """Allows the instance to be used as a factory for another instance."""
        return TimeOffset(source=source, offset=self.offset)
```
### Usage in a pipe:
1. Create a "template" node with parameters
2. Pipe the source into it

```python
graph = (
    Read("path_%05d.png") 
    >> TimeOffset(offset=10)
    >> ...

# 1. Define recipes
pre_cache = Cache.curry()
retime = TimeOffset.curry(offset=10)
move = Transform.curry(translate=(50, 50))

# 2. Build the graph
# The source is a real instance
src = Read(path="source.png") >> pre_cache

# The diamond: Merge takes two real instances
# We use the recipes to derive two branches from the same 'src'
graph = MergeOverOperator(
    A = src >> move,
    B = src >> retime,
    mix = 0.5
)
```

```python
class Node(Generic[RequestType, OutputType]):
    def __init__(self):
        self._node_id = id(self)

    # ... execute and process methods as defined before ...

    def __rshift__(self, other):
        """Supports the 'pipe' syntax: node >> Transform(...)"""
        if isinstance(other, type) and issubclass(other, Node):
            # Supports syntax: read_node >> TimeOffset
            return other(source=self)
        
        if callable(other):
            # Supports syntax: read_node >> TimeOffset(offset=5) 
            # (assuming TimeOffset returns a factory/partial)
            return other(self)
            
        raise TypeError(f"Cannot pipe Node into {type(other)}")

    def __add__(self, other):
        """Supports syntax: nodeA + nodeB (for Merging)"""
        return MergeOverOperator(A=self, B=other, mix=0.5)


from functools import partial

# Functional helpers to make piping look like a DSL
def offset(frames):
    return lambda source: TimeOffset(source=source, offset=frames)

def move(x, y):
    return lambda source: Transform(source=source, translate=(x, y))

def cache():
    return lambda source: Cache(source=source)
```

__example__
```python
# Create the base
src = Read("frames_%05d.png") >> cache()

# Create the diamond branch
# Using '+' as a shortcut for MergeOver
final_node = src + (src >> offset(10)) 

# Or a long chain
final_node = (
    Read("bg.png") >> move(10, 10) 
    >> offset(5) 
    >> cache()
)
```

### The "Fluent" approach
No partials, no extra functions, just your existing classes

__example__
```python
graph = (
    Read("path_%05d.png")
    .cache()
    .offset(10)
)
```


### Using TEE
# TOOD: this seems pretty cool
```python
read_node = (
    Read(r"assets\SMPTE_Color_Bars_animation\SMPTE_Color_Bars_animation_%05d.png")
    .pipe(Cache().curry())
    .tee(Identity(), TimeOffset(offset=5))
    .pipe(Identity(), MergeOver()) # pipe to multiple nodes
    .tee(           Transform(translate=(50, 50)), Identity()          )
    .pipe(MergeOver.curry(2)(mix=.05))

        READ
         |
        CACHE
        |    \
        .   TimeOffset
      /    \     |
      .         MergeOver
      Transform  .
      \       /
      MergeOver
)
```