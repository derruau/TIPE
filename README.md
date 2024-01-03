# Simulation de fluide pour TIPE 2023/2024

Développé sous python 3.11.5

## Présentation

On a 2 modes d'input pour la simulation:
1. Mode Déplacement
    - On peut se déplacer dans l'espace en utilisant WASD et la souris mais on ne peut interragir avec le fluide
2. Mode Interaction
    - On peut intéragir avec le domaine de simulation du fluide mais pas se déplacer
    - Plus précisément, on peut changer la box du domaine de simulation, rajouter/enlever des objets dans la simulation, rajouter/enlever des sources de fluide etc...

On peut basculer entre ces 2 modes en appuyant sur la touche 'm'. \
Appuyer sur 'échap' pour mettre en pause la simulation \
Appuyer sur les flèches directionnelles de gauche et droite pour avancer/reculer étape par étape de la simulation \
Note: les étapes de la simulation sont stockées dans un buffer temporaire, on peut revenir max 128 étapes en arrière \

## Le plan pour faire le rendu des particules
1. Créer une bounding box de simulation
2. Les particules sont des points dans un VBO avec une velocitee et une couleur
3. Demerde toi dans le shader

## Docs
On utilise le design pattern 'model view controller'

# TODO
- AJOUTER UN MOYEN DE DEPLACER LA CAMERA DANS LES COORDONNEES ABSOLUES ET NON RELATIVE AU VECTEUR FORWARD!!
- Clean le code
- Rajouter de la documentation
- Compléter le manuel tex
- Rajouter de la lumière? ==> [Eclairage Blinn Phong](https://en.wikipedia.org/wiki/Blinn%E2%80%93Phong_reflection_model)
