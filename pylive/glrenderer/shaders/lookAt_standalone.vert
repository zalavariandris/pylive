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
