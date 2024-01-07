#version 460 core

struct Particle {
    vec3 position;
    vec3 speed;
};

layout(location=0) in vec3 vertexPos;


layout (binding = 3, std140) uniform Matrices
{
    mat4 projection;
    mat4 view;
};
layout(binding = 1, std430) buffer particlebuffer0 {
    Particle particles0[];
};
layout(binding = 2, std430) buffer particlebuffer1 {
    Particle particles1[];
};
// uniform mat4 projection = mat4(1.0);
//uniform mat4 view = mat4(1.0);
layout(location = 4) uniform int readBuffer = 0; 
uniform float particleSize = 1;

out vec2 fragmentTexCoord;
out vec4 aColor;
Particle p(int id) {
    if( readBuffer == 0) {
        return particles0[id];
    };
    return particles1[id];
}

void main() {
    /*Ici, pour chaque position, il faut calculer la matrice de translation en utilisant les coordonnées fournies par le compute shader*/
    float x = p(gl_InstanceID).position[0];
    float y = p(gl_InstanceID).position[1];
    float z = p(gl_InstanceID).position[2];
    
    mat4 model = mat4(
        particleSize, 0, 0, 0,
        0, particleSize, 0, 0,
        0, 0, particleSize, 0,
        x, y, z, 1
    );
    aColor = vec4(0, 0, particles0[gl_InstanceID].position.y, 1);
    if (particles0[gl_InstanceID].position.y > 1) {
        aColor = vec4(1, 0, 0, 1);
    };
    gl_Position = projection * view * model *  vec4(vertexPos, 1.0);
}
