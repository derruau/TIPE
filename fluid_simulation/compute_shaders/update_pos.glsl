#version 430 core

layout(binding=1, std430) buffer positionsBuffer {vec3 positions[]; };
layout(binding=3, std430) buffer velocitiesBuffer { vec3 velocities[]; };

uniform float delta;
layout (binding = 7, std140) uniform params {
	vec3 sim_corner_1;
	vec3 sim_corner_2;
	int numParticles;
	float particleSize;
	float smoothingRadius;
	float targetDensity;
	float pressureCst;
	float gravity;
    float delta_;
    bool disable_simulation;
};

void resolveCollisions(uint index) {
    vec3 center = (sim_corner_1 + sim_corner_2) * 0.5;
    vec3 size = vec3(abs(sim_corner_2.x - sim_corner_1.x),abs(sim_corner_2.y - sim_corner_1.y),abs(sim_corner_2.z - sim_corner_1.z));

    if (abs(center.x - positions[index].x) > size.x) {
        velocities[index].x *= -1;
    };
    if (abs(center.y - positions[index].y) > size.y) {
        velocities[index].y *= -1;
    };
    if (abs(center.z - positions[index].z) > size.z) {
        velocities[index].z *= -1;
    }
};


void UpdatePositions(uint id)
{
	//if (id >= numParticles) return;

	positions[id] += velocities[id]* delta;
    velocities[0] = 100 *vec3(delta, delta, delta);
	//resolveCollisions(id);
};

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;
void main() {
    positions[gl_WorkGroupID.x] += vec3(0, 1, 0) * delta;
    //UpdatePositions(gl_WorkGroupID.x);
};
