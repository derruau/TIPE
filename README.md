# Simulation de fluide pour TIPE 2023/2024

Développé sous python 3.12.3

## Présentation

Ce projet est un [TIPE](https://www.scei-concours.fr/tipe.php) d'informatique développé pour l'année scolaire 2023/2024 dans le cadre du thème *Jeux et Sports*. J'y présente une simulation de fluide en temps réel utilisant la technique dite [d'hydrodynamique des particules lissées](https://fr.wikipedia.org/wiki/Hydrodynamique_des_particules_liss%C3%A9es) (Smoothed Particles Hydrodynamics en anglais). 

En lançant le programme, une fenètre 3D s'ouvrira dans laquelle vous pourrez configurer les paramètres initiaux du fluide puis lancer la simulation et interragir avec le fluide.

## MCOT
### Simulation de fluide en temps réel via l'hydrodynamique des particules lissées.

Il est extrêmement rare de voir une véritable simulation de fluide dans les jeux vidéos.
Usuellement, les développeurs se contentent de modéliser des fluides fixe dans l'environnement.
Mon TIPE vise à mettre en évidence les problèmes qui rendent la mise en place d'une
simulation de fluide en temps réel difficile.

Le lien avec le thème de l'année est les jeux vidéos, et plus particulièrement les mécaniques de
jeu intéressantes qui pourraient découler de l'exploitation d'une simulation de fluide en temps
réel.

### Positionnement thématique (ÉTAPE 1) :
- INFORMATIQUE (Informatique pratique)
- PHYSIQUE (Mécanique)

### Mots-clés (ÉTAPE 1) :
- Hydrodynamique des Particules Lissées -- Smoothed Particle Hydrodynamics

- Equations de Navier-Stokes -- Navier-Stokes Equations

- Parallélisme -- Parallel Computing

- Partitionnement de l'Espace -- Space Partitioning

- Simulation en temps réel -- Realtime simulation

### Bibliographie commentée
La mécanique des fluides [5] est un thème de la physique particulièrement compliqué, dont on a longtemps peiné à modéliser le comportement. Bien que les équations de Navier-Stokes aient formalisé leur comportement, ces équations restent non résolues à ce jour dans le cas général. Il est donc nécessaire, si notre objectif est de faire une simulation de fluide, de faire une approximation des solutions. 

Beaucoup de logiciels de conception assistée par ordinateur utilisent les méthodes du volume de fluide (VOF) où de Boltzmann sur réseau pour modéliser des fluides. Ces méthodes ont pour avantage de pouvoir simuler des systèmes avec plusieurs niveaux de détails. Par exemple il est possible de simuler un grand navire tout simulant les petits tourbillons autour des extrémités des hélices. Ces techniques montrent cependant des signes de faiblesse lorsqu'il s'agit de simuler des systèmes où beaucoup de parties bougent et interagissent avec le fluide. Dans le cas d'un jeu vidéo, les interactions avec le fluide sont bien plus importantes que les petits détails, on peut donc dire que ces méthodes ne sont pas adaptées. 

D'abord introduite par J. J Monaghan et Lucy en 1977 pour étudier des problèmes d'astrophysique, la technique d'hydrodynamique des particules lissées [1] permet de simuler la mécanique de milieux continus. Cette technique modélise le milieu comme un ensemble de points discrets qui interagissent les uns sur les autres selon des règles totalement arbitraires. Elle possède l'avantage d'être parallélisable et simple à calculer ce qui la rends très rapide. Contrairement aux techniques précédemment mentionnés, l'hydrodynamique des particules lissées brille lorsqu'il s'agit d'interagir avec l'environnement, même si celui ci est à géométrie complexe. On sacrifie cependant des détails de simulation mais comme dit précédemment, ce n'est pas très gênant pour nous. La technique est donc pertinente dans le contexte d'un jeu vidéo.

Cette technique est bien plus simple à programmer que les méthodes concurrentes de l'époque ce qui l'a vite rendue très populaire chez les développeurs . En effet, dès 2003 Matthias Müller publie une étude [2]dans laquelle il met en avant la possibilité d'approximer les équations de Navier-Stokes grâce à cette technique. On découvre, dans le cadre de ces équations, plusieurs résultats très attractifs [3], dont notamment:
- Une solution exacte et indépendante du temps de l'équation de continuité.
- Les phénomènes d'advection parfaitement modélisés.
- Une conservation exacte de la masse, la vitesse et l'énergie du fluide.
- Une résolution (en terme de détails) dépendante du nombre de particules et non du volume de
la simulation.

Par la suite, d'autres personnes comme Nuttapong Chentanez [6] vont améliorer l'algorithme et suggérer des optimisations dont la plus importante est sans doute l'introduction du partitionnement de l'espace. En effet, le mouvement de chaque particule dépends du mouvement de tout les autres, donc l'algorithme initial est en complexité quadratique. Cependant, J.J Monaghan a démontré que le mouvement de chaque particule ne dépend presque que de celui de ses voisines. On peut donc, en assignant à des particules des "régions", ne prendre en compte que les particules de la même région pour effectuer les calculs de la simulation.

Ce processus nécessite de trier les particules. On introduit donc l'algorithme de Tri Bitonique [4] qui est un algorithme de tri parallélisable. Il est la pièce centrale derrière le fonctionnement du partitionnement de l'espace. Grâce à cela, l'hydrodynamique des particules lissées devient une technique capable de simuler un fluide à plus de 100 000 particules en temps réel sur une carte graphique moderne (contre seulement environ 1000 en retirant le partitionnement de l'espace).

