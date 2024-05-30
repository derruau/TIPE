#version 430 core

layout(binding=1, std430) buffer positionsBuffer {vec3 positions[]; };
layout(binding=2, std430) buffer predictedPositionsBuffer { vec3 predictedPositions[]; };
layout(binding=3, std430) buffer velocitiesBuffer { vec3 velocities[]; };
layout(binding=4, std430) buffer densitiesBuffer { float densities[]; };
layout(binding=5, std430) buffer spatialIndicesBuffer { uvec3 spatialIndices[]; };
layout(binding=6, std430) buffer spatialOffsetsBuffer { int spatialOffsets[]; };

layout(binding=7, std430) buffer paramsBuffer {
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
} params;

uniform vec3 camPos;

const float maxVelocity = 10.0;

in vec3 fragmentNormal;
in vec3 fragmentPosition;
flat in int instanceID;
out vec4 color;


vec3 lightPosition = vec3(0.0, -10.0, -10.0);
vec3 lightColor = vec3(1.0, 1.0, 1.0);
float lightStrength = 0.5;

vec3 velocityToColor(float velocity) {
    if (velocity < maxVelocity/2) {
        float g = 1.0 * velocity / maxVelocity * 2;
        float b = 1.0 - g;
        return vec3(0.0, g, b);
    } else {
        float r = 1.0 * (velocity - maxVelocity/2) / maxVelocity * 2;
        float g = 1.0 - r;
        return vec3(r, g, 0.0);
    }
}

void main() {

    vec3 velocity = velocities[instanceID];
    float speed = sqrt(velocity.x *velocity.x + velocity.y *velocity.y + velocity.z*velocity.z);
    vec3 particleColor = velocityToColor(speed);

    vec3 result = vec3(0);

    vec3 lightDirectionToPixel = lightPosition - fragmentPosition;
    float dst = length(lightDirectionToPixel);
    //lightDirectionToPixel = (lightDirectionToPixel);
    vec3 cameraDirectionToPixel = camPos - fragmentPosition;
    vec3 halfway = normalize(lightDirectionToPixel + cameraDirectionToPixel);

    float lightStrength = pow(max(dot(halfway, fragmentNormal), 0), 2);

    //ambient
    result += 0.2*particleColor;
    //diffuse
    result += lightColor * lightStrength * max(0.0, dot(fragmentNormal, lightDirectionToPixel)) / (dst * dst) * particleColor;
    //specular
    result += lightColor * lightStrength * pow(max(0.0, dot(fragmentNormal, halfway)),4) / (dst * dst);


    color = vec4(result, 1.0);
}

