script = """
import numpy as np  # Standard import inside the exec script
height, width = 256, 256  # You can adjust the size

def random_image():
    return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
	
print(random_image())
"""

# Use exec with a custom global dictionary that simulates a fresh execution environment
global_vars = {}
local_vars = {}



# Execute the script with exec; it will handle imports normally within this isolated scope
def run():
	exec(script, globals(), locals())

run()
