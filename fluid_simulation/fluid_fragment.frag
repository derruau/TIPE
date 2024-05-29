#version 430 core

layout(binding=3, std430) buffer velocitiesBuffer { vec3 velocities[]; };

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

in vec3 fragmentNormal;
in vec3 fragmentPosition;
flat in int instanceID;
out vec4 color;


vec3 lightPosition = vec3(0.0, -10.0, -10.0);
vec3 lightColor = vec3(1.0, 1.0, 1.0);
float lightStrength = 0.5;

void main() {

    vec3 particleColor = vec3(velocities[instanceID][0], 0.0, 0.0);

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

