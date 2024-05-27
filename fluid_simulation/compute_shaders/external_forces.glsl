#version 430 core

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(binding=1, std430) buffer positionsBuffer {vec3 positions[]; };
layout(binding=2, std430) buffer predictedPositionsBuffer { vec3 predictedPositions[]; };
layout(binding=3, std430) buffer velocitiesBuffer { vec3 velocities[]; };


layout (binding = 7, std140) uniform params {
	vec3 sim_corner_1;
	vec3 sim_corner_2;
	int numParticles;
	float particleSize;
	float smoothingRadius;
	float targetDensity;
	float pressureCst;
	float gravity;
    float delta;
    bool disable_simulation;
};


void calculateGravity(uint index) {
    if (index >= numParticles) return;

    //Force de gravité
    velocities[index] += vec3(0, gravity, 0) * delta;

    predictedPositions[index] = positions[index] + velocities[index] * delta;
};

void main() {
    calculateGravity(gl_WorkGroupID.x);
};
