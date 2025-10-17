from typing import Dict
import moderngl
import numpy as np
from typing import Any, Tuple, List
import textwrap


class Command:
	def __init__(self, vert:str, frag:str, uniforms:Dict[str, Any], attributes:Dict[str, np.ndarray|list], count:int):
		super().__init__()
		self.vert = textwrap.dedent(vert)
		self.frag = textwrap.dedent(frag)
		self.uniforms = uniforms
		self.attributes = attributes
		self.count = count

		# GL OBJECTS
		self._attr_buffers: list[Tuple[moderngl.Buffer, str, str]] = []
		self._program:moderngl.Program = None

	def _lazy_setup(self):
		ctx = moderngl.get_context()

		# create program
		self._program = ctx.program(self.vert, self.frag)

		# create attribute buffers
		for name, data in self.attributes.items():
			buffer = ctx.buffer(data.tobytes())
			type_string = f"{data.shape[1]}{data.dtype.char}"
			attr_buffer = (buffer, type_string, name)
			self._attr_buffers.append(attr_buffer)

		# TODO: consider createing VAO here for performance
		# how to cache it, and how to update buffers if needed in __call__ ?
		...

	def __del__(self):
		for buffer, type_string, name in self._attr_buffers:
			buffer.release()

		if program:=self._program:
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

	def __call__(self, *, uniforms:Dict[str, Any]=None, attributes:Dict[str, np.ndarray|list]=None, count:int=None):
		uniforms = uniforms or {}
		if attributes is not None:
			raise NotImplementedError("Updating attributes at call time is not implemented yet.")
		attributes = attributes or {}

		# lazy setup
		if not (self._attr_buffers and self._program):
			self._lazy_setup()

		# validate input parameters
		self.validate_uniforms()

		assert self._program

		# update uniforms
		final_uniforms = {**self.uniforms, **uniforms} # merge initial uniforms with call-time uniforms
		for key, value in final_uniforms.items():
			self._program[key].write(value)

		ctx = moderngl.get_context()

		# reorganize buffers for modenrgl format

		# create vao TODO: consider caching VAO for performance
		vao = ctx.vertex_array(
			self._program,
			self._attr_buffers,
			mode=moderngl.TRIANGLES
		)
		vao.render()
