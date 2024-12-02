from typing import *
import numpy as np
from textwrap import dedent

import glm # or import pyrr !!!! TODO: checkout pyrr
import numpy as np
import trimesh
import moderngl
from pylive.render_engine.camera import Camera

class RenderLayer:
	FLAT_VERTEX_SHADER = dedent('''
		#version 330 core

		uniform mat4 view;
		uniform mat4 projection;


		layout(location = 0) in vec3 position;

		void main() {
			gl_Position = projection * view * vec4(position, 1.0);
		}
	''')

	FLAT_FRAGMENT_SHADER = dedent('''
		#version 330 core

		layout (location = 0) out vec4 out_color;
		uniform vec4 color;
		void main() {
			out_color = color;
		}
	''')

	def setup(self, ctx:moderngl.Context):
		...

	def destroy(self, ctx:moderngl.Context):
		...

	def resize(self, ctx:moderngl.Context, w:int, h:int):
		...

	def render(self, ctx:moderngl.Context):
		...

class BoxLayer(RenderLayer):
	def __init__(self, camera:Camera|None=None) -> None:
		super().__init__()
		self.camera = camera or Camera()
		self.program = None

	@override
	def setup(self, ctx:moderngl.Context):
		# Setup shaders
		self.program = ctx.program(
			vertex_shader=self.FLAT_VERTEX_SHADER,
			fragment_shader=self.FLAT_FRAGMENT_SHADER
		)

		# Trimesh Cube
		box = trimesh.creation.box(extents=(1, 1, 1))

		# to VAO
		vertices = box.vertices.flatten().astype(np.float32)
		indices = box.faces.flatten().astype(np.uint32)
		vbo = ctx.buffer(vertices)
		ibo = ctx.buffer(indices)

		self.vao = ctx.vertex_array(
			self.program,
			[
				(vbo, '3f', 'position'),
			],
			mode=moderngl.TRIANGLES,
			index_buffer=ibo
		)

	def render(self, ctx:moderngl.Context):
		if not self.program:
			self.setup(ctx)
		self.program['view'].write(self.camera.viewMatrix())
		self.program['projection'].write(self.camera.projectionMatrix())
		self.program['color'].write(glm.vec4(0.5, 0.5, 0.5, 1.0))
		
		self.vao.render()


class TriangleLayer(RenderLayer):
	def __init__(self, camera:Camera|None=None) -> None:
		super().__init__()
		self.camera = camera or Camera()
		self.program = None

	@override
	def setup(self, ctx:moderngl.Context):
		self.program = ctx.program(
			vertex_shader=self.FLAT_VERTEX_SHADER,
			fragment_shader=self.FLAT_FRAGMENT_SHADER
		)

		# triangle
		vertices = np.array([
			 0.0, 0.0,  0.4,   # Vertex 1
			-0.4, 0.0, -0.3,   # Vertex 2
			 0.4, 0.0, -0.3    # Vertex 3
		], dtype=np.float32)

		self.vbo = ctx.buffer(vertices.tobytes())

		self.vao = ctx.vertex_array(
			self.program,
			[
				(self.vbo, '3f', 'position'),
			],
			mode=moderngl.TRIANGLES
		)

	@override
	def destroy(self, ctx:moderngl.Context):
		if self.program:
			self.program.release()
		if self.vbo:
			self.vbo.release()
		if self.vao:
			self.vao.release()

	@override
	def render(self, ctx:moderngl.Context):
		if not self.program:
			self.setup(ctx)

		self.program['view'].write(self.camera.viewMatrix())
		self.program['projection'].write(self.camera.projectionMatrix())
		self.program['color'].write(glm.vec4(1.0, 1.0, 0.3, 1.0))
		self.vao.render()


class GridLayer(RenderLayer):
	def __init__(self, camera, color=glm.vec4(0.5, 0.5, 0.5, 1.0)):
		super().__init__()
		self.program = None
		self.vao = None
		self.camera = camera
		self.color = color
		
	def setup(self, ctx):
		self.program = ctx.program(
			vertex_shader=self.FLAT_VERTEX_SHADER,
			fragment_shader=self.FLAT_FRAGMENT_SHADER
		)
		

		vertices = []
		for x in range(0,11,1):
			vertices.append( (x-5, 0, -5) )
			vertices.append( (x-5, 0, +5) )

		for y in range(0,11,1):
			vertices.append( (-5, 0, y-5) )
			vertices.append( (+5, 0, y-5) )

		# faces = np.array(faces)
		grid = trimesh.Trimesh(vertices=vertices)

		# to VAO
		vertices = grid.vertices.flatten().astype(np.float32)
		vbo = ctx.buffer(vertices)

		self.vao = ctx.vertex_array(
			self.program,
			[
				(vbo, '3f', 'position'),
			],
			mode=moderngl.LINES
		)
		
	def render(self, ctx):
		if not self.program or not self.vao:
			self.setup(ctx)
		self.program['view'].write(self.camera.viewMatrix())
		self.program['projection'].write(self.camera.projectionMatrix())
		self.program['color'].write(self.color)
		self.vao.render()


