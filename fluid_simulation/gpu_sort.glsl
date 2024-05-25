#version 460 core

// le veteur est de la forme (indexe d'origine, hash, clé)
layout(binding=5, std430) buffer spatialIndicesBuffer { uvec3 spatialIndices[]; };

uniform int numEntries;
uniform int groupWidth;
uniform int groupHeight;
uniform int stepIndex;

//Implémentation du Bitonic Merge Sort
layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;
void main() {
	uint i = gl_InstanceID;

	uint hIndex = i & (groupWidth - 1);
	uint indexLeft = hIndex + (groupHeight + 1) * (i / groupWidth);
	uint rightStepSize = stepIndex == 0 ? groupHeight - 2 * hIndex : (groupHeight + 1) / 2;
	uint indexRight = indexLeft + rightStepSize;

    // S'arrete si on dépasse le nombre de particules à tier (lorsque le nombre de particules n'est pas une puissance de 2)
	if (indexRight >= numEntries) return;

	uint valueLeft = spatialIndices[indexLeft].z;
	uint valueRight = spatialIndices[indexRight].z;

    // On échange les valeurs si elles sont décroissantes
	if (valueLeft > valueRight)
	{
		uvec3 temp = spatialIndices[indexLeft];
		spatialIndices[indexLeft] = spatialIndices[indexRight];
		spatialIndices[indexRight] = temp;
	}
};
