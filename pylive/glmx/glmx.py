import sys

backend = None

if "glm" in sys.modules:
    from . math_backend_glm import *
    backend = "glm"
elif "nuke" in sys.modules:
    from . math_backend_nuke import *
    backend = "nuke"
elif "blender" in sys.modules:
    from . math_backend_blender import *
    backend = "blender"
else:
    from . math_backend_named_tuple import *
    print("Warning: Using named_tuple math backend, performance may be suboptimal.")
    backend = "named_tuple"