### Problématique retenue
Dans cette étude, je vais chercher à coder une simulation de fluide en temps réel, en essayant
de trouver un bon compromis entre réalisme de la simulation et rapidité de calcul.

Le but final étant d'arriver à un modèle qui puisse être codé dans un jeu vidéo.

### Objectifs du TIPE du candidat

1. Tout d'abord j'expliquerai les bases de la théorie derrière l'hydrodynamique des particules
lissées.
2. Dans un second temps je parlerai de la manière de traduire les équations de Navier-Stokes
dans le modèle précédemment développé.
3. Ensuite, j'aborderai la manière dont le code fonctionne et les techniques utilisées afin de faire
tourner la simulation assez vite pour être visionnée en temps réel.
4. Finalement, je discuterai des possibles améliorations du modèle ainsi que de ses limites

### Références bibliographiques (ÉTAPE 1)
[1] J.J MONAGHAN : Smoothed Particle Hydrodynamics : [lien](https://www.annualreviews.org/doi/abs/10.1146/annurev.aa.30.090192.002551?)

[2] MATTHIAS MÜLLER, DAVID CHARYPAR ET MARKUS GROSS : Particle-Based Fluid Simulation for Interactive Applications : [lien](https://matthias-research.github.io/pages/publications/sca03.pdf)

[3] PETER J. COSSINS : Smoothed Particle Hydrodynamics : [lien](https://www.researchgate.net/publication/230988821_Smoothed_Particle_Hydrodynamics)

[4] TIM GFRERER : Implementing Bitonic Merge Sort in Vulkan Compute : [lien](https://poniesandlight.co.uk/reflect/bitonic_merge_sort/)

[5] JIMMY ROUSSEL : Cours de physique: Mécanique des fluides : [lien](https://femto-physique.fr/mecanique_des_fluides/pdf/book_mecaflu.pdf)

[6] NUTTAPONG CHENTANEZ : Real-time Simulation of Large Bodies of Water with Small Scale Details : [lien](https://matthias-research.github.io/pages/publications/hfFluid.pdf)

### DOT
[1] : 28 octobre 2023: Début du TIPE

[2] : 8 novembre 2023: Moteur 3D fini

[3] : Vacances de Noël: Recherche sur la méthode SPH

[4] : Janvier 2024: Apprentissage des shaders OpenGL

[5] : 16 mai 2024 à 1er juin 2024: Codage de la simulation

[6] : 1er juin 2024 à 10 juin 2024: Conception de la présentation

## Installation et lancement
### Installation
Pour installer ce projet, suivre les instructions suivantes
1. Télécharger localement une copie du projet 
```bash
git clone https://github.com/XxJean-YvesxX/TIPE
```

2. Se rendre dans le fichier et créer un environnement virtuel python
```bash
cd TIPE && python -m venv venv
```

3. Activer l'environnement virtuel
```bash
# Sous Linux
source ./venv/bin/activate
# Sous windows
.\venv\Scripts\activate
```

4. Installer les dépendences requises
```bash
pip install -r requirements.txt
```

### Lancement

Pour lancer le projet, suivre les instructions suivantes:

1. Activer l'environnement virtuel
```bash
# Sous Linux
source ./venv/bin/activate
# Sous windows
.\venv\Scripts\activate
```


2. Lancer le projet
```bash
python main.py
```

Pour désactiver l'environnement virtuel, taper la commande ``deactivate``. Si vous fermez le terminal, l'environnement virtuel se désactive tout seul.

## Documentation
Pour avoir une idée de la théorie mathématique et physique derrière le TIPE, regarder le fichier ``./docs/OpenGL_3D_Engine_Manual.pdf``

Le moteur de jeu utilise la structure '[model view controller](https://fr.wikipedia.org/wiki/Mod%C3%A8le-vue-contr%C3%B4leur)'. Le but de mon TIPE n'est pas d'expliquer comment fonctionne ce modèle donc je ne détaille pas plus. Si vous souhaitez tout de même comprendre comment le projet est structuré précisément je vous conseille de commencer par lire le manuel et ensuite de vous plonger dans le code. Tout les fichiers de ce projet sont documentés proprement et le code est assez explicite.

 - Le dossier ``./core/`` contient le moteur de jeu de base. Ce n'est pas très intéressant dans le cadre du TIPE pour savoir comment j'ai codé la simulation de fluide.

 - Le dossier ``./fluid_simulation/`` contient tout le code qui fait tourner la simulation de fluide. Il est principalement consitué de *shaders*, les fichiers qui ont une extension en ``.glsl``

 - Le dossier ``./assets/`` contient tout les objets 3D et images qui sont utilisées dans ce projet.

# Bugs connus
1. Changer le nombre de particules dans la simulation avec ImGUI fait souvent bugger le programme, surement car j'ai implémenté l'UI très vite et que je n'ai pas vraiment pris le temps de voir comment ImGUI fonctionne

# TODO
- Intégrer ImGUI et faire un UI sympa
- Clean le code
- Compléter le manuel tex
- Rajouter de la documentation
- Etre plus consistent avec les notations, par exemple, toujours écrire shaders au lieu de shader, etc...