class ArrowLayer(RenderLayer):
	BILLBOARD = dedent('''\
		// Decompose the view matrix to remove its rotational part
		mat4 billboard(mat4 view, vec4 position){
		    // Extract translation and scale (ignore rotation) from the view matrix
		    mat4 billboardMatrix = mat4(1.0); // Identity matrix for billboard effect
		    billboardMatrix[3] = view[3];     // Keep camera's translation
		    
		    // Compute final position in world space
		    return billboardMatrix * vec4(position, 1.0);
		}
	''')
	FLAT_VERTEX_SHADER = dedent('''\
		#version 330 core

		uniform mat4 view;         // View matrix
		uniform mat4 projection;   // Projection matrix
		uniform mat4 model;        // Model matrix

		layout(location = 0) in vec3 position; // Local vertex position (e.g., quad corners)

		// Function to decompose a matrix into position, rotation, and scale
		void decompose(mat4 M, out vec3 position, out mat3 rotation, out vec3 scale) {
		    // Extract translation
		    position = vec3(M[3][0], M[3][1], M[3][2]);

		    // Extract the upper-left 3x3 matrix for rotation and scale
		    mat3 upper3x3 = mat3(M);

		    // Extract scale
		    scale.x = length(upper3x3[0]); // Length of the X-axis
		    scale.y = length(upper3x3[1]); // Length of the Y-axis
		    scale.z = length(upper3x3[2]); // Length of the Z-axis

		    // Normalize the columns of the 3x3 matrix to remove scaling, leaving only rotation
		    rotation = mat3(
		        upper3x3[0] / scale.x,
		        upper3x3[1] / scale.y,
		        upper3x3[2] / scale.z
		    );
		}

		// Function to create a lookAt matrix
		mat4 lookAt(vec3 eye, vec3 center, vec3 up) {
		    vec3 forward = normalize(center - eye);
		    vec3 right = normalize(cross(forward, up));
		    vec3 cameraUp = cross(right, forward);

		    // Create a rotation matrix
		    mat4 rotation = mat4(
		        vec4(right, 0.0),
		        vec4(cameraUp, 0.0),
		        vec4(-forward, 0.0),
		        vec4(0.0, 0.0, 0.0, 1.0)
		    );

		    // Create a translation matrix
		    mat4 translation = mat4(
		        vec4(1.0, 0.0, 0.0, 0.0),
		        vec4(0.0, 1.0, 0.0, 0.0),
		        vec4(0.0, 0.0, 1.0, 0.0),
		        vec4(-eye, 1.0)
		    );

		    // Combine rotation and translation
		    return rotation * translation;
		}

		void main() {
		    // Decompose the inverse of the view matrix to get camera properties
		    vec3 eye;
		    mat3 rotation;
		    vec3 scale;
		    decompose(inverse(view), eye, rotation, scale);

		    // Create a lookAt matrix (view matrix from camera properties)
		    mat4 lookAtMatrix = lookAt(vec3(0.0, 0.0, 0.0), eye, vec3(0.0, 1.0, 0.0));

		    // Apply transformations: projection * view * model
		    gl_Position = projection * view * model * vec4(position, 1.0);
		}
	''')
	def __init__(self, camera, model=glm.mat4(1.0), color=glm.vec4(1.0, 1.0, 1.0, 1.0)):
		super().__init__()
		self.program = None
		self.vao = None
		self.camera = camera
		self.model = model
		self.color = color
		
	def setup(self, ctx):
		self.program = ctx.program(
			vertex_shader=self.FLAT_VERTEX_SHADER,
			fragment_shader=self.FLAT_FRAGMENT_SHADER
		)
		
		vertices = np.array([
		    (0.0, 0.0, 0.0),  # Bottom of the shaft
		    (0.0, 1.0, 0.0),  # Top of the shaft

		    (0.0, 1.0, 0.0),  # Top of the shaft
		    (-0.1, 0.9, 0.0),  # Left of the arrowhead
		    
		    (0.0, 1.0, 0.0),  # Top of the shaft
		    (0.1, 0.9, 0.0)   # Right of the arrowhead
		], dtype=np.float32).flatten()
	

		vbo = ctx.buffer(vertices)

		self.vao = ctx.vertex_array(
			self.program,
			[
				(vbo, '3f', 'position'),
			],
			mode=moderngl.LINES
		)
		
	def render(self, ctx):
		if not self.program or not self.vao:
			self.setup(ctx)
		self.program['view'].write(self.camera.viewMatrix())
		self.program['projection'].write(self.camera.projectionMatrix())
		self.program['model'].write(self.model)
		self.program['color'].write(self.color)
		self.vao.render()


class AxisLayer(RenderLayer):
	def __init__(self, camera:Camera):
		super().__init__()

		self.xarrow = ArrowLayer(camera, 
			model=glm.rotate(90*math.pi/180, glm.vec3(1,0,0)),
			color=glm.vec4(1,0,0,1)
		), # X
		self.yarrow = ArrowLayer(camera,
			color=glm.vec4(0,1,0,1),
			model=glm.mat4(1)
		), # Y

		self.zarrow = ArrowLayer(camera, 
			model=glm.rotate(90*math.pi/180, glm.vec3(0,0,1)),
			color=glm.vec4(0,0,1,1)
		), # Z

		