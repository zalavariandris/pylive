import pytest
import glm

from pylive.perspy.core.utils import decompose_frustum

def test_decompose_frustum():
    left, right, bottom, top, near, far = -0.32, 0.32, -0.24, 0.24, 1.0, 1000.0
    proj = glm.frustum(left, right, bottom, top, near, far)

    d_left, d_right, d_bottom, d_top, d_near, d_far = decompose_frustum(proj)

    assert left   == pytest.approx(d_left)
    assert right  == pytest.approx(d_right)
    assert bottom == pytest.approx(d_bottom)
    assert top    == pytest.approx(d_top)
    assert near   == pytest.approx(d_near)
    assert far    == pytest.approx(d_far)

def test_decompose_perspective():
    fovy, aspect, near, far = 45.0, 16/9, 0.1, 100.0
    proj = glm.perspective(fovy, aspect, near, far)

    d_fovy, d_aspect, d_near, d_far = decompose_perspective(proj)

    assert fovy   == pytest.approx(d_fovy)
    assert aspect == pytest.approx(d_aspect)
    assert near   == pytest.approx(d_near)
    assert far    == pytest.approx(d_far)

if __name__ == "__main__":
    pytest.main([__file__])