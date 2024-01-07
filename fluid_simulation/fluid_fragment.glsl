#version 460 core

in vec4 aColor;
out vec4 color;

struct Particle {
    vec3 position;
    vec3 speed;
};

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
    /*if (distance(point_pos.xy, gl_FragCoord.xy) > 10) discard;*/
    float b = 0;
    b = particles0[0].position.y /2;
    color = aColor;
    //color = vec4(0.0, 0.0, 1.0, 1.0);
}

