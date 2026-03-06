import threading
import queue
import glfw
from OpenGL.GL import *
from IPython import embed

# Thread-safe queue for drawing commands
command_queue = queue.Queue()
# Persistent list of shapes to draw
shapes = []

# --- OpenGL window thread ---
def opengl_window():
    if not glfw.init():
        print("Failed to initialize GLFW")
        return

    window = glfw.create_window(640, 480, "OpenGL Window", None, None)
    if not window:
        glfw.terminate()
        print("Failed to create window")
        return

    glfw.make_context_current(window)
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glOrtho(0, 640, 0, 480, -1, 1)  # Match window pixels

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT)

        # Add new commands from the queue to the persistent shapes list
        while not command_queue.empty():
            cmd = command_queue.get()
            shapes.append(cmd)

        # Draw all shapes every frame
        for shape in shapes:
            if shape['type'] == 'draw_rect':
                x, y, w, h = shape['x'], shape['y'], shape['w'], shape['h']
                r, g, b = shape.get('color', (1, 1, 1))
                glColor3f(r, g, b)
                glBegin(GL_QUADS)
                glVertex2f(x, y)
                glVertex2f(x + w, y)
                glVertex2f(x + w, y + h)
                glVertex2f(x, y + h)
                glEnd()

        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

# --- Functions exposed to REPL ---
def draw_rect(x, y, w, h, color=(1, 1, 1)):
    """Queue a rectangle to be drawn persistently"""
    command_queue.put({'type': 'draw_rect', 'x': x, 'y': y, 'w': w, 'h': h, 'color': color})

def clear():
    """Clear all shapes"""
    shapes.clear()

# Start OpenGL window in a separate thread
threading.Thread(target=opengl_window, daemon=True).start()

# --- Start interactive Python console ---
banner = """
Python REPL for OpenGL Drawing
Use draw_rect(x, y, w, h, color=(r,g,b)) to draw.
Use clear() to remove all shapes.
Example: draw_rect(100, 100, 50, 50, color=(1,0,0))
"""
embed(banner1=banner, local_ns=globals())