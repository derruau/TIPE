#version 460 core

uniform vec3 camPos;

in vec3 fragmentNormal;
in vec3 fragmentPosition;
out vec4 color;

struct Particle {
    vec3 position;
    vec3 speed;
};

vec3 lightPosition = vec3(0.0, 10.0, 10.0);
vec3 lightColor = vec3(1.0, 1.0, 1.0);
float lightStrength = 0.5;

layout(binding = 1, std430) readonly buffer particlebuffer0 {
    Particle particles0[];
};
layout(binding = 2, std430) readonly buffer particlebuffer1 {
    Particle particles1[];
};

void main() {
    /*
    Le *3 c'est pour manuellement ajuster la texture sur le cube de base
    Sinon le if c'est pour que la transparence marche
    */
    vec3 particleColor = vec3(1.0, 0.0, 1.0);

    vec3 result = vec3(0);

    vec3 lightDirectionToPixel = lightPosition - fragmentPosition;
    float dst = length(lightDirectionToPixel);
    lightDirectionToPixel = (lightDirectionToPixel);
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

