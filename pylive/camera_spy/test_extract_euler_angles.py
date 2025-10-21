import glm
import math
from src import solver

import glm
import math
import pytest

def build_matrix_from_euler(angles, order):
    x, y, z = angles
    import glm
    R = glm.mat4(1.0)
    if order == "XYZ":
        R = glm.rotate(R, x, glm.vec3(1,0,0))
        R = glm.rotate(R, y, glm.vec3(0,1,0))
        R = glm.rotate(R, z, glm.vec3(0,0,1))
    elif order == "XZY":
        R = glm.rotate(R, x, glm.vec3(1,0,0))
        R = glm.rotate(R, z, glm.vec3(0,0,1))
        R = glm.rotate(R, y, glm.vec3(0,1,0))
    elif order == "YXZ":
        R = glm.rotate(R, y, glm.vec3(0,1,0))
        R = glm.rotate(R, x, glm.vec3(1,0,0))
        R = glm.rotate(R, z, glm.vec3(0,0,1))
    elif order == "YZX":
        R = glm.rotate(R, y, glm.vec3(0,1,0))
        R = glm.rotate(R, z, glm.vec3(0,0,1))
        R = glm.rotate(R, x, glm.vec3(1,0,0))
    elif order == "ZXY":
        R = glm.rotate(R, z, glm.vec3(0,0,1))
        R = glm.rotate(R, x, glm.vec3(1,0,0))
        R = glm.rotate(R, y, glm.vec3(0,1,0))
    elif order == "ZYX":
        R = glm.rotate(R, z, glm.vec3(0,0,1))
        R = glm.rotate(R, y, glm.vec3(0,1,0))
        R = glm.rotate(R, x, glm.vec3(1,0,0))
    return glm.mat3(R)

def matrices_almost_equal(A, B, tol=1e-5):
    for i in range(3):
        for j in range(3):
            if abs(A[i][j] - B[i][j]) > tol:
                return False
    return True

# Import your get_rotation function here if it's in another file
# from your_module import get_rotation
def almost_equal(a, b, tol=1e-5):
    """Check if two angles are almost equal, considering wrap-around."""
    return abs((a - b + math.pi) % (2*math.pi) - math.pi) < tol

rotation_orders = ["XYZ", "XZY", "YXZ", "YZX", "ZXY", "ZYX"]
test_angles = [
    (0, 0, 0),
    (math.radians(10), math.radians(40), math.radians(75)),
    (math.radians(-45), math.radians(20), math.radians(16035)),
    (math.radians(180), math.radians(-90), math.radians(60)),
]

@pytest.mark.parametrize("order", rotation_orders)
@pytest.mark.parametrize("angles", test_angles)
def test_get_rotation(order, angles):
    x, y, z = angles
    R = glm.mat4(1.0)

    # Build rotation matrix according to the given order
    for axis, angle in zip(order, (x, y, z)):
        if axis == "X":
            R = glm.rotate(R, angle, glm.vec3(1, 0, 0))
        elif axis == "Y":
            R = glm.rotate(R, angle, glm.vec3(0, 1, 0))
        elif axis == "Z":
            R = glm.rotate(R, angle, glm.vec3(0, 0, 1))

    R3 = glm.mat3(R)
    computed = solver.extract_euler_angle(R3, order)

    # Reconstruct matrix from computed angles and compare
    reconstructed = build_matrix_from_euler(computed, order)
    assert matrices_almost_equal(R3, reconstructed), f"Matrix mismatch for order {order} and angles {angles}\nOriginal:\n{R3}\nReconstructed:\n{reconstructed}"

# Standalone execution using pytest programmatically
if __name__ == "__main__":
    print("Running tests using pytest...")
    # This will execute all test functions in this file
    pytest.main([__file__, "-v"])