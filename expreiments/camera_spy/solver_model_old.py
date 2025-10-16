
class DataModel:
    ...


class SolverModel(DataModel):
    def __init__(self, dimensions:Tuple[int,int]):
        self._image_width, self._image_height = dimensions

        self._principal_point_pixel = None
        self._origin_pixel = None
        self._first_vanishing_lines_pixel = None
        self._second_vanishing_lines_pixel = None
        self._focal_length_pixel = None

        self.first_axis = Axis.PositiveZ
        self.second_axis = Axis.PositiveX

        self._scene_scale:float|None = None

    # required user input
    @property
    def dimensions(self)->Tuple[int,int]:
        return self._image_width, self._image_height
    
    @dimensions.setter
    def dimensions(self, value:Tuple[int,int]):
        assert len(value) == 2, "Dimensions must be a tuple of (width, height)"
        assert isinstance(value[0], int) and isinstance(value[1], int), "Width and height must be integers"
        assert value[0] > 0 and value[1] > 0, "Width and height must be positive"
        self._image_width, self._image_height = value

    # user input wih defaults
    @property
    def principal_point_pixel(self)->glm.vec2:
        # depends on: dimensions
        if self._principal_point_pixel:
            return self._principal_point_pixel
        image_width, image_height = self.dimensions
        return glm.vec2(image_width / 2, image_height / 2)
    
    @principal_point_pixel.setter
    def principal_point_pixel(self, value:glm.vec2|None):
        assert value is None or isinstance(value, glm.vec2), "Principal point must be a glm.vec2 or None"
        self._principal_point_pixel = value

    @property
    def origin_pixel(self):
        # depends on: principal_point_pixel
        if self._origin_pixel:
            return self._origin_pixel
        
        return self.principal_point_pixel # default
    
    @origin_pixel.setter
    def origin_pixel(self, value:glm.vec2|None):
        assert value is None or isinstance(value, glm.vec2), "Principal point must be a glm.vec2 or None"
        self._origin_pixel = value

    @property
    def scene_scale(self):
        if self._scene_scale:
            return self._scene_scale
        return 5.0 # default

    @scene_scale.setter
    def scene_scale(self, value:float|None):
        assert value is None or (isinstance(value, (int, float)) and value > 0), "Scene scale must be a positive number or None"
        self._scene_scale = value

    @property
    def first_vanishing_lines_pixel(self):
        # optional user input, drives first_vanishing_point_pixel
        if self._first_vanishing_lines_pixel:
            return self._first_vanishing_lines_pixel
        return []
    
    @first_vanishing_lines_pixel.setter
    def first_vanishing_lines_pixel(self, value:List[Tuple[glm.vec2, glm.vec2]]|None):
        self._first_vanishing_lines_pixel = value

    @property
    def second_vanishing_lines_pixel(self):
        # optional user input, drives second_vanishing_point_pixel
        return self._second_vanishing_lines_pixel
    
    @second_vanishing_lines_pixel.setter
    def second_vanishing_lines_pixel(self, value:List[Tuple[glm.vec2, glm.vec2]]|None):
        self._second_vanishing_lines_pixel = value

    @property
    def first_vanishing_point_pixel(self):
        # depends on: first_vanishing_lines_pixel
        try:
            # compute by default
            return least_squares_intersection_of_lines(self.first_vanishing_lines_pixel)
        except ValueError:
            # fallback to stored value
            return self._first_vanishing_point_pixel

    @first_vanishing_point_pixel.setter
    def first_vanishing_point_pixel(self, value:glm.vec2):
        if self._first_vanishing_lines_pixel:
            # adjust dependent lines
            current_value = self.first_vanishing_point_pixel
            new_vp = value
            self.first_vanishing_lines_pixel = adjust_vanishing_lines(current_value, new_vp, self.first_vanishing_lines_pixel)
        else:
            self._first_vanishing_point_pixel = value

    @property
    def second_vanishing_point_pixel(self):
        # circular dependency second_vanishing_lines_pixel
        return least_squares_intersection_of_lines(self.second_vanishing_lines_pixel)

    @second_vanishing_point_pixel.setter
    def second_vanishing_point_pixel(self, value:glm.vec2):
        # adjust dependent lines
        current_value = self.second_vanishing_point_pixel
        new_vp = value
        self.second_vanishing_lines_pixel = adjust_vanishing_lines(current_value, new_vp, self.second_vanishing_lines_pixel)

    @property
    def focal_length_pixel(self):
        # depends on: vp1, vp2, principal_point_pixel
        pp = self.principal_point_pixel
        vp1 = self.first_vanishing_point_pixel
        vp2 = self.second_vanishing_point_pixel
        
        # Add validation
        if not all([pp, vp1, vp2]):
            return self._image_height / 2.0  # default
            
        try:
            return compute_focal_length_from_vanishing_points(vp1, vp2, pp)
        except ValueError:
            return self._image_height / 2.0  # fallback to default

    # computed values
    @property
    def orientation(self)->glm.mat3:
        # depends on vp1, vp2, focal_length_pixel
        assert isinstance(self.first_vanishing_point_pixel, glm.vec2), f"First vanishing point must be computed before orientation, {self.first_vanishing_point_pixel}"
        assert isinstance(self.second_vanishing_point_pixel, glm.vec2), f"Second vanishing point must be computed before orientation, {self.second_vanishing_point_pixel}"
        assert isinstance(self.focal_length_pixel, float), f"Focal length must be computed before orientation, {self.focal_length_pixel}"
        assert isinstance(self.principal_point_pixel, glm.vec2), f"Principal point must be computed before orientation, {self.principal_point_pixel}"
        forward = glm.normalize(glm.vec3(self.first_vanishing_point_pixel - self.principal_point_pixel, -self.focal_length_pixel))
        right =   glm.normalize(glm.vec3(self.second_vanishing_point_pixel- self.principal_point_pixel, -self.focal_length_pixel))
        up = glm.cross(forward, right)

        view_orientation_matrix = glm.mat3(forward, right, up)

        glm.determinant(view_orientation_matrix)
        if 1-math.fabs(glm.determinant(view_orientation_matrix)) > 1e-5:
            raise Exception(f'Invalid vanishing point configuration. Rotation determinant {glm.determinant(view_orientation_matrix)}')

        # apply axis assignment
        axis_assignment_matrix:glm.mat3 = create_axis_assignment_matrix(self.first_axis, self.second_axis)            
        view_orientation_matrix:glm.mat3 = view_orientation_matrix * glm.inverse(axis_assignment_matrix)

        return view_orientation_matrix

    @property
    def position(self):
        # depends on: orientation, fov, origin_pixel, scene_scale
        image_width, image_height = self.dimensions
        
        fovy = math.atan(image_height / 2 / self.focal_length_pixel) * 2
        near = 0.1
        far = 100
        projection_matrix = glm.perspective(
            fovy, # fovy in radians
            image_width/image_height, # aspect 
            near,
            far
        )
        assert isinstance(self.orientation, glm.mat3), f"Orientation must be computed before position, {self.orientation}"
        assert isinstance(self.origin_pixel, glm.vec2), f"Origin pixel must be computed before position, {self.origin_pixel}"
        view_transform = glm.mat4(self.orientation)
        view_transform[3][3] = 1.0
        origin_3D = glm.unProject(
            glm.vec3(
                self.origin_pixel.x, 
                self.origin_pixel.y, 
                _world_depth_to_ndc_z(self.scene_scale, near, far)
            ),
            view_transform, 
            projection_matrix, 
            glm.vec4(0,0,image_width,image_height)
        )

        return -origin_3D

    def camera(self)->'Camera':
        # depends on: orientation, position, fov
        from pylive.render_engine.camera import Camera
        camera = Camera()
        fovy = math.atan(self._image_height / 2 / self.focal_length_pixel) * 2
        camera.setFoVY(math.degrees(fovy))

        view_translate_transform = glm.translate(glm.mat4(1.0), self.position)
        view_rotation_transform = glm.mat4(self.orientation)
        view_rotation_transform[3][3] = 1.0
        view_transform= view_rotation_transform * view_translate_transform
        camera.transform = glm.inverse(view_transform)
        return camera