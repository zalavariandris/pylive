import glm
from typing import Tuple, Literal

vec2 = glm.vec2
vec3 = glm.vec3
vec4 = glm.vec4
Line2D = Tuple[vec2, vec2]
Line3D = Tuple[vec3, vec3]
mat3 = glm.mat3
mat4 = glm.mat4

def identity(kind:Literal[mat3, mat4])->mat3|mat4:
    return glm.identity(m)

def distance(a:vec2|vec3, b:vec2|vec3)->float:
    return glm.distance(a, b)
    
def length(v:vec2|vec3)->float:
    return glm.length(v)

def normalize(v:vec2|vec3)->vec2|vec3:
    return glm.normalize(v)

def inverse(m:mat3|mat4)->mat3|mat4:
    return glm.inverse(m)

def cross(a:vec3, b:vec3)->vec3:
    return glm.cross(a, b)

def dot(a:vec2|vec3, b:vec2|vec3)->float:
    return glm.dot(a, b)

def determinant(m:mat3|mat4)->float:
    return glm.determinant(m)

def perspective(fovy:float, aspect:float, near:float, far:float)->mat4:
    return glm.perspective(fovy, aspect, near, far)

def unProject(win:vec3, view:mat4, projection:mat4, viewport:glm.vec4)->vec3:
    return glm.unProject(win, view, projection, viewport)

def project(win:vec3, view:mat4, projection:mat4, viewport:glm.vec4)->vec3:
    return glm.project(win, view, projection, viewport)

def rotate(mat:mat4, angle:float, axis:vec3)->mat4:
    return glm.rotate(mat, angle, axis)

def clamp(value:float, min_value:float, max_value:float)->float:
    return glm.clamp(value, min_value, max_value)

def mat3_from_directions(forward:vec3, right:vec3, up:vec3):
    return glm.mat3(forward, right, up)

def mat4_from_mat3(m:mat3)->mat4:
    return mat4(m)