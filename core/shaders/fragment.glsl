#version 450 core

in vec2 fragmentTexCoord;

uniform sampler2D imageTexture;

out vec4 color;

void main() {
    /*
    Le *3 c'est pour manuellement ajuster la texture sur le cube de base
    Sinon le if c'est pour que la transparence marche
    */
    if (texture(imageTexture, fragmentTexCoord * 3).a < 0.1) discard;
    color = texture(imageTexture, fragmentTexCoord * 3);
}

