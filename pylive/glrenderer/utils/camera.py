from typing import Tuple
import glm

Vec3 = glm.vec3 | Tuple[float, float, float]

import math
class Camera:
	def __init__(self) -> None:
		# The transformation matrix, combining position, rotation, and scale
		self.transform = glm.mat4(1.0)  # Identity matrix as the initial transform

		# Camera parameters
		self.near_plane = 0.1  # Near clipping plane
		self.far_plane = 1000.0  # Far clipping plane

		# Lens parameters
		self._focal_length = 23.0  # Focal length in mm
		self._sensor_size = (36.0, 24.0)  # Default sensor size in mm (width, height)
		# self._fovy = 45.0  # Field of view in degrees
	
		# Perspective projection matrix
		self._update_projection()

	def __copy__(self):
		new_camera = Camera()
		new_camera.transform = glm.mat4(self.transform)
		new_camera.near_plane = self.near_plane
		new_camera.far_plane = self.far_plane
		new_camera._focal_length = self._focal_length
		new_camera._sensor_size = self._sensor_size
		new_camera.projection = glm.mat4(self.projection)
		return new_camera

	def _update_projection(self):
		"""Updates the projection matrix based on current camera parameters."""
		self.projection = glm.perspective(
			glm.radians(self.fovy), 
			self.aspect_ratio, 
			self.near_plane, 
			self.far_plane
		)

	@property
	def aspect_ratio(self)->float:
		"""Returns the current aspect ratio."""
		return self._sensor_size[0] / self._sensor_size[1]

	def setAspectRatio(self, aspect:float):
		"""Sets the aspect ratio and updates the projection matrix."""
		w, h = self._sensor_size
		self._sensor_size = (aspect * h, h)
		self._update_projection()

	def setSensorSize(self, width:float, height:float):
		"""
		Sets the sensor size (width and height) and updates the aspect ratio and projection matrix.
		"""
		self._aspect_ratio = width / height
		self._update_projection()

	@property
	def fovy(self)->float:
		"""
		Returns the field of view in degrees.
		"""
		w, h = self._sensor_size
		return math.degrees(math.atan(h / 2 / self._focal_length) * 2)

	def setFoVY(self, fovy_degrees:float):
		"""
		Sets the field of view in degrees and updates the projection matrix.
		"""
		w, h = self._sensor_size
		self._focal_length = (h / 2) / math.tan(math.radians(fovy_degrees) / 2)
		self._update_projection()

	def viewMatrix(self):
		"""
		Returns the view matrix by inverting the transform matrix.
		"""
		return glm.inverse(self.transform)

	def projectionMatrix(self):
		"""
		Returns the current projection matrix.
		"""
		return self.projection

	def setPosition(self, position: Vec3):
		"""
		Sets the camera's position by modifying the transform matrix.
		"""
		position = glm.vec3(position)
		self.transform[3] = glm.vec4(position, 1.0)  # Update the translation part
		return self

	def getPosition(self)->glm.vec3:
		"""
		Returns the position of the camera by extracting it from the transform matrix.
		"""
		return glm.vec3(self.transform[3].x, self.transform[3].y, self.transform[3].z)

	def getDistance(self)->float:
		"""
		Returns the distance of the camera from the origin.
		"""
		pos = self.getPosition()
		return glm.length(pos)

	def translate(self, offset: Vec3):
		"""
		Translates the camera by a given offset in world space.
		"""
		offset = glm.vec3(offset)
		translation = glm.translate(glm.mat4(1.0), offset)
		self.transform = translation * self.transform

	def rotate(self, axis: Vec3, angle: float):
		"""
		Rotates the camera around a specified axis by a given angle (in degrees).
		"""
		axis = glm.vec3(axis)
		rotation = glm.rotate(glm.mat4(1.0), glm.radians(angle), axis)
		self.transform = rotation * self.transform

	def lookAt(self, target:glm.vec3, up:Vec3=(0,1,0)):
		up = glm.vec3(up)
		self.transform = glm.inverse(glm.lookAt(self.getPosition(), target, up))
		return self

	def orbit(self, yaw:float, tilt:float, roll:float=0, target=(0,0,0)):
		target = glm.vec3(target)

		def rotate_around_origin(point, origin, axis, angle):
			rotation_matrix = glm.rotate(glm.mat4(1.0), angle, axis)
			vec4 = rotation_matrix * glm.vec4(point - origin, 1.0)
			return vec4.xyz

		Y_Axis = glm.vec3(0.0, 1.0, 0.0)    # Rotate around the z-axis
		right_axis = glm.vec3(self.transform[0][0], self.transform[0][1], self.transform[0][2])

		pos = self.getPosition()
		pos = rotate_around_origin(pos, glm.vec3(0,0,0), Y_Axis, glm.radians(yaw))
		pos = rotate_around_origin(pos, glm.vec3(0,0,0), right_axis, glm.radians(tilt))
		self.setPosition(pos)
		self.lookAt(glm.vec3(0,0,0))

	def dolly(self, delta:float, target=None):
		"""
		Moves the camera forward or backward along its viewing direction.
		Positive delta moves the camera forward, negative delta moves it backward.
		If target is specified, the delta movement is relative to the distance to the target, otherwise it's in world units.
		"""
		pos = self.getPosition()
		front_axis = glm.vec3(self.transform[2][0], self.transform[2][1], self.transform[2][2])
		if target is not None:
			target = glm.vec3(target)
			delta = glm.length(target - pos) * delta
		pos += front_axis * delta
		self.setPosition(pos)