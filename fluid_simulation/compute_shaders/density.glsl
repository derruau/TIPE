#version 430

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

layout(binding=4, std430) buffer densitiesBuffer { float densities[]; };
layout(binding=5, std430) buffer spatialIndicesBuffer { uvec3 spatialIndices[]; };
layout(binding=6, std430) buffer spatialOffsetsBuffer { int spatialOffsets[]; };

uniform bool disable_simulation = true;
uniform int numParticles;
uniform float smoothingRadius;
uniform float targetDensity;
uniform float pressureCst;
uniform float gravity;


ivec3 GetCell3D(vec3 position, float radius) {
    return ivec3(position.x / radius, position.y / radius, position.z / radius);
};

int HashCell3D(ivec3 cell) {
    return cell.x * hashK1 + cell.y * hashK2 + cell.z * hashK3;
};

ivec3 GetCell3D(vec3 position, float radius) {
    return ivec3(position.x / radius, position.y / radius, position.z / radius);
};

// 3d conversion: done
//Integrate[(h-r)^2 r^2 Sin[θ], {r, 0, h}, {θ, 0, π}, {φ, 0, 2*π}]
float SpikyKernelPow2(float dst, float radius)
{
	if (dst < radius)
	{
		float scale = 15 / (2 * PI * pow(radius, 5));
		float v = radius - dst;
		return v * v * scale;
	}
	return 0;
}

float DensityKernel(float dst, float radius) {
    return SpikyKernelPow2(dst, radius);
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
			density += DensityKernel(dst, smoothingRadius); // A implémenter
			//nearDensity += NearDensityKernel(dst, smoothingRadius);
		}
	}
	
	densities[id] = density; //float2(density, nearDensity);
};

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;
void main() {
    calculateDensities(gl_InstanceID);
};
