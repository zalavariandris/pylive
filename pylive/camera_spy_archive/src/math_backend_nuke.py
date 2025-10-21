import DD
from typing import Tuple

# Aliases
from typing import Union
import DD

class vec2(DD.Image.Vector2):
    def __init__(self, x: float = 0.0, y: float = 0.0):
        self._v = DD.Image.Vector2(x, y)

    @property
    def x(self) -> float:
        return self._v.x

    @x.setter
    def x(self, value: float):
        self._v.x = value

    @property
    def y(self) -> float:
        return self._v.y

    @y.setter
    def y(self, value: float):
        self._v.y = value

    # --- Arithmetic ---
    def __add__(self, other: 'vec2') -> 'vec2':
        return vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'vec2') -> 'vec2':
        return vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'vec2':
        return vec2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> 'vec2':
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> 'vec2':
        return vec2(self.x / scalar, self.y / scalar)

    def __repr__(self):
        return f"glmx.vec2({self.x}, {self.y})"


class vec3:
    def __init__(self, x: float = 0, y: float = 0, z: float = 0):
        self._v = DD.Image.Vector3(x, y, z)

    @property
    def x(self) -> float:
        return self._v.x
    @x.setter
    def x(self, value: float):
        self._v.x = value

    @property
    def y(self) -> float:
        return self._v.y
    @y.setter
    def y(self, value: float):
        self._v.y = value

    @property
    def z(self) -> float:
        return self._v.z
    
    @z.setter
    def z(self, value: float):
        self._v.z = value

    # --- Arithmetic ---
    def __add__(self, other: "vec3") -> "vec3":
        return vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: "vec3") -> "vec3":
        return vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> "vec3":
        return vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __rmul__(self, scalar: float) -> "vec3":
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> "vec3":
        return vec3(self.x / scalar, self.y / scalar, self.z / scalar)

    def __repr__(self):
        return f"glmx.vec3({self.x}, {self.y}, {self.z})"


vec4 = DD.Image.Vector4
Line2D = Tuple[vec2, vec2]
Line3D = Tuple[vec3, vec3]
mat3 = DD.Image.Matrix3
mat4 = DD.Image.Matrix4


# --- Core math utilities ---
def identity(m: mat3 | mat4) -> mat3 | mat4:
    ident = m.__class__()
    ident.makeIdentity()
    return ident


def distance(a: vec2 | vec3, b: vec2 | vec3) -> float:
    return (a._v - b._v).length()


def length(v: vec2 | vec3) -> float:
    return v._v.length()


def normalize(v: vec2 | vec3) -> vec2 | vec3:
    result = v.__class__(v)
    l = v._v.length()
    if l != 0:
        result /= l
    return result


def inverse(m: mat3 | mat4) -> mat3 | mat4:
    inv = m.__class__(m)
    inv.invert()
    return inv


def cross(a: vec3, b: vec3) -> vec3:
    return  a._v.cross(b._v)


def dot(a: vec2 | vec3, b: vec2 | vec3) -> float:
    return a.dot(b)


def determinant(m: mat3 | mat4) -> float:
    return m.determinant()


def perspective(fovy: float, aspect: float, near: float, far: float) -> mat4:
    # Nuke has no direct perspective helper; build manually
    import math
    f = 1.0 / math.tan(fovy / 2.0)
    persp = mat4()
    persp.makeIdentity()
    persp.array([
        [f / aspect, 0, 0, 0],
        [0, f, 0, 0],
        [0, 0, (far + near) / (near - far), (2 * far * near) / (near - far)],
        [0, 0, -1, 0]
    ])
    return persp


def unProject(win: vec3, view: mat4, projection: mat4, viewport: vec4) -> vec3:
    import DD
    # Nuke doesn’t have a built-in unProject; you’d implement manually if needed.
    raise NotImplementedError("unProject is not directly supported in Nuke's API.")


def project(win: vec3, view: mat4, projection: mat4, viewport: vec4) -> vec3:
    raise NotImplementedError("project is not directly supported in Nuke's API.")


def rotate(mat: mat4, angle: float, axis: vec3) -> mat4:
    import math
    from DD import Image
    r = mat.__class__()
    r.makeIdentity()
    r.rotate(angle * 180.0 / math.pi, axis.x, axis.y, axis.z)
    return r * mat


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min(value, max_value), min_value)
