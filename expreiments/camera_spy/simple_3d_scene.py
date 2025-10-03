class Simple3DScene:
    def __init__(self):
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.zoom = 3.0
        self.auto_rotate = False
        
        # Define a simple cube (8 vertices)
        self.vertices = np.array([
            [-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],  # back face
            [-1, -1,  1], [1, -1,  1], [1, 1,  1], [-1, 1,  1]   # front face
        ], dtype=np.float32)
        
        # Define cube edges (lines connecting vertices)
        self.edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # back face
            (4, 5), (5, 6), (6, 7), (7, 4),  # front face
            (0, 4), (1, 5), (2, 6), (3, 7)   # connecting edges
        ]
        
        # Colors for each vertex
        self.colors = [
            [1.0, 0.0, 0.0],  # red
            [0.0, 1.0, 0.0],  # green
            [0.0, 0.0, 1.0],  # blue
            [1.0, 1.0, 0.0],  # yellow
            [1.0, 0.0, 1.0],  # magenta
            [0.0, 1.0, 1.0],  # cyan
            [1.0, 1.0, 1.0],  # white
            [0.5, 0.5, 0.5]   # gray
        ]
        
    def create_rotation_matrix(self):
        # Rotation around X axis
        cos_x, sin_x = math.cos(self.rotation_x), math.sin(self.rotation_x)
        rot_x = np.array([
            [1, 0, 0],
            [0, cos_x, -sin_x],
            [0, sin_x, cos_x]
        ])
        
        # Rotation around Y axis
        cos_y, sin_y = math.cos(self.rotation_y), math.sin(self.rotation_y)
        rot_y = np.array([
            [cos_y, 0, sin_y],
            [0, 1, 0],
            [-sin_y, 0, cos_y]
        ])
        
        # Combine rotations
        return np.dot(rot_y, rot_x)
        
    def project_point(self, point, width, height):
        # Simple perspective projection
        z = point[2] + self.zoom
        if z <= 0.1:
            z = 0.1
            
        x = (point[0] / z) * 200 + width / 2
        y = (point[1] / z) * 200 + height / 2
        return (x, y)
        
    def render_wireframe(self, width, height):
        # Apply rotation
        rotation_matrix = self.create_rotation_matrix()
        rotated_vertices = np.dot(self.vertices, rotation_matrix.T)
        
        # Project to 2D
        projected = []
        for vertex in rotated_vertices:
            x, y = self.project_point(vertex, width, height)
            projected.append((x, y))
        
        # Get window position for offset
        window_pos = imgui.get_cursor_screen_pos()
        
        # Draw edges
        draw_list = imgui.get_window_draw_list()
        for i, (start_idx, end_idx) in enumerate(self.edges):
            start_pos = projected[start_idx]
            end_pos = projected[end_idx]
            
            # Offset by window position
            start_x = window_pos.x + start_pos[0]
            start_y = window_pos.y + start_pos[1]
            end_x = window_pos.x + end_pos[0]
            end_y = window_pos.y + end_pos[1]
            
            # Color based on edge type
            if i < 4:  # back face
                color = imgui.IM_COL32(255, 0, 0, 255)  # red
            elif i < 8:  # front face
                color = imgui.IM_COL32(0, 255, 0, 255)  # green
            else:  # connecting edges
                color = imgui.IM_COL32(0, 0, 255, 255)  # blue
                
            draw_list.add_line(
                imgui.ImVec2(start_x, start_y),
                imgui.ImVec2(end_x, end_y),
                color,
                2.0
            )
        
        # Draw vertices as circles
        for i, pos in enumerate(projected):
            color_rgb = self.colors[i]
            color = imgui.IM_COL32(
                int(color_rgb[0] * 255),
                int(color_rgb[1] * 255),
                int(color_rgb[2] * 255),
                255
            )
            
            # Offset by window position
            circle_x = window_pos.x + pos[0]
            circle_y = window_pos.y + pos[1]
            
            draw_list.add_circle_filled(
                imgui.ImVec2(circle_x, circle_y),
                4.0,
                color
            )
