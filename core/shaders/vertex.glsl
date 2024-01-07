#version 450 core

layout(location=0) in vec3 vertexPos;
layout(location=1) in vec2 VertexTexCoord;

layout (binding = 3, std140) uniform Matrices
{
    mat4 projection;
    mat4 view;
};

//uniform mat4 projection = mat4(1.0);
//uniform mat4 view = mat4(1.0);
uniform mat4 model = mat4(1.0);

out vec2 fragmentTexCoord;

void main() {
    gl_Position = projection * view * model *  vec4(vertexPos, 1.0);
    fragmentTexCoord = VertexTexCoord;
}
