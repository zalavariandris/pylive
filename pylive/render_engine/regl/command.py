from typing import Dict
import moderngl
import numpy as np


class Command:
	def __init__(self, vert:str, frag:str, uniforms:Dict, attributes:Dict, count:int):
		super().__init__()
		self.vert = vert
		self.frag = frag
		self.uniforms = uniforms
		self.attributes = attributes
		self.count = count

		# GL OBJECTS
		self.vao = None
		self.buffers = []
		self.program:moderngl.Program = None

	def _lazy_setup(self):
		ctx = moderngl.get_context()

		self.program = ctx.program(self.vert, self.frag)


		self.buffers = [
			(
				ctx.buffer(buffer.tobytes()), 
				f"{buffer.shape[1]}{buffer.dtype.char}", 
				name
			)
			for name, buffer in self.attributes.items()
		]

	def __del__(self):
		for buffer, type_string, name in self.buffers:
			buffer.release()
		if vao:=self.vao:
			vao.release()
		if program:=self.program:
			program.release()

	def validate_uniforms(self):
		for uniform in self.uniforms.values():
			... #TODO: Validate uniform values. allow tuples, numpy arrays and glm values.

	def validate_attributes(self):
		if not all(isinstance(buffer, np.ndarray) or isinstance(buffer, list) for buffer in self.attributes.values()):
			raise ValueError(f"All buffer must be np.ndarray or a List, got:{self.attributes.values()}")

		if not all(len(buffer.shape) == 2 for buffer in self.attributes.values()):
			# see  opengl docs: https://registry.khronos.org/OpenGL-Refpages/gl4/html/glVertexAttribPointer.xhtml
			# size must be aither 1,2,3 or 4
			raise ValueError(f"The buffers must be 2 dimensional.") #TODO: accep 1 or a flat array for 1 dimensional data.

		if not all(buffer.shape[1] in {1,2,3,4} for buffer in self.attributes.values()):
			# see  opengl docs: https://registry.khronos.org/OpenGL-Refpages/gl4/html/glVertexAttribPointer.xhtml
			# size must be aither 1,2,3 or 4
			raise ValueError(f"The number of components per generic vertex attribute. Must be 1, 2, 3, or 4.")

		supported_datatypes = {'f','u'}
		for buffer in self.attributes.values():
			if buffer.dtype.char not in supported_datatypes:
				raise ValueError(f"Datatype '{buffer.dtype}' is not supported.")

	def __call__(self):
		# lazy setup
		if not (self.buffers and self.vao and self.program):
			self._lazy_setup()

		# validate input parameters
		self.validate_uniforms()
		self.validate_attributes()

		assert self.program
		# update uniforms
		for key, value in self.uniforms.items():
			self.program[key].write(value)

		ctx = moderngl.get_context()

		# reorganize buffers for modenrgl format

		# create vao
		vao = ctx.vertex_array(
			self.program,
			self.buffers,
			mode=moderngl.TRIANGLES
		)
		vao.render()
