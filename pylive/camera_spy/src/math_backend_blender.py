import mathutils
from typing import Tuple, Literal
import math

# Aliases
vec2 = mathutils.Vector
vec3 = mathutils.Vector
vec4 = mathutils.Vector
Line2D = Tuple[vec2, vec2]
Line3D = Tuple[vec3, vec3]
mat3 = mathutils.Matrix
mat4 = mathutils.Matrix


# --- Core math utilities ---
def identity(kind:Literal[mat3, mat4]) -> mat3 | mat4:
    return m.__class__.Identity(len(m))


def distance(a: vec2 | vec3, b: vec2 | vec3) -> float:
    return (a - b).length


def length(v: vec2 | vec3) -> float:
    return v.length


def normalize(v: vec2 | vec3) -> vec2 | vec3:
    if v.length == 0:
        return v.copy()
    return v.normalized()


def inverse(m: mat3 | mat4) -> mat3 | mat4:
    return m.inverted()


def cross(a: vec3, b: vec3) -> vec3:
    return a.cross(b)


def dot(a: vec2 | vec3, b: vec2 | vec3) -> float:
    return a.dot(b)


def determinant(m: mat3 | mat4) -> float:
    return m.determinant()


def perspective(fovy: float, aspect: float, near: float, far: float) -> mat4:
    f = 1.0 / math.tan(fovy / 2.0)
    return mat4((
        (f / aspect, 0.0, 0.0, 0.0),
        (0.0, f, 0.0, 0.0),
        (0.0, 0.0, (far + near) / (near - far), (2.0 * far * near) / (near - far)),
        (0.0, 0.0, -1.0, 0.0)
    ))


def unProject(win: vec3, view: mat4, projection: mat4, viewport: vec4) -> vec3:
    # Use Blender’s mathutils.Matrix inversion to simulate unproject
    inv = (projection @ view).inverted()
    ndc = mathutils.Vector((
        (win.x - viewport[0]) / viewport[2] * 2.0 - 1.0,
        (win.y - viewport[1]) / viewport[3] * 2.0 - 1.0,
        2.0 * win.z - 1.0,
        1.0
    ))
    world = inv @ ndc
    world /= world.w
    return mathutils.Vector((world.x, world.y, world.z))


def project(world: vec3, view: mat4, projection: mat4, viewport: vec4) -> vec3:
    clip = projection @ view @ mathutils.Vector((world.x, world.y, world.z, 1.0))
    ndc = clip.xyz / clip.w
    win = mathutils.Vector((
        ((ndc.x + 1.0) / 2.0) * viewport[2] + viewport[0],
        ((ndc.y + 1.0) / 2.0) * viewport[3] + viewport[1],
        (ndc.z + 1.0) / 2.0
    ))
    return win


def rotate(mat: mat4, angle: float, axis: vec3) -> mat4:
    rot = mat4.Rotation(angle, 4, axis)
    return mat @ rot


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min(value, max_value), min_value)
