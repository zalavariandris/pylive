from typing import Tuple, Literal
import nuke
import math
vec2 = nuke.nukemath.Vector2
vec3 = nuke.nukemath.Vector3
vec4 = nuke.nukemath.Vector4
Line2D = Tuple[vec2, vec2]
Line3D = Tuple[vec3, vec3]
mat3 = nuke.nukemath.Matrix3
mat4 = nuke.nukemath.Matrix4


# --- Core math utilities ---
def identity(kind:Literal[mat3, mat4]) -> mat3 | mat4:
    m = kind()
    m.makeIdentity()
    return m

def distance(a: vec2 | vec3, b: vec2 | vec3) -> float:
    return math.fabs(a - b).length()

def length(v: vec2 | vec3) -> float:
    return v.length()

def normalize(v: vec2 | vec3) -> vec2 | vec3:
    result = v.__class__(v)
    l = v.length()
    if l != 0:
        result /= l
    return result

def inverse(m: mat3 | mat4) -> mat3 | mat4:
    return m.inverse()

def cross(a: vec3, b: vec3) -> vec3:
    return  a.cross(b)

def dot(a: vec2 | vec3, b: vec2 | vec3) -> float:
    return a.dot(b)

def determinant(m: mat3 | mat4) -> float:
    return m.determinant()

def perspective(fovy: float, aspect: float, near: float, far: float) -> mat4:
    import math
    f = 1.0 / math.tan(fovy / 2.0)
    
    m = nuke.nukemath.Matrix4()
    m.projection(f, near, far, False) #TODO: this is the built in nuke perspective projection constructor. not sure how ot acually works
    return m

def project(world: vec3, view: mat4, projection: mat4, viewport: vec4) -> vec3:
    clip:vec4 = projection * inverse(view) * vec4(world.x, world.y, world.z, 1.0)
    ndc = vec3(clip.x/clip.w, clip.y/clip.w, clip.z/clip.w)
    window_coords = nuke.nukemath.Vector3(
        ((ndc.x + 1.0) / 2.0) * viewport[2] + viewport[0],
        ((ndc.y + 1.0) / 2.0) * viewport[3] + viewport[1],
        (ndc.z + 1.0) / 2.0
    )
    return window_coords

def unProject(win: vec3, view: mat4, projection: mat4, viewport: vec4) -> vec3:
    viewport_pos = vec2(viewport.x, viewport.y)
    viewport_size = vec2(viewport.z, viewport.w)
    ndc = vec4(
        (win.x-viewport_pos.x) / viewport_size.x*2-1,
        (win.y-viewport_pos.y) / viewport_size.y*2-1,
        win.z * 2 -1,
        1.0
    )

    inv = inverse((projection * inverse(view)))
    obj = inv * ndc
    return vec3(
        obj.x/obj.w, 
        obj.y/obj.w, 
        obj.z/obj.w
    )


def rotate(mat: mat4, angle: float, axis: vec3) -> mat4:
    r = mat.__class__()
    r.makeIdentity()
    r.rotate(angle * 180.0 / math.pi, axis.x, axis.y, axis.z)
    return r * mat


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min(value, max_value), min_value)

def mat3_from_directions(forward:vec3, right:vec3, up:vec3):
    m = mat3(
        forward.x, right.x, up.x,
        forward.y, right.y, up.y,
        forward.z, right.z, up.z
    )
    return m

def mat4_from_mat3(m3:mat3)->mat4:
    m4 = nuke.nukemath.Matrix4()
    m4.makeIdentity()
    m4[0] =  m3[0]
    m4[1] =  m3[1]
    m4[2] =  m3[2]
    m4[4] =  m3[3]
    m4[5] =  m3[4]
    m4[6] =  m3[5]
    m4[8] =  m3[6]
    m4[9] =  m3[7]
    m4[10] = m3[8]
    
    return m4

def decompose(mat:mat3):
    r11, r12, r13 = mat[0]
    r21, r22, r23 = mat[1]
    r31, r32, r33 = mat[2]

    
    # Compute pitch (Y-axis rotation)
    pitch = math.atan2(-r31, math.sqrt(r11*r11 + r21*r21))

    # Compute roll (X-axis rotation)
    roll = math.atan2(r32, r33)

    # Compute yaw (Z-axis rotation)
    yaw = math.atan2(r21, r11)

    return roll, pitch, yaw