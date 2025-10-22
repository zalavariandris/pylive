from imgui_bundle import imgui
from typing import TypeVar, Tuple
import glm

Vec2T = TypeVar('Vec2')
def point_handle(label:str, point:Vec2T, view:glm.mat4, projection:glm.mat4, viewport:Tuple[int, int, int, int])->Tuple[bool, Vec2T]:
    glm.ortho(0,1,0,1,-1,1)
    glm.perspective(glm.radians(45.0), 1.0, 0.1, 100.0)
    glm.project(glm.vec3(point.x,point.y,0), view, projection, glm.ivec4(*viewport))

def begin_plot(str_id:str):
    if imgui.begin_child(str_id, None):
        imgui.text("My Plot Area")
        point_handle()
        return True
    
    return False

def end_plot():
    imgui.end_child()

