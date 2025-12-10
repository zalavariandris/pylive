import pytest
import glm
import numpy as np

from pylive.perspy.core import solver_functional as solver

############################
# test main solve function #
############################

def test_solve_with_one_vp():
    results = solver.solve(
        mode = solver.SolverMode.OneVP,
        viewport = solver.Rect(0,0, 1280,720),

        first_vanishing_lines=[
            (glm.vec2(50,260), glm.vec2(850,500)),
            (glm.vec2(740,30), glm.vec2(1050,400)),
        ],
        second_vanishing_lines=[
            (glm.vec2(100,650), glm.vec2(1180,650))
        ],
        third_vanishing_lines=[],

        f=720,
        P=glm.vec2(640,360),
        O=glm.vec2(640,200),

        reference_axis=solver.ReferenceAxis.X_Axis,
        reference_distance_segment=(0,100),
        reference_world_size=1.0,

        first_axis = solver.Axis.NegativeX,
        second_axis = solver.Axis.PositiveY,
    )

    assert 'view' in results, "View matrix missing in results"
    assert 'projection' in results, "Projection matrix missing in results"

    view = results['view']
    projection = results['projection']

    view_expected = glm.mat4(
        -0.610905, -0.263127,  0.746699, 0,
        -0.791416,   0.22838, -0.567012, 0,
        -0.021335,  -0.93734, -0.347761, 0,
        1.0776e-07,   -1.0285,  -4.62827, 1
    )
    assert np.allclose(np.array(view), np.array(view_expected)),\
        f"View matrix does not match expected."\
        f"\nGot:\n{view}\nExpected:\n{view_expected}"
    
    
    projection_expected = glm.mat4(
        1.125, 0,       0,  0,
            0, 2,       0,  0,
            0, 0,  -1.002, -1,
            0, 0, -0.2002,  0
    )
    assert np.allclose(np.array(projection), np.array(projection_expected)),\
        f"Projection matrix does not match expected."\
        f"\nGot:\n{projection}\nExpected:\n{projection_expected}"
    
def test_solve_with_two_vp():
    results = solver.solve(
        mode = solver.SolverMode.TwoVP,
        viewport = solver.Rect(0,0, 1280,720),

        first_vanishing_lines=[
            (glm.vec2(870,70), glm.vec2(140,460)),
            (glm.vec2(1220,300), glm.vec2(300,550)),
        ],
        second_vanishing_lines=[
            (glm.vec2(400,60), glm.vec2(1210,460)),
            (glm.vec2(140,330), glm.vec2(1060,560))
        ],
        third_vanishing_lines=[],

        f=720,
        P=glm.vec2(640,360),
        O=glm.vec2(640,280),

        reference_axis=solver.ReferenceAxis.X_Axis,
        reference_distance_segment=(0,100),
        reference_world_size=1.0,

        first_axis = solver.Axis.NegativeX,
        second_axis = solver.Axis.PositiveY,
    )

    assert 'view' in results, "View matrix missing in results"
    assert 'projection' in results, "Projection matrix missing in results"

    view = results['view']
    projection = results['projection']

    view_expected = glm.mat4(
            0.686495, -0.252992,  0.681703, 0,
            0.727128,  0.242701, -0.642169, 0,
         -0.00298585,  0.936532,  0.350571, 0,
        -4.63389e-07, -0.547301,  -6.85107, 1
    )
    assert np.allclose(np.array(view), np.array(view_expected)),\
        f"View matrix does not match expected."\
        f"\nGot:\n{view}\nExpected:\n{view_expected}"
    
    projection_expected = glm.mat4(
        1.56474,      0,       0,  0,
              0,2.78176,       0,  0,
              0,      0,  -1.002, -1,
              0,      0, -0.2002,  0,
    )
    assert np.allclose(np.array(projection), np.array(projection_expected)),\
        f"Projection matrix does not match expected."\
        f"\nGot:\n{projection}\nExpected:\n{projection_expected}"
    
def test_solve_with_three_vp():
    """ Test the solver with three vanishing points."""
    results = solver.solve(
        mode = solver.SolverMode.ThreeVP,
        viewport = solver.Rect(0,0, 1757,2040),

        first_vanishing_lines=[
            (glm.vec2(1008, 61), glm.vec2(-38,901)),
            (glm.vec2(1562,1467), glm.vec2(282,1872)),
        ],
        second_vanishing_lines=[
            (glm.vec2(870,829), glm.vec2(1327,1505)),
            (glm.vec2(-49,1045), glm.vec2(986,1849))
        ],
        third_vanishing_lines=[
            (glm.vec2(261,327), glm.vec2(-45,1919)),
            (glm.vec2(1454,601), glm.vec2(1670,1915)),
        ],

        f=720, # unnecessary in 3VP mode
        P=glm.vec2(640,360), # unnecessary in 3VP mode
        O=glm.vec2(873,491),

        reference_axis=solver.ReferenceAxis.X_Axis,
        reference_distance_segment=(0,100),
        reference_world_size=1.0,

        first_axis = solver.Axis.NegativeX,
        second_axis = solver.Axis.PositiveY,
    )

    assert 'view' in results, "View matrix missing in results"
    assert 'projection' in results, "Projection matrix missing in results"

    view = results['view']
    projection = results['projection']

    # print("View Matrix:\n", glm.transpose(view))
    # print("Projection Matrix:\n", glm.transpose(projection))

    expected_view = glm.mat4(
        0.823959, -0.190644,  0.533617, 0,
            0.566121,   0.31764, -0.760666, 0,
            -0.0244815,  0.928849,   0.36965, 0,
            1.23902,   -15.152,  -19.7499, 1
        )
    
    assert np.allclose(np.array(view), np.array(expected_view)),\
        f"View matrix does not match expected."\
        f"\nGot:\n{view}\nExpected:\n{expected_view}"

    expected_projection = glm.mat4(
        2.20622,   0,          0,      0,
        0,         1.90016,    0,      0,
        0.144669, -0.939165,  -1.002, -1,
        0,         0,         -0.2002, 0
    )

    assert np.allclose(np.array(expected_projection), np.array(expected_projection)),\
        f"View matrix does not match expected."\
        f"\nGot:\n{projection}\nExpected:\n{expected_view}"

##########################
# test solver components #
##########################

if __name__ == "__main__":
    pytest.main([
        __file__, 
        # "-v", # verbose
        "-s" # to show print statements
    ])