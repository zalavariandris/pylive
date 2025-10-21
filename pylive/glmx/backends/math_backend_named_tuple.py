from __future__ import annotations
from collections import namedtuple
from typing import Literal, Union
import math

# ---------- Vectors ----------

class vec2(namedtuple('vec2', ['x', 'y'])):
    __slots__ = ()

    def __add__(self, other: vec2) -> vec2:
        return vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: vec2) -> vec2:
        return vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> vec2:
        return vec2(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> vec2:
        return vec2(self.x / scalar, self.y / scalar)


class vec3(namedtuple('vec3', ['x', 'y', 'z'])):
    __slots__ = ()

    def __add__(self, other: vec3) -> vec3:
        return vec3(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: vec3) -> vec3:
        return vec3(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> vec3:
        return vec3(self.x * scalar, self.y * scalar, self.z * scalar)

    def __truediv__(self, scalar: float) -> vec3:
        return vec3(self.x / scalar, self.y / scalar, self.z / scalar)


class vec4(namedtuple('vec4', ['x', 'y', 'z', 'w'])):
    __slots__ = ()

    def __add__(self, other: vec4) -> vec4:
        return vec4(self.x + other.x, self.y + other.y, self.z + other.z, self.w + other.w)

    def __sub__(self, other: vec4) -> vec4:
        return vec4(self.x - other.x, self.y - other.y, self.z - other.z, self.w - other.w)

    def __mul__(self, scalar: float) -> vec4:
        return vec4(self.x * scalar, self.y * scalar, self.z * scalar, self.w * scalar)

    def __truediv__(self, scalar: float) -> vec4:
        return vec4(self.x / scalar, self.y / scalar, self.z / scalar, self.w / scalar)


# ---------- Matrices ----------

class mat3(namedtuple('mat3', [
    'm00','m01','m02',
    'm10','m11','m12',
    'm20','m21','m22'
])):
    __slots__ = ()

    def __new__(cls,
                m00=None, m01=None, m02=None,
                m10=None, m11=None, m12=None,
                m20=None, m21=None, m22=None):
        if all(v is None for v in [m00, m01, m02, m10, m11, m12, m20, m21, m22]):
            # Return identity
            return super().__new__(cls,
                1.0, 0.0, 0.0,
                0.0, 1.0, 0.0,
                0.0, 0.0, 1.0)
        return super().__new__(cls,
            m00 if m00 is not None else 0.0,
            m01 if m01 is not None else 0.0,
            m02 if m02 is not None else 0.0,
            m10 if m10 is not None else 0.0,
            m11 if m11 is not None else 0.0,
            m12 if m12 is not None else 0.0,
            m20 if m20 is not None else 0.0,
            m21 if m21 is not None else 0.0,
            m22 if m22 is not None else 0.0)

    def __getitem__(self, idx):
        # Allow row access like mat[i][j]
        row = idx
        return [getattr(self, f"m{row}{col}") for col in range(3)]
    def __mul__(self, other):
        if isinstance(other, mat3):
            # Matrix-matrix multiplication
            def cell(i, j):
                return sum(getattr(self, f"m{i}{k}") * getattr(other, f"m{k}{j}") for k in range(3))
            return mat3(
                cell(0,0), cell(0,1), cell(0,2),
                cell(1,0), cell(1,1), cell(1,2),
                cell(2,0), cell(2,1), cell(2,2)
            )
        elif isinstance(other, vec3):
            # Matrix-vector multiplication
            x = self.m00 * other.x + self.m01 * other.y + self.m02 * other.z
            y = self.m10 * other.x + self.m11 * other.y + self.m12 * other.z
            z = self.m20 * other.x + self.m21 * other.y + self.m22 * other.z
            return vec3(x, y, z)
        elif isinstance(other, (int, float)):
            # Scalar multiplication
            return mat3(
                self.m00 * other, self.m01 * other, self.m02 * other,
                self.m10 * other, self.m11 * other, self.m12 * other,
                self.m20 * other, self.m21 * other, self.m22 * other
            )
        else:
            return NotImplemented
    

class mat4(namedtuple('mat4', [
    'm00','m01','m02','m03',
    'm10','m11','m12','m13',
    'm20','m21','m22','m23',
    'm30','m31','m32','m33'
])):
    __slots__ = ()

    def __new__(cls,
                m00=None, m01=None, m02=None, m03=None,
                m10=None, m11=None, m12=None, m13=None,
                m20=None, m21=None, m22=None, m23=None,
                m30=None, m31=None, m32=None, m33=None):
        if all(v is None for v in [m00, m01, m02, m03, m10, m11, m12, m13, m20, m21, m22, m23, m30, m31, m32, m33]):
            # Return identity
            return super().__new__(cls,
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0)
        return super().__new__(cls,
            m00 if m00 is not None else 0.0,
            m01 if m01 is not None else 0.0,
            m02 if m02 is not None else 0.0,
            m03 if m03 is not None else 0.0,
            m10 if m10 is not None else 0.0,
            m11 if m11 is not None else 0.0,
            m12 if m12 is not None else 0.0,
            m13 if m13 is not None else 0.0,
            m20 if m20 is not None else 0.0,
            m21 if m21 is not None else 0.0,
            m22 if m22 is not None else 0.0,
            m23 if m23 is not None else 0.0,
            m30 if m30 is not None else 0.0,
            m31 if m31 is not None else 0.0,
            m32 if m32 is not None else 0.0,
            m33 if m33 is not None else 0.0)

    def __getitem__(self, idx):
        row = idx
        return [getattr(self, f"m{row}{col}") for col in range(4)]

    def __mul__(self, other):
        if isinstance(other, mat4):
            def cell(i, j):
                return sum(getattr(self, f"m{i}{k}") * getattr(other, f"m{k}{j}") for k in range(4))
            return mat4(
                cell(0,0), cell(0,1), cell(0,2), cell(0,3),
                cell(1,0), cell(1,1), cell(1,2), cell(1,3),
                cell(2,0), cell(2,1), cell(2,2), cell(2,3),
                cell(3,0), cell(3,1), cell(3,2), cell(3,3)
            )
        elif isinstance(other, vec4):
            x = self.m00 * other.x + self.m01 * other.y + self.m02 * other.z + self.m03 * other.w
            y = self.m10 * other.x + self.m11 * other.y + self.m12 * other.z + self.m13 * other.w
            z = self.m20 * other.x + self.m21 * other.y + self.m22 * other.z + self.m23 * other.w
            w = self.m30 * other.x + self.m31 * other.y + self.m32 * other.z + self.m33 * other.w
            return vec4(x, y, z, w)
        elif isinstance(other, (int, float)):
            return mat4(
                self.m00 * other, self.m01 * other, self.m02 * other, self.m03 * other,
                self.m10 * other, self.m11 * other, self.m12 * other, self.m13 * other,
                self.m20 * other, self.m21 * other, self.m22 * other, self.m23 * other,
                self.m30 * other, self.m31 * other, self.m32 * other, self.m33 * other
            )
        else:
            return NotImplemented
    __slots__ = ()

    def __new__(cls,
                m00=None, m01=None, m02=None, m03=None,
                m10=None, m11=None, m12=None, m13=None,
                m20=None, m21=None, m22=None, m23=None,
                m30=None, m31=None, m32=None, m33=None):
        if all(v is None for v in [m00, m01, m02, m03, m10, m11, m12, m13, m20, m21, m22, m23, m30, m31, m32, m33]):
            # Return identity
            return super().__new__(cls,
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0)
        return super().__new__(cls,
            m00 if m00 is not None else 0.0,
            m01 if m01 is not None else 0.0,
            m02 if m02 is not None else 0.0,
            m03 if m03 is not None else 0.0,
            m10 if m10 is not None else 0.0,
            m11 if m11 is not None else 0.0,
            m12 if m12 is not None else 0.0,
            m13 if m13 is not None else 0.0,
            m20 if m20 is not None else 0.0,
            m21 if m21 is not None else 0.0,
            m22 if m22 is not None else 0.0,
            m23 if m23 is not None else 0.0,
            m30 if m30 is not None else 0.0,
            m31 if m31 is not None else 0.0,
            m32 if m32 is not None else 0.0,
            m33 if m33 is not None else 0.0)

    def __getitem__(self, idx):
        row = idx
        return [getattr(self, f"m{row}{col}") for col in range(4)]

    def __mul__(self, other):
        if isinstance(other, mat4):
            def cell(i, j):
                return sum(getattr(self, f"m{i}{k}") * getattr(other, f"m{k}{j}") for k in range(4))
            return mat4(
                cell(0,0), cell(0,1), cell(0,2), cell(0,3),
                cell(1,0), cell(1,1), cell(1,2), cell(1,3),
                cell(2,0), cell(2,1), cell(2,2), cell(2,3),
                cell(3,0), cell(3,1), cell(3,2), cell(3,3)
            )
        elif isinstance(other, vec4):
            x = self.m00 * other.x + self.m01 * other.y + self.m02 * other.z + self.m03 * other.w
            y = self.m10 * other.x + self.m11 * other.y + self.m12 * other.z + self.m13 * other.w
            z = self.m20 * other.x + self.m21 * other.y + self.m22 * other.z + self.m23 * other.w
            w = self.m30 * other.x + self.m31 * other.y + self.m32 * other.z + self.m33 * other.w
            return vec4(x, y, z, w)
        elif isinstance(other, (int, float)):
            return mat4(
                self.m00 * other, self.m01 * other, self.m02 * other, self.m03 * other,
                self.m10 * other, self.m11 * other, self.m12 * other, self.m13 * other,
                self.m20 * other, self.m21 * other, self.m22 * other, self.m23 * other,
                self.m30 * other, self.m31 * other, self.m32 * other, self.m33 * other
            )
        else:
            return NotImplemented
    
    def __mul__(self, other):
        if isinstance(other, mat4):
            # Matrix-matrix multiplication
            def cell(i, j):
                return sum(getattr(self, f"m{i}{k}") * getattr(other, f"m{k}{j}") for k in range(4))
            return mat4(
                cell(0,0), cell(0,1), cell(0,2), cell(0,3),
                cell(1,0), cell(1,1), cell(1,2), cell(1,3),
                cell(2,0), cell(2,1), cell(2,2), cell(2,3),
                cell(3,0), cell(3,1), cell(3,2), cell(3,3)
            )
        elif isinstance(other, vec4):
            # Matrix-vector multiplication
            x = self.m00 * other.x + self.m01 * other.y + self.m02 * other.z + self.m03 * other.w
            y = self.m10 * other.x + self.m11 * other.y + self.m12 * other.z + self.m13 * other.w
            z = self.m20 * other.x + self.m21 * other.y + self.m22 * other.z + self.m23 * other.w
            w = self.m30 * other.x + self.m31 * other.y + self.m32 * other.z + self.m33 * other.w
            return vec4(x, y, z, w)
        elif isinstance(other, (int, float)):
            # Scalar multiplication
            return mat4(
                self.m00 * other, self.m01 * other, self.m02 * other, self.m03 * other,
                self.m10 * other, self.m11 * other, self.m12 * other, self.m13 * other,
                self.m20 * other, self.m21 * other, self.m22 * other, self.m23 * other,
                self.m30 * other, self.m31 * other, self.m32 * other, self.m33 * other
            )
        else:
            return NotImplemented


    def __mul__(self, other):
        if isinstance(other, mat3):
            # Matrix-matrix multiplication
            def cell(i, j):
                return sum(getattr(self, f"m{i}{k}") * getattr(other, f"m{k}{j}") for k in range(3))
            return mat3(
                cell(0,0), cell(0,1), cell(0,2),
                cell(1,0), cell(1,1), cell(1,2),
                cell(2,0), cell(2,1), cell(2,2)
            )
        elif isinstance(other, vec3):
            # Matrix-vector multiplication
            x = self.m00 * other.x + self.m01 * other.y + self.m02 * other.z
            y = self.m10 * other.x + self.m11 * other.y + self.m12 * other.z
            z = self.m20 * other.x + self.m21 * other.y + self.m22 * other.z
            return vec3(x, y, z)
        elif isinstance(other, (int, float)):
            # Scalar multiplication
            return mat3(
                self.m00 * other, self.m01 * other, self.m02 * other,
                self.m10 * other, self.m11 * other, self.m12 * other,
                self.m20 * other, self.m21 * other, self.m22 * other
            )
        else:
            return NotImplemented
# ---------- Utilities ----------

def identity(kind: type[mat3] | type[mat4]) -> mat3 | mat4:
    if kind is mat3:
        return mat3([[1 if i == j else 0 for j in range(3)] for i in range(3)])
    elif kind is mat4:
        return mat4([[1 if i == j else 0 for j in range(4)] for i in range(4)])
    else:
        raise TypeError("Unsupported matrix type")


def length(v: vec2 | vec3) -> float:
    match v:
        case vec2(x, y):
            return math.sqrt(x*x + y*y)
        case vec3(x, y, z):
            return math.sqrt(x*x + y*y + z*z)
        case _:
            raise TypeError("Unsupported vector type")


def normalize(v: vec2 | vec3) -> vec2 | vec3:
    l = length(v)
    if l == 0:
        return v
    match v:
        case vec2(x, y):
            return vec2(x / l, y / l)
        case vec3(x, y, z):
            return vec3(x / l, y / l, z / l)
        case _:
            raise TypeError("Unsupported vector type")


def dot(a: vec2 | vec3, b: vec2 | vec3) -> float:
    match (a, b):
        case (vec2(ax, ay), vec2(bx, by)):
            return ax*bx + ay*by
        case (vec3(ax, ay, az), vec3(bx, by, bz)):
            return ax*bx + ay*by + az*bz
        case _:
            raise TypeError("Vectors must be same type vec2 or vec3")


def cross(a: vec3, b: vec3) -> vec3:
    return vec3(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x
    )


def distance(a: vec2 | vec3, b: vec2 | vec3) -> float:
    return length(a - b)


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


# ---------- Transformations ----------

def perspective(fovy: float, aspect: float, near: float, far: float) -> mat4:
    f = 1.0 / math.tan(fovy / 2)
    m = identity(mat4)
    m[0][0] = f / aspect
    m[1][1] = f
    m[2][2] = (far + near) / (near - far)
    m[2][3] = (2 * far * near) / (near - far)
    m[3][2] = -1
    m[3][3] = 0
    return m


def mat4_from_mat3(m3: mat3) -> mat4:
    return mat4(
        m3.m00, m3.m01, m3.m02, 0,
        m3.m10, m3.m11, m3.m12, 0,
        m3.m20, m3.m21, m3.m22, 0,
        0,      0,      0,      1
    )


def mat3_from_directions(forward: vec3, right: vec3, up: vec3) -> mat3:
    return mat3(
        right.x, up.x, forward.x,
        right.y, up.y, forward.y,
        right.z, up.z, forward.z
    )


# ---------- Placeholders for complex ops ----------

# ---------- Determinant ----------

def determinant(m: mat3 | mat4) -> float:
    match m:
        case mat3():
            return m.m00*(m.m11*m.m22 - m.m12*m.m21)\
                - m.m01*(m.m10*m.m22 - m.m12*m.m20)\
                + m.m02*(m.m10*m.m21 - m.m11*m.m20)

        case mat4():
            a00,a01,a02,a03 = m.m00,m.m01,m.m02,m.m03
            a10,a11,a12,a13 = m.m10,m.m11,m.m12,m.m13
            a20,a21,a22,a23 = m.m20,m.m21,m.m22,m.m23
            a30,a31,a32,a33 = m.m30,m.m31,m.m32,m.m33

            # Precompute 2x2 determinants (minors)
            b00 = a00*a11 - a01*a10
            b01 = a00*a12 - a02*a10
            b02 = a00*a13 - a03*a10
            b03 = a01*a12 - a02*a11
            b04 = a01*a13 - a03*a11
            b05 = a02*a13 - a03*a12
            b06 = a20*a31 - a21*a30
            b07 = a20*a32 - a22*a30
            b08 = a20*a33 - a23*a30
            b09 = a21*a32 - a22*a31
            b10 = a21*a33 - a23*a31
            b11 = a22*a33 - a23*a32

            # Compute determinant
            det = b00*b11 - b01*b10 + b02*b09 + b03*b08 - b04*b07 + b05*b06
            return det
        case _:
            raise TypeError("Unsupported matrix type")


# ---------- Inverse ----------

def inverse(m: mat3 | mat4) -> mat3 | mat4:
    match m:
        case mat3():
            det = determinant(m)
            if det == 0:
                raise ValueError("Matrix is singular")
            
            return mat3(
                (m.m11*m.m22 - m.m12*m.m21)/det,
                -(m.m01*m.m22 - m.m02*m.m21)/det,
                (m.m01*m.m12 - m.m02*m.m11)/det,
                -(m.m10*m.m22 - m.m12*m.m20)/det,
                (m.m00*m.m22 - m.m02*m.m20)/det,
                -(m.m00*m.m12 - m.m02*m.m10)/det,
                (m.m10*m.m21 - m.m11*m.m20)/det,
                -(m.m00*m.m21 - m.m01*m.m20)/det,
                (m.m00*m.m11 - m.m01*m.m10)/det
            )

        case mat4():
            # For readability, assign all fields
            a00,a01,a02,a03 = m.m00,m.m01,m.m02,m.m03
            a10,a11,a12,a13 = m.m10,m.m11,m.m12,m.m13
            a20,a21,a22,a23 = m.m20,m.m21,m.m22,m.m23
            a30,a31,a32,a33 = m.m30,m.m31,m.m32,m.m33

            # Compute cofactors for first row (expand determinant)
            b00 = a00*a11 - a01*a10
            b01 = a00*a12 - a02*a10
            b02 = a00*a13 - a03*a10
            b03 = a01*a12 - a02*a11
            b04 = a01*a13 - a03*a11
            b05 = a02*a13 - a03*a12
            b06 = a20*a31 - a21*a30
            b07 = a20*a32 - a22*a30
            b08 = a20*a33 - a23*a30
            b09 = a21*a32 - a22*a31
            b10 = a21*a33 - a23*a31
            b11 = a22*a33 - a23*a32

            det = b00*b11 - b01*b10 + b02*b09 + b03*b08 - b04*b07 + b05*b06
            if det == 0: raise ValueError("Matrix is singular")

            invDet = 1.0 / det

            return mat4(
                ( a11*b11 - a12*b10 + a13*b09)*invDet,
                (-a01*b11 + a02*b10 - a03*b09)*invDet,
                ( a31*b05 - a32*b04 + a33*b03)*invDet,
                (-a21*b05 + a22*b04 - a23*b03)*invDet,

                (-a10*b11 + a12*b08 - a13*b07)*invDet,
                ( a00*b11 - a02*b08 + a03*b07)*invDet,
                (-a30*b05 + a32*b02 - a33*b01)*invDet,
                ( a20*b05 - a22*b02 + a23*b01)*invDet,

                ( a10*b10 - a11*b08 + a13*b06)*invDet,
                (-a00*b10 + a01*b08 - a03*b06)*invDet,
                ( a30*b04 - a31*b02 + a33*b00)*invDet,
                (-a20*b04 + a21*b02 - a23*b00)*invDet,

                (-a10*b09 + a11*b07 - a12*b06)*invDet,
                ( a00*b09 - a01*b07 + a02*b06)*invDet,
                (-a30*b03 + a31*b01 - a32*b00)*invDet,
                ( a20*b03 - a21*b01 + a22*b00)*invDet,
            )

        case _:
            raise TypeError("Unsupported matrix type")


# ---------- Rotate ----------

def rotate(mat: mat4, angle: float, axis: vec3) -> mat4:
    axis = normalize(axis)
    c = math.cos(angle)
    s = math.sin(angle)
    t = 1 - c
    x, y, z = axis.x, axis.y, axis.z

    rot = mat4(
        t*x*x + c,   t*x*y - z*s, t*x*z + y*s, 0,
        t*x*y + z*s, t*y*y + c,   t*y*z - x*s, 0,
        t*x*z - y*s, t*y*z + x*s, t*z*z + c,   0,
        0,           0,           0,           1
    )

    # Multiply mat * rot manually
    r = mat4()
    for i in range(4):
        for j in range(4):
            val = sum(getattr(mat,f"m{i}{k}") * getattr(rot,f"m{k}{j}") for k in range(4))
            r = r._replace(**{f"m{i}{j}": val})
    return r


# ---------- Project / unProject ----------

def project(win: vec3, view: mat4, projection: mat4, viewport: vec4) -> vec3:
    # Transform to clip space: clip = projection * view * vec4(win,1)
    v = vec4(win.x, win.y, win.z, 1)
    # Multiply view
    temp = [sum(view[i][k]*[v.x,v.y,v.z,v.w][k] for k in range(4)) for i in range(4)]
    # Multiply projection
    clip = [sum(projection[i][k]*temp[k] for k in range(4)) for i in range(4)]
    ndc = [clip[i]/clip[3] for i in range(3)]
    # Window coords
    x = (ndc[0]*0.5 + 0.5)*viewport.z + viewport.x
    y = (ndc[1]*0.5 + 0.5)*viewport.w + viewport.y
    z = ndc[2]*0.5 + 0.5
    return vec3(x, y, z)


def unProject(win: vec3, view: mat4, projection: mat4, viewport: vec4) -> vec3:
    # NDC
    x = (win.x - viewport.x)/viewport.z*2 -1
    y = (win.y - viewport.y)/viewport.w*2 -1
    z = win.z*2 -1
    ndc = [x,y,z,1]
    # Inverse of combined projection * view
    m = inverse(projection * view)
    obj = [sum(m[i][k]*ndc[k] for k in range(4)) for i in range(4)]
    w = obj[3]
    return vec3(obj[0]/w, obj[1]/w, obj[2]/w)

