#version 430 core

layout(location=0) in vec3 vertexPos;
layout(location=2) in vec3 vertexNormal;


layout (binding = 0, std140) uniform Matrices
{
    mat4 projection;
    mat4 view;
};
layout(binding=1, std430) buffer positionsBuffer {vec3 positions[]; };
layout(binding=3, std430) buffer velocitiesBuffer { vec3 velocities[]; };


layout(location = 4) uniform int readBuffer = 0; 
uniform float particleSize = 1;

out vec2 fragmentTexCoord;
out vec3 fragmentNormal;
out vec3 fragmentPosition;
out int instanceID;


void main() {
    /*Ici, pour chaque position, il faut calculer la matrice de translation en utilisant les coordonnées fournies par le compute shader*/
    float x = positions[gl_InstanceID][0];
    float y = positions[gl_InstanceID][1];
    float z = positions[gl_InstanceID][2];
    
    //Ne pas demander d'explication pour le *2, c'est juste comme ça 
    mat4 model = mat4(
        particleSize*2, 0, 0, 0,
        0, particleSize*2, 0, 0,
        0, 0, particleSize*2, 0,
        x, y, z, 1
    );
    gl_Position = projection * view * model * vec4(vertexPos, 1.0);
    //fragmentNormal = mat3(model) * vertexNormal;
    fragmentNormal = mat3(model) * normalize(vertexPos);
    fragmentPosition = (model * vec4(vertexPos, 1.0)).xyz;
    instanceID = gl_InstanceID;
}
