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
layout(location = 5) uniform vec3 sim_corner_1 = vec3(0, 1, 0);
layout(location = 6) uniform vec3 sim_corner_2 = vec3(0, 0, 0);
uniform float delta = 0.0;
uniform bool disable_simulation = true;  

// Pour sélectionner une particule dans le code utiliser cette fonction plutôt que particles0[id] où particles1[id]
Particle p(int id) {
    if( readBuffer == 0) {
        return particles0[id];
    };
    return particles1[id];
}

void update(inout Particle p) {
    vec3 center = (sim_corner_1 + sim_corner_2) * 0.5;
    vec3 size = vec3(abs(sim_corner_2.x - sim_corner_1.x),abs(sim_corner_2.y - sim_corner_1.y),abs(sim_corner_2.z - sim_corner_1.z));

    if (abs(center.x - p.position.x) > size.x) {
        p.speed.x *= -1;
    };
    if (abs(center.y - p.position.y) > size.y) {
        p.speed.y *= -1;
    };
    if (abs(center.z - p.position.z) > size.z) {
        p.speed.z *= -1;
    }
};

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;
void main() {
    if (!disable_simulation) {
        int writeBuffer = 1 - readBuffer;
        particles0[gl_WorkGroupID.x].speed = clamp(particles0[gl_WorkGroupID.x].speed + 20 * vec3(0, -1, 0) * delta, -20, 20);
        particles0[gl_WorkGroupID.x].position += particles0[gl_WorkGroupID.x].speed * delta;
        update(particles0[gl_WorkGroupID.x]);
    }
};
