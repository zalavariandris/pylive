// Decompose the view matrix to remove its rotational part
mat4 billboard(mat4 view, vec4 position){
	// Extract translation and scale (ignore rotation) from the view matrix
	mat4 billboardMatrix = mat4(1.0); // Identity matrix for billboard effect
	billboardMatrix[3] = view[3];     // Keep camera's translation
	
	// Compute final position in world space
	return billboardMatrix * vec4(position, 1.0);
}

#version 330 core

uniform mat4 view;         // View matrix
uniform mat4 projection;   // Projection matrix
uniform mat4 model;		   // Model matrix

layout(location = 0) in vec3 position; // Local vertex position (e.g., quad corners)


void main() {
    // Extract the camera position from the view matrix


    // Transform to clip space
    gl_Position = projection * view * worldPosition;
}