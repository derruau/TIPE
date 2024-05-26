#version 460 core

const ivec3 offsets3D[27] = ivec3[27](
    ivec3(-1, -1, -1),
	ivec3(-1, -1, 0),
	ivec3(-1, -1, 1),
	ivec3(-1, 0, -1),
	ivec3(-1, 0, 0),
	ivec3(-1, 0, 1),
	ivec3(-1, 1, -1),
	ivec3(-1, 1, 0),
	ivec3(-1, 1, 1),
	ivec3(0, -1, -1),
	ivec3(0, -1, 0),
	ivec3(0, -1, 1),
	ivec3(0, 0, -1),
	ivec3(0, 0, 0),
	ivec3(0, 0, 1),
	ivec3(0, 1, -1),
	ivec3(0, 1, 0),
	ivec3(0, 1, 1),
	ivec3(1, -1, -1),
	ivec3(1, -1, 0),
	ivec3(1, -1, 1),
	ivec3(1, 0, -1),
	ivec3(1, 0, 0),
	ivec3(1, 0, 1),
	ivec3(1, 1, -1),
	ivec3(1, 1, 0),
	ivec3(1, 1, 1)
);

// Les 3 constantes sont des nombres premiers pris au hasard pour la fonction de hachage.
const int hashK1 = 15823;
const int hashK2 = 9737333;
const int hashK3 = 440817757;

layout(binding=1, std430) buffer positionsBuffer {vec3 positions[]; };
layout(binding=2, std430) buffer predictedPositionsBuffer { vec3 predictedPositions[]; };
layout(binding=3, std430) buffer velocitiesBuffer { vec3 velocities[]; };
layout(binding=4, std430) buffer densitiesBuffer { float densities[]; };
layout(binding=5, std430) buffer spatialIndicesBuffer { uvec3 spatialIndices[]; };
layout(binding=6, std430) buffer spatialOffsetsBuffer { int spatialOffsets[]; };

layout(location = 4) uniform int readBuffer = 0; 
layout(location = 5) uniform vec3 sim_corner_1 = vec3(0, 1, 0);
layout(location = 6) uniform vec3 sim_corner_2 = vec3(0, 0, 0);

uniform float delta = 0.0;
uniform bool disable_simulation = true;
uniform int numParticles;
uniform float smoothingRadius;
uniform float targetDensity;
uniform float pressureCst;
uniform float gravity;

// ===================================
// Fonctions en rapport avec la grille
// ===================================

ivec3 GetCell3D(vec3 position, float radius) {
    return ivec3(position.x / radius, position.y / radius, position.z / radius);
};

int HashCell3D(ivec3 cell) {
    return cell.x * hashK1 + cell.y * hashK2 + cell.z * hashK3;
};

int KeyFromHash(int hash, int tableSize) {
    return hash % tableSize;
};

void UpdateSpatialHash(int id) {
	if (id >= numParticles) return;

	// Réinitialisation des offsets
	spatialOffsets[id] = numParticles;
	// Update index buffer
	int index = id;
	ivec3 cell = GetCell3D(predictedPositions[index], smoothingRadius);
	int hash = HashCell3D(cell);
	int key = KeyFromHash(hash, numParticles);
	spatialIndices[id] = uvec3(index, hash, key);
};

// ====================================================
// Fonctions pour le calcul du mouvement des particules
// ====================================================

void resolveCollisions(int index) {
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

float pressureFromDensity(int index) {
    return (densities[index] - targetDensity) * pressureCst;
};


void calculateGravity(int index) {
    if (index >= numParticles) return;

    //Force de gravité
    velocities[index] += vec3(0, gravity, 0) * delta;

    predictedPositions[index] = positions[index] + velocities[index] * delta;
};

void calculateDensities(int id) {
	if (id >= numParticles) return;

	vec3 pos = predictedPositions[id];
	ivec3 originCell = GetCell3D(pos, smoothingRadius);
	float sqrRadius = smoothingRadius * smoothingRadius;
	float density = 0;
	//float nearDensity = 0;

	// Neighbour search
	for (int i = 0; i < 27; i ++)
	{
		int hash = HashCell3D(originCell + offsets3D[i]);
		int key = KeyFromHash(hash, numParticles);
		int currIndex = spatialOffsets[key];

		while (currIndex < numParticles)
		{
			uvec3 indexData = spatialIndices[currIndex];
			currIndex ++;
			// Exit if no longer looking at correct bin
			if (indexData[2] != key) break;
			// Skip if hash does not match
			if (indexData[1] != hash) continue;

			uint neighbourIndex = indexData[0];
			vec3 neighbourPos = predictedPositions[neighbourIndex];
			vec3 offsetToNeighbour = neighbourPos - pos;
			float sqrDstToNeighbour = dot(offsetToNeighbour, offsetToNeighbour);

			// Skip if not within radius
			if (sqrDstToNeighbour > sqrRadius) continue;

			// Calculate density and near density
			float dst = sqrt(sqrDstToNeighbour);
			//density += DensityKernel(dst, smoothingRadius); // A implémenter
			//nearDensity += NearDensityKernel(dst, smoothingRadius);
		}
	}
	
	densities[id] = density; //float2(density, nearDensity);
};

void calculatePressureForces(int id) {

};


void calculateViscosities(int id) {

}

void updatePositions(int id) {

}

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;
void main() {
     if (disable_simulation) {
        return;
     };
};
