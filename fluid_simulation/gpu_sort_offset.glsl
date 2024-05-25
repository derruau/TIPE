#version 460 core


layout(binding=5, std430) buffer spatialIndicesBuffer { uvec3 spatialIndices[]; };
layout(binding=6, std430) buffer spatialOffsetsBuffer { int spatialOffsets[]; };

uniform int numEntries;

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;
void main() {
    if (gl_InstanceID >= numEntries) { return; }

	uint i = gl_InstanceID;
	uint null = numEntries;

	uint key = spatialIndices[i].z;
	uint keyPrev = i == 0 ? null : spatialIndices[i - 1].z;

	if (key != keyPrev)
	{
		spatialOffsets[key] = i;
	}
}
