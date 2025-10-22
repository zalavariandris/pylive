from imgui_bundle import imgui, hello_imgui
from imgui_bundle import imgui
import moderngl

def main():
    ctx = moderngl.create_context()
    # def gui():


    imgui.new_frame()

        ctx = moderngl.get_context()
        if ctx is None:
            return
        ctx.gc_mode = 'auto'

    imgui.end_frame()

    # hello_imgui.RunnerParams()
    # immapp = hello_imgui.run()