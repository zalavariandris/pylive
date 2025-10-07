import numpy as np
import streamlit as st
import plotly.graph_objects as go


# --- Streamlit App with Plotly Dragging ---
st.title("Interactive Camera Calibration (fSpy-style) with Plotly Drag")
st.write("Drag points on the plot to adjust axis lines.")

# Default line sets
def_lines = [
    [((100, 200), (400, 220)), ((120, 300), (420, 320))],
    [((200, 100), (220, 400)), ((300, 120), (320, 420))],
    [((50, 50), (60, 300)), ((80, 60), (100, 310))]
]

principal_point = (500, 500)

# Prepare Plotly Figure
fig = go.Figure()
colors = ['red','green','blue']
axis_lines_dict = {0: [], 1: [], 2: []}

for i, axis_lines in enumerate(def_lines):
    xs, ys = [], []
    for (x1,y1),(x2,y2) in axis_lines:
        xs += [x1, x2, None]
        ys += [y1, y2, None]
        axis_lines_dict[i].append([[x1,y1],[x2,y2]])
    fig.add_trace(go.Scatter(x=xs, y=ys, mode='lines+markers', line=dict(color=colors[i]),
                             marker=dict(size=12), name=f'{colors[i]} axis'))

fig.update_layout(title='Drag Points to Adjust Lines', dragmode='pan')
st.plotly_chart(fig, use_container_width=True)

st.write("### Update Coordinates")
updated_lines = []
for i in range(3):
    st.write(f"{colors[i]} axis")
    axis_pts = []
    for j, line in enumerate(axis_lines_dict[i]):
        p1 = st.number_input(f'{colors[i]} line {j+1} x1', 0, 1000, int(line[0][0]), key=f'{i}_{j}_x1')
        p1y = st.number_input(f'{colors[i]} line {j+1} y1', 0, 1000, int(line[0][1]), key=f'{i}_{j}_y1')
        p2 = st.number_input(f'{colors[i]} line {j+1} x2', 0, 1000, int(line[1][0]), key=f'{i}_{j}_x2')
        p2y = st.number_input(f'{colors[i]} line {j+1} y2', 0, 1000, int(line[1][1]), key=f'{i}_{j}_y2')
        axis_pts.append(((p1,p1y),(p2,p2y)))
    updated_lines.append(axis_pts)

# Run calibration
try:
    calib = calibrate_camera(updated_lines, principal_point)
    st.success(f"Estimated focal length: {calib['focal_length']:.2f}")
    st.write("Rotation matrix:")
    st.write(calib['rotation'])
    st.write("Vanishing points:")
    st.write(calib['vanishing_points'])
except Exception as e:
    st.error(f"Calibration error: {e}")
