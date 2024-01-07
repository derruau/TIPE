#version 460 core

struct Particle {
    vec3 position;
    vec3 speed;
};

layout(binding = 1, std430) buffer particlebuffer0 {
    Particle particles0[];
};
layout(binding = 2, std430) buffer particlebuffer1 {
    Particle particles1[];
};

layout(location = 4) uniform int readBuffer = 0; 
uniform vec3 sim_corner_1 = vec3(1, 1, 0);
uniform vec3 sim_corner_2 = vec3(0, 0, 0);
uniform float delta = 0.0;

Particle p(int id) {
    if( readBuffer == 0) {
        return particles0[id];
    };
    return particles1[id];
}

void resolveCollisions(inout Particle p) {
    if (p.position.y > 1) {
        p.position = vec3(0, 0, 0);
        p.speed = -1* p.speed;
    };
    // if (p.position[1] > sim_corner_1[1]) {
    //     p.position[1] = sim_corner_1[1];
    //     p.speed[1] = -1* p.speed[1];
    // };
};

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;
void main() {
    int writeBuffer = 1 - readBuffer;
    particles0[gl_WorkGroupID.x].speed = 20 * vec3(0, 1, 0) * delta;
    particles0[gl_WorkGroupID.x].position += particles0[gl_WorkGroupID.x].speed * delta;
    resolveCollisions(particles0[gl_WorkGroupID.x]);
};
