from typing import Tuple
import glm

Vec3 = glm.vec3 | Tuple[float, float, float]

class Camera:
	def __init__(self) -> None:
		# The transformation matrix, combining position, rotation, and scale
		self.transform = glm.mat4(1.0)  # Identity matrix as the initial transform

		# Perspective projection matrix
		fov = 45.0  # Field of view in degrees
		aspect_ratio = 1.0  # Aspect ratio (width / height)
		near_plane = 0.1  # Near clipping plane
		far_plane = 1000.0  # Far clipping plane
		self.projection = glm.perspective(glm.radians(fov), aspect_ratio, near_plane, far_plane)

	def setAspectRatio(self, aspect:float):
		fov = 45.0  # Field of view in degrees
		near_plane = 0.1  # Near clipping plane
		far_plane = 1000.0  # Far clipping plane
		self.projection = glm.perspective(glm.radians(fov), aspect, near_plane, far_plane)

	def setFOV(self, fov_degrees:float):
		"""
		Sets the field of view in degrees and updates the projection matrix.
		"""
		self.fov = fov_degrees
		aspect_ratio = 1.0  # Will be overridden by setAspectRatio if needed
		near_plane = 0.1
		far_plane = 1000.0
		self.projection = glm.perspective(glm.radians(fov_degrees), aspect_ratio, near_plane, far_plane)

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

	def dolly(self, delta:float):
		pos = self.getPosition()
		front_axis = glm.vec3(self.transform[2][0], self.transform[2][1], self.transform[2][2])
		pos+=front_axis*delta
		self.setPosition(pos)