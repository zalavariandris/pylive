# run with jurigged to auto-reload on changes
# python -m jurigged jurigged_and_implot.py

from imgui_bundle import imgui, immapp, implot
import numpy as np
import math

def gui():
    imgui.text("Hello, World!")
    try:
        implot.begin_plot("My Plot")
        x = np.linspace(0.0, 1.0, 100)
        fn = lambda x: math.pow(x, 10)
        implot.plot_line("My Line", x, np.array([fn(x) for x in x]))
    except Exception as e:
        imgui.text(f"Failed to render plot. {e}")
    finally:
        implot.end_plot()

if __name__ == "__main__":
    immapp.run(gui, with_implot=True)